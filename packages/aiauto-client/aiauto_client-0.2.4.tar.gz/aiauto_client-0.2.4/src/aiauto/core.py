"""Core AIAuto controller and study management classes.

This module contains the main classes for interacting with the AIAuto service:
- AIAutoController: Main controller for workspace and study management
- TrialController: Controller for individual trial management
- StudyWrapper: Wrapper for Optuna study with AIAuto integration
- WaitOption: Enum for optimize() wait behavior
"""

import json
import logging
import os
import tempfile
from enum import Enum
from os import makedirs
from typing import Any, Callable, ClassVar, Dict, List, Optional, Union

import optuna
from optuna_dashboard import save_note
from tenacity import (
    RetryError,
    before_sleep_log,
    retry,
    retry_if_exception,
    retry_if_exception_type,
    stop_after_delay,
    wait_fixed,
)

from .grpc_helper import _parse_grpc_url, _should_retry_rpc_error
from .grpc_storage import PathPrefixGrpcStorageProxy
from .http_client import ConnectRPCClient, ConnectRPCError
from .serializer import build_requirements, object_to_json, serialize
from .util import (
    MAX_DEV_SHM_GI,
    MAX_TMP_CACHE_GI,
    _fetch_available_gpu_models,
    _parse_size_to_gi,
    _validate_study_name,
    _validate_top_n_artifacts,
)

# Configure logger for tenacity retry messages
logger = logging.getLogger(__name__)

# Error code to user hint message mapping
_ERROR_HINTS = {
    "unauthenticated": "Token is expired or invalid. Please reissue your token from the dashboard.",
    "failed_precondition": "Previous workspace is still being deleted. Please try again shortly.",
    "unavailable": "Service is temporarily unavailable. Please try again later.",
}
_DEFAULT_ERROR_HINT = "Server error occurred. Please contact administrator if the problem persists."


class WaitOption(Enum):
    """Options for waiting on optimize() to complete trials."""

    WAIT_NO = "wait_no"
    WAIT_ATLEAST_ONE_TRIAL = "wait_atleast_one"
    WAIT_ALL_TRIALS = "wait_all"


class AIAutoController:
    _instances: ClassVar[Dict[str, "AIAutoController"]] = {}

    def __new__(
        cls,
        token: str,
        storage_size: str = "500Mi",
        artifact_store_size: str = "2Gi",
        shared_cache_dir: str = "/mnt/shared-cache",
        shared_cache_size: str = "500Mi",
    ):
        if token not in cls._instances:
            cls._instances[token] = super().__new__(cls)
        return cls._instances[token]

    def __init__(
        self,
        token: str,
        storage_size: str = "500Mi",
        artifact_store_size: str = "2Gi",
        shared_cache_dir: str = "/mnt/shared-cache",
        shared_cache_size: str = "500Mi",
    ):
        if hasattr(self, "token") and self.token == token:
            return

        self.token = token
        self.client = ConnectRPCClient(token)

        # Validate storage sizes (result unused, validation raises on error)
        _parse_size_to_gi(storage_size, max_gi=10.0)
        _parse_size_to_gi(artifact_store_size, max_gi=100.0)
        _parse_size_to_gi(shared_cache_size, max_gi=MAX_TMP_CACHE_GI)

        # EnsureWorkspace 호출해서 journal_grpc_storage_proxy_host_external 받아와서 storage 초기화
        # Automatically retries for up to 30 seconds if workspace is not ready
        # Only retries on unavailable/failed_precondition errors (CRD not ready)
        @retry(
            stop=stop_after_delay(30),
            wait=wait_fixed(5),
            retry=retry_if_exception(_should_retry_rpc_error),
            before_sleep=before_sleep_log(logger, logging.INFO),
            reraise=True,
        )
        def _ensure_workspace():
            response = self.client.call_rpc(
                "EnsureWorkspace",
                {
                    "storage_size": storage_size,
                    "artifact_store_size": artifact_store_size,
                    "shared_cache_dir": shared_cache_dir,
                    "shared_cache_size": shared_cache_size,
                },
            )

            # 받아온 journal_grpc_storage_proxy_host_external로 storage 초기화
            host_external = response.get("journalGrpcStorageProxyHostExternal", "")
            if not host_external:
                # Server-side validation error, create ConnectRPCError for consistency
                raise ConnectRPCError(
                    "unavailable", "No storage host returned from EnsureWorkspace"
                )

            return response

        try:
            response = _ensure_workspace()

            # Parse gRPC storage URL (supports both path-based and legacy formats)
            host_external = response.get("journalGrpcStorageProxyHostExternal", "")
            host, port, user_id = _parse_grpc_url(host_external)

            # Use PathPrefixGrpcStorageProxy for path-based routing (user_id present)
            # Fall back to standard GrpcStorageProxy for legacy host:port format
            if user_id:
                self.storage = PathPrefixGrpcStorageProxy(host=host, port=port, user_id=user_id)
            else:
                self.storage = optuna.storages.GrpcStorageProxy(host=host, port=int(port))

            # Store the internal host for CRD usage (if needed later)
            self.storage_host_internal = response.get("journalGrpcStorageProxyHostInternal", "")
            self.dashboard_url = response.get("dashboardUrl", "")

        except RetryError as e:
            raise RuntimeError(
                f"OptunaWorkspace creation timed out after 30 seconds.\n"
                f"Please check workspace status in dashboard.\n"
                f"Details: {e.last_attempt.exception()}"
            ) from e
        except ConnectRPCError as e:
            hint = _ERROR_HINTS.get(e.code, _DEFAULT_ERROR_HINT)
            raise RuntimeError(f"Failed to initialize workspace: {e}\n{hint}") from e
        except Exception as e:
            raise RuntimeError(f"Failed to initialize workspace: {e}\n{_DEFAULT_ERROR_HINT}") from e

        # artifact store: lazily resolved at call time based on runtime environment
        self._artifact_store = None
        self.tmp_dir = tempfile.mkdtemp(prefix="ai_auto_tmp_")

    def get_storage(self):
        return self.storage

    def get_artifact_store(
        self,
    ) -> Union[
        optuna.artifacts.FileSystemArtifactStore,
        optuna.artifacts.Boto3ArtifactStore,
        optuna.artifacts.GCSArtifactStore,
    ]:
        # Lazy init: prefer container-mounted PVC at /artifacts (runner env),
        # fallback to local ./artifacts for client/local usage.
        if self._artifact_store is None:
            if os.path.isdir("/artifacts"):
                path = "/artifacts"
            else:
                path = "./artifacts"
                if not os.path.isdir(path):
                    makedirs(path, exist_ok=True)
            self._artifact_store = optuna.artifacts.FileSystemArtifactStore(path)

        return self._artifact_store

    def get_artifact_tmp_dir(self):
        return self.tmp_dir

    def upload_artifact(
        self,
        trial: Union[optuna.trial.Trial, optuna.trial.FrozenTrial],
        file_path: str,
    ) -> str:
        """Upload artifact and set artifact_id on trial.

        Args:
            trial: The trial to associate the artifact with.
            file_path: Path to the file to upload.

        Returns:
            The artifact_id string.
        """
        artifact_id = optuna.artifacts.upload_artifact(
            artifact_store=self.get_artifact_store(),
            storage=self.get_storage(),
            study_or_trial=trial,
            file_path=file_path,
        )
        trial.set_user_attr("artifact_id", artifact_id)
        return artifact_id

    def create_study(
        self,
        study_name: str,
        direction: Optional[str] = "minimize",
        directions: Optional[List[str]] = None,
        sampler: Union[object, dict, None] = None,
        pruner: Union[object, dict, None] = None,
    ) -> "StudyWrapper":
        """Create a new study using the controller's token."""
        # Validate study name follows Kubernetes DNS rules
        _validate_study_name(study_name)

        if not direction and not directions:
            raise ValueError("Either 'direction' or 'directions' must be specified")

        if direction and directions:
            raise ValueError("Cannot specify both 'direction' and 'directions'")

        try:
            # Prepare request data for CreateStudy
            # direction_spec is oneof: only one of direction or directions should be set
            spec = {
                "studyName": study_name,
                "samplerJson": object_to_json(sampler),
                "prunerJson": object_to_json(pruner),
            }

            if direction:
                spec["direction"] = direction
            elif directions:
                # DirectionList wrapper message with "values" field
                spec["directions"] = {"values": directions}

            request_data = {"spec": spec}

            # Call CreateStudy RPC
            response = self.client.call_rpc("CreateStudy", request_data)

            # Return StudyWrapper
            return StudyWrapper(
                study_name=response.get("studyName", study_name),
                storage=self.storage,
                controller=self,
            )

        except Exception as e:
            raise RuntimeError(f"Failed to create study: {e}") from e


class TrialController:
    _instances: ClassVar[Dict[int, "TrialController"]] = {}

    # System-reserved user_attr keys that users must not override
    RESERVED_KEYS = frozenset(
        {
            "pod_name",  # Pod <-> Trial matching
            "trialbatch_name",  # TrialBatch identifier
            "gpu_name",  # Actual allocated GPU model (from nvidia-smi)
            "artifact_id",  # Artifact download link (set by ac.upload_artifact)
            "artifact_removed",  # Artifact deletion flag
        }
    )

    def __new__(cls, trial: Union[optuna.trial.Trial, optuna.trial.FrozenTrial]):
        trial_id = getattr(trial, "_trial_id", id(trial))
        if trial_id not in cls._instances:
            cls._instances[trial_id] = super().__new__(cls)
        return cls._instances[trial_id]

    def __init__(self, trial: Union[optuna.trial.Trial, optuna.trial.FrozenTrial]):
        trial_id = getattr(trial, "_trial_id", id(trial))
        if hasattr(self, "trial") and getattr(self.trial, "_trial_id", id(self.trial)) == trial_id:
            return  # Already initialized

        self.trial = trial
        self.logger = optuna.logging.get_logger("optuna")
        self.logs = []
        self.log_count = 0

    def get_trial(self) -> Union[optuna.trial.Trial, optuna.trial.FrozenTrial]:
        return self.trial

    def set_user_attr(self, key: str, value: Any) -> None:
        if key in self.RESERVED_KEYS:
            raise ValueError(
                f"Cannot set user_attr '{key}': This key is reserved by the system. "
                f"Reserved keys: {', '.join(sorted(self.RESERVED_KEYS))}"
            )
        self.trial.set_user_attr(key, value)

    # python client core, runner, objective 함수 안에서 각각 tc 객체가 다 다름
    # tc.log 는 runner 랑 objective 함수 안에서 만 쓰는게 맞을 듯
    # -> singleton 으로 이건 되는 듯 하다
    # runner 에서도 objective 실행한거 try catch 로 감싸서 에러밖에 안 찍음 (이것만 허용)
    # core lib 에서 나는 에러는 최대한 objective 안 사용자 코드에서 try catch 로 감싸는 걸로
    def log(self, value: str):
        # 로그를 배열에 추가
        self.logs.append(value)
        self.log_count += 1

        # 5개 로그마다 save_note 호출
        if self.log_count % 5 == 0:
            self._save_note()

        # 콘솔에도 출력 (Pod 실행 중 실시간 확인용)
        self.logger.info(f"\ntrial_number: {self.trial.number}, {value}")

    def _save_note(self):
        """optuna_dashboard의 save_note로 로그 저장"""
        try:
            # 각 로그에 인덱스 번호 추가 및 구분선으로 구분
            separator = "\n" + "-" * 10 + "\n"
            formatted_logs = [f"[{i + 1:05d}] {log}" for i, log in enumerate(self.logs)]
            note_content = separator.join(formatted_logs)
            save_note(self.trial, note_content)
        except Exception as e:
            # save_note 실패해도 계속 진행 (fallback: console log)
            self.logger.warning(f"Failed to save note: {e}")

    def flush(self):
        """Trial 종료 시 남은 로그 강제 저장 (조건 3)"""
        if self.logs:
            self._save_note()


class StudyWrapper:
    def __init__(self, study_name: str, storage, controller: AIAutoController):
        self.study_name = study_name
        self._storage = storage
        self._controller = controller
        self._study = None
        self._last_trialbatch_name = None

    def get_study(self) -> optuna.Study:
        if self._study is None:
            # Automatically retries for up to 30 seconds if study gRPC storage is not ready
            # Retries on all exceptions since optuna.create_study raises various gRPC errors
            @retry(
                stop=stop_after_delay(30),
                wait=wait_fixed(5),
                before_sleep=before_sleep_log(logger, logging.INFO),
                reraise=True,
            )
            def _create_study():
                return optuna.create_study(
                    study_name=self.study_name,
                    storage=self._storage,
                    load_if_exists=True,
                )

            try:
                self._study = _create_study()

                # Wrap the original ask() method to add trialbatch_name
                original_ask = self._study.ask

                def wrapped_ask(fixed_distributions=None):
                    logger.warning("WARNING: ask/tell trial runs locally (not in Kubernetes)")
                    logger.warning("    - No Pod created")
                    logger.warning("    - Not counted in TrialBatch statistics")
                    logger.warning("    - Visible in Optuna Dashboard with 'ask_tell_local' tag")

                    trial = original_ask(fixed_distributions=fixed_distributions)

                    try:
                        trial.set_user_attr("trialbatch_name", "ask_tell_local")
                    except Exception as e:
                        logger.warning(f"Failed to set trialbatch_name: {e}")

                    return trial

                self._study.ask = wrapped_ask

            except RetryError as e:
                raise RuntimeError(
                    f"Study gRPC storage not ready after 30 seconds.\n"
                    f"Study runner pod may not be running. "
                    f"Please check study status in dashboard.\n"
                    f"Details: {e.last_attempt.exception()}"
                ) from e
            except Exception as e:
                dashboard_msg = ""
                if self._controller.dashboard_url:
                    dashboard_msg = f" from the web dashboard at {self._controller.dashboard_url}"
                raise RuntimeError(
                    "Failed to get study. If this persists, please delete and reissue your token"
                    f"{dashboard_msg}"
                ) from e
        return self._study

    def optimize(  # noqa: C901, PLR0912, PLR0915
        self,
        objective: Callable,
        n_trials: int = 10,
        parallelism: int = 2,
        requirements_file: Optional[str] = None,
        requirements_list: Optional[List[str]] = None,
        resources_requests: Optional[Dict[str, str]] = None,
        resources_limits: Optional[Dict[str, str]] = None,
        runtime_image: Optional[str] = None,
        use_gpu: bool = False,
        gpu_model: Optional[Union[str, Dict[str, int]]] = None,
        wait_option: WaitOption = WaitOption.WAIT_ATLEAST_ONE_TRIAL,
        wait_timeout: int = 600,
        dev_shm_size: str = "500Mi",  # /dev/shm size (use_gpu=True only), max 4Gi
        tmp_cache_dir: str = "/mnt/tmp-cache",  # Mount path for tmp-cache emptyDir
        use_tmp_cache_mem: bool = False,  # Use tmpfs (Memory medium) for tmp-cache
        tmp_cache_size: str = "500Mi",  # Size limit for tmp-cache, max 4Gi
        top_n_artifacts: int = 5,  # Number of top artifacts to keep (default: 5, min: 1)
        # Image pull credentials (mutually exclusive: registry method XOR generic method)
        image_pull_registry: Optional[str] = None,  # Registry URL (e.g., "registry.gitlab.com")
        image_pull_username: Optional[str] = None,  # Registry username
        image_pull_password: Optional[str] = None,  # Registry password/token
        image_pull_docker_config_json: Optional[Dict[str, Any]] = None,  # dockerconfigjson format
    ) -> str:
        # Validate emptyDir size parameters
        gpu_model_map = {}
        if gpu_model is not None:
            if isinstance(gpu_model, str):
                gpu_model_map = {gpu_model: n_trials}
            elif isinstance(gpu_model, dict):
                gpu_model_map = gpu_model
            else:
                raise ValueError(f"gpu_model must be str or dict, got {type(gpu_model).__name__}")

            # Fetch available GPU models dynamically from Frontend API
            # Validation is mandatory to ensure GPU flavors exist in cluster
            valid_models = _fetch_available_gpu_models(
                self._controller.client.base_url, self._controller.token
            )

            if not valid_models:
                raise ValueError(
                    "No GPU models available in cluster. "
                    "Please ensure Kueue ResourceFlavors are configured."
                )

            invalid_keys = set(gpu_model_map.keys()) - valid_models
            if invalid_keys:
                raise ValueError(
                    f"Invalid GPU model(s): {invalid_keys}. "
                    f"Available models: {sorted(valid_models)}"
                )

            if not all(v > 0 for v in gpu_model_map.values()):
                raise ValueError(
                    f"All GPU model trial counts must be positive. Got: {gpu_model_map}"
                )

            total_allocated = sum(gpu_model_map.values())
            if total_allocated > n_trials:
                raise ValueError(
                    f"Total GPU model allocations ({total_allocated}) "
                    f"exceeds n_trials ({n_trials}). "
                    f"GPU model allocation: {gpu_model_map}"
                )

        # CPU 사용 시 dev_shm_size 지정 오류
        if not use_gpu and dev_shm_size != "500Mi":
            raise ValueError(
                "dev_shm_size parameter can only be used with GPU (use_gpu=True). "
                "dev_shm_size is automatically applied when GPU is enabled."
            )

        # dev_shm_size max 4Gi 초과 체크
        if dev_shm_size:
            try:
                dev_shm_gi = _parse_size_to_gi(dev_shm_size)
                if dev_shm_gi > MAX_DEV_SHM_GI:
                    raise ValueError(
                        f"dev_shm_size={dev_shm_size} exceeds max size of {MAX_DEV_SHM_GI}Gi. "
                        f"Specified size: {dev_shm_gi:.2f}Gi"
                    )
            except ValueError as e:
                if "Invalid size format" in str(e) or "Unsupported size unit" in str(e):
                    raise ValueError(f"dev_shm_size: {e}") from e
                raise

        # tmp_cache_size max 4Gi 초과 체크
        if tmp_cache_size:
            try:
                tmp_cache_gi = _parse_size_to_gi(tmp_cache_size)
                if tmp_cache_gi > MAX_TMP_CACHE_GI:
                    raise ValueError(
                        f"tmp_cache_size={tmp_cache_size} exceeds max "
                        f"size of {MAX_TMP_CACHE_GI}Gi. "
                        f"Specified size: {tmp_cache_gi:.2f}Gi"
                    )
            except ValueError as e:
                if "Invalid size format" in str(e) or "Unsupported size unit" in str(e):
                    raise ValueError(f"tmp_cache_size: {e}") from e
                raise

        # top_n_artifacts 최소값 검증
        _validate_top_n_artifacts(top_n_artifacts)

        # Image pull credentials validation (mutually exclusive)
        registry_method = any([image_pull_registry, image_pull_username, image_pull_password])
        generic_method = image_pull_docker_config_json is not None
        if registry_method and generic_method:
            raise ValueError(
                "Cannot use both registry method (image_pull_registry/username/password) "
                "and generic method (image_pull_docker_config_json). Choose one."
            )
        # Registry method requires all 3 fields
        if registry_method and not all(
            [image_pull_registry, image_pull_username, image_pull_password]
        ):
            raise ValueError(
                "Registry method requires all 3 fields: "
                "image_pull_registry, image_pull_username, image_pull_password"
            )

        # 리소스 기본값 설정
        if resources_requests is None:
            if use_gpu:
                resources_requests = {"cpu": "2", "memory": "4Gi"}
            else:
                resources_requests = {"cpu": "1", "memory": "1Gi"}

        if resources_limits is None:
            resources_limits = {}  # 빈 dict로 전달, operator가 requests 기반으로 처리

        if runtime_image is None or runtime_image == "":
            if use_gpu:
                runtime_image = "pytorch/pytorch:2.1.0-cuda12.1-cudnn8-runtime"
            else:
                runtime_image = "ghcr.io/astral-sh/uv:python3.8-bookworm-slim"

        # Convert to kebab-case for gRPC
        gpu_model_grpc = (
            {k.replace("_", "-"): v for k, v in gpu_model_map.items()} if gpu_model_map else {}
        )

        try:
            request_data = {
                "objective": {
                    "sourceCode": serialize(objective),
                    "requirementsTxt": build_requirements(requirements_file, requirements_list),
                    "objectiveName": objective.__name__,  # 함수명 추출하여 전달
                },
                "batch": {
                    "studyName": self.study_name,
                    "nTrials": n_trials,
                    "parallelism": parallelism,
                    "runtimeImage": runtime_image or "",
                    "resourcesRequests": resources_requests or {},
                    "resourcesLimits": resources_limits or {},
                    "useGpu": use_gpu,
                    "gpuModel": gpu_model_grpc,
                    "devShmSize": dev_shm_size or "",
                    "tmpCacheDir": tmp_cache_dir or "",
                    "useTmpCacheMem": use_tmp_cache_mem,
                    "tmpCacheSize": tmp_cache_size or "",
                    "topNArtifacts": top_n_artifacts,
                },
            }

            # Add image pull credentials to batch (oneof field)
            if registry_method:
                request_data["batch"]["imagePullRegistry"] = {
                    "registry": image_pull_registry,
                    "username": image_pull_username,
                    "password": image_pull_password,
                }
            elif generic_method:
                # Convert dict to JSON string for protobuf string field
                request_data["batch"]["imagePullDockerConfigJson"] = json.dumps(
                    image_pull_docker_config_json
                )

            response = self._controller.client.call_rpc("Optimize", request_data)
            trialbatch_name = response.get("trialbatchName", "")
            self._last_trialbatch_name = trialbatch_name

            # Wait for trials based on wait_option
            if wait_option != WaitOption.WAIT_NO:
                self._wait_for_trialbatch(trialbatch_name, n_trials, wait_option, wait_timeout)

            return trialbatch_name

        except Exception as e:
            raise RuntimeError(f"Failed to start optimization: {e}") from e

    def _wait_for_trialbatch(
        self, trialbatch_name: str, n_trials: int, wait_option: WaitOption, timeout: int
    ) -> None:
        """Internal method to wait for TrialBatch trials to complete."""

        @retry(
            stop=stop_after_delay(timeout),
            wait=wait_fixed(5),
            before_sleep=before_sleep_log(logger, logging.INFO),
            reraise=True,
            retry=retry_if_exception_type(RuntimeError),  # ValueError (Failed phase) skips retry
        )
        def _poll():
            status = self.get_status(trialbatch_name=trialbatch_name)
            trialbatches = status.get("trialbatches", {})

            if trialbatch_name not in trialbatches:
                raise RuntimeError(f"TrialBatch {trialbatch_name} not found")

            tb_status = trialbatches[trialbatch_name]

            # Check for Failed phase - immediate failure without retry
            phase = tb_status.get("phase", "")
            if phase == "Failed":
                raise ValueError(
                    f"TrialBatch {trialbatch_name} failed. "
                    "Check logs: pip or uv may not be installed in the custom image."
                )

            completed = tb_status.get("count_completed", 0)

            if wait_option == WaitOption.WAIT_ALL_TRIALS:
                if completed >= n_trials:
                    logger.info(f"All {n_trials} trials completed")
                    return
                raise RuntimeError(f"Waiting for all trials: {completed}/{n_trials} completed")
            elif wait_option == WaitOption.WAIT_ATLEAST_ONE_TRIAL:
                if completed >= 1:
                    logger.info(f"At least one trial completed: {completed}/{n_trials}")
                    return
                raise RuntimeError(
                    f"Waiting for at least one trial: {completed}/{n_trials} completed"
                )

        try:
            _poll()
        except RetryError as e:
            raise RuntimeError(
                f"Timeout after {timeout} seconds waiting for trials to complete. "
                f"Check status in dashboard or use get_status() to see current progress."
            ) from e

    def get_status(
        self, trialbatch_name: Optional[str] = None, include_trials: bool = False
    ) -> dict:
        """
        Get status of the study or a specific TrialBatch.

        Args:
            trialbatch_name: Optional TrialBatch name to filter
            include_trials: Include completed_trials details (default: False)

        Returns:
            dict with trialbatches map structure
        """
        try:
            request_data = {"studyName": self.study_name, "includeTrials": include_trials}
            if trialbatch_name:
                request_data["trialbatchName"] = trialbatch_name

            response = self._controller.client.call_rpc("GetStatus", request_data)

            # Convert trialbatches from camelCase to snake_case
            trialbatches_raw = response.get("trialbatches", {})
            trialbatches_converted = {}

            for tb_name, tb_status in trialbatches_raw.items():
                converted = {
                    "trialbatch_name": tb_status.get("trialbatchName", ""),
                    "phase": tb_status.get("phase", ""),
                    "message": tb_status.get("message", ""),
                    "count_active": tb_status.get("countActive", 0),
                    "count_succeeded": tb_status.get("countSucceeded", 0),
                    "count_pruned": tb_status.get("countPruned", 0),
                    "count_failed": tb_status.get("countFailed", 0),
                    "count_total": tb_status.get("countTotal", 0),
                    "count_completed": tb_status.get("countCompleted", 0),
                }

                if "completedTrials" in tb_status:
                    converted["completed_trials"] = tb_status["completedTrials"]

                trialbatches_converted[tb_name] = converted

            return {
                "study_name": response.get("studyName", ""),
                "trialbatches": trialbatches_converted,
                "dashboard_url": response.get("dashboardUrl", ""),
                "updated_at": response.get("updatedAt", ""),
            }

        except Exception as e:
            raise RuntimeError(f"Failed to get status: {e}") from e

    def is_trial_finished(
        self, trial_identifier: Union[int, str], trialbatch_name: Optional[str] = None
    ) -> bool:
        """
        Check if a specific trial has finished.

        Args:
            trial_identifier: Either trial number (int) or pod name (str)
            trialbatch_name: TrialBatch name to check. Required when using trial number.
                           If None, uses the most recent TrialBatch from optimize().

        Returns:
            True if the trial has finished, False otherwise
        """
        # Use provided trialbatch_name or fall back to most recent
        tb_name = trialbatch_name or self._last_trialbatch_name

        # Trial number requires a valid trialbatch_name (provided or _last_trialbatch_name)
        if isinstance(trial_identifier, int) and tb_name is None:
            raise ValueError(
                "trialbatch_name is required when using trial number. "
                "Trial numbers are unique only within a TrialBatch. "
                "Call optimize() first to set _last_trialbatch_name, "
                "or provide trialbatch_name explicitly. "
                "Example: is_trial_finished(5, trialbatch_name='tb-abc123')"
            )

        if tb_name is None:
            logger.warning(
                "No TrialBatch tracked. Call optimize() first or specify trialbatch_name."
            )
            return False

        try:
            status = self.get_status(trialbatch_name=tb_name, include_trials=True)
            trialbatches = status.get("trialbatches", {})

            if tb_name not in trialbatches:
                return False

            tb_status = trialbatches[tb_name]
            completed_trials = tb_status.get("completed_trials", {})

            if isinstance(trial_identifier, int):
                # Search by trial number
                for trial_info in completed_trials.values():
                    if trial_info.get("trialNumber") == trial_identifier:
                        return True
                return False
            else:
                # Search by pod name (trial_identifier is the key)
                return trial_identifier in completed_trials

        except Exception as e:
            logger.error(f"Failed to check trial status: {e}")
            return False

    def wait(
        self,
        trial_identifier: Union[int, str],
        trialbatch_name: Optional[str] = None,
        timeout: int = 600,
    ) -> bool:
        """
        Wait for a specific trial to finish.

        Args:
            trial_identifier: Either trial number (int) or pod name (str)
            trialbatch_name: TrialBatch name to check. Required when using trial number.
                           If None, uses the most recent TrialBatch from optimize().
            timeout: Maximum wait time in seconds (default: 600)

        Returns:
            True if trial finished within timeout, False if timeout occurred
        """
        # Use provided trialbatch_name or fall back to most recent
        tb_name = trialbatch_name or self._last_trialbatch_name

        # Trial number requires a valid trialbatch_name (provided or _last_trialbatch_name)
        if isinstance(trial_identifier, int) and tb_name is None:
            raise ValueError(
                "trialbatch_name is required when using trial number. "
                "Trial numbers are unique only within a TrialBatch. "
                "Call optimize() first to set _last_trialbatch_name, "
                "or provide trialbatch_name explicitly. "
                "Example: wait(5, trialbatch_name='tb-abc123')"
            )

        if tb_name is None:
            raise RuntimeError(
                "No TrialBatch tracked. Call optimize() first or specify trialbatch_name."
            )

        @retry(
            stop=stop_after_delay(timeout),
            wait=wait_fixed(5),
            before_sleep=before_sleep_log(logger, logging.INFO),
            reraise=True,
        )
        def _poll():
            if self.is_trial_finished(trial_identifier, trialbatch_name=tb_name):
                logger.info(f"Trial {trial_identifier} in TrialBatch {tb_name} finished")
                return
            raise RuntimeError(
                f"Waiting for trial {trial_identifier} in TrialBatch {tb_name} to finish"
            )

        try:
            _poll()
            return True
        except RetryError:
            logger.warning(
                f"Timeout after {timeout}s waiting for trial {trial_identifier} "
                f"in TrialBatch {tb_name}"
            )
            return False

    def __repr__(self) -> str:
        return f"StudyWrapper(study_name='{self.study_name}', storage={self._storage})"
