"""General utility functions for AIAuto client.

This module contains validation and parsing utilities used internally by core.py.
"""

import re
from typing import Optional, Set

import requests

# Kubernetes resource naming constraints
MAX_K8S_NAME_LENGTH = 63

# Storage size limits (in Gi)
MAX_DEV_SHM_GI = 4.0
MAX_TMP_CACHE_GI = 4.0


def _validate_study_name(name: str) -> None:
    """Validate study name follows Kubernetes DNS-1123 subdomain rules.

    Rules:
    - Must contain only lowercase letters, numbers, and hyphens (-)
    - Must start and end with a letter or number
    - Maximum 63 characters

    Args:
        name: The study name to validate

    Raises:
        ValueError: If study name is invalid
    """
    if not name:
        raise ValueError("Study name cannot be empty")

    if len(name) > MAX_K8S_NAME_LENGTH:
        raise ValueError(
            f"Study name too long ({len(name)} characters). "
            f"Maximum 63 characters allowed for Kubernetes resource names."
        )

    # Kubernetes DNS-1123 subdomain: lowercase alphanumeric and hyphen only
    # Must start and end with alphanumeric
    if not re.match(r"^[a-z0-9]([-a-z0-9]*[a-z0-9])?$", name):
        raise ValueError(
            f"Invalid study name '{name}'. "
            f"Study name must contain only lowercase letters, numbers, and hyphens (-). "
            f"Must start and end with a letter or number."
        )


def _parse_size_to_gi(size_str: str, max_gi: Optional[float] = None) -> float:
    """Parse Kubernetes size string to Gi value.

    Args:
        size_str: Size string in Kubernetes format (e.g., "500Mi", "4Gi")
        max_gi: Maximum allowed size in Gi (optional)

    Returns:
        Size in Gi (float)

    Raises:
        ValueError: If size format is invalid or exceeds maximum

    Examples:
        "500Mi" -> 0.48828125
        "1Gi" -> 1.0
        "4Gi" -> 4.0
    """
    if not size_str:
        return 0.0

    match = re.match(r"^(\d+(?:\.\d+)?)(Mi|Gi)$", size_str)
    if not match:
        raise ValueError(
            f"Invalid size format: {size_str}. "
            "Only binary units (Mi, Gi) are allowed. Use formats like '500Mi', '4Gi'"
        )

    value, unit = match.groups()
    value = float(value)

    gi = 0.0
    if unit == "Mi":
        gi = value / 1024  # Mi to Gi
    elif unit == "Gi":
        gi = value
    else:
        raise ValueError(f"Unsupported size unit: {unit}")

    if max_gi is not None and gi > max_gi:
        raise ValueError(f"Size {size_str} exceeds maximum allowed size of {max_gi}Gi")

    return gi


def _validate_top_n_artifacts(value: int, min_value: int = 1) -> None:
    """Validate top_n_artifacts parameter.

    Args:
        value: The top_n_artifacts value to validate
        min_value: Minimum allowed value (default: 1)

    Raises:
        ValueError: If value is less than min_value
    """
    if value < min_value:
        raise ValueError(f"top_n_artifacts must be at least {min_value}, got {value}")


def _fetch_available_gpu_models(base_url: str, token: str) -> Set[str]:
    """Fetch available GPU model names from the Frontend API.

    Args:
        base_url: Base URL of the Frontend service
        token: Authentication token

    Returns:
        Set of available GPU model names (converted to Python naming with underscores)

    Raises:
        ValueError: If API call fails or service is unavailable
    """
    try:
        url = f"{base_url}/api/gpu-flavors"
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()

        # API returns list of GpuFlavorInfo: [{name: "gpu-3090", nodeLabels: {...}}, ...]
        gpu_flavors = response.json()
        # Extract flavor names and convert Kubernetes naming (gpu-3090) to Python naming (gpu_3090)
        return {f["name"].replace("-", "_") for f in gpu_flavors}
    except Exception as e:
        raise ValueError(
            f"Failed to fetch available GPU models from API. "
            f"Please ensure the Frontend service is running and accessible at {base_url}. "
            f"Error: {e}"
        ) from e
