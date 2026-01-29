"""Version checking utility for MCA SDK.

This module checks if the running SDK version is outdated and logs warnings.
"""

import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger("mca_sdk.version_check")


def check_version(current_version: str, timeout: float = 2.0) -> Optional[dict]:
    """Check if current SDK version is outdated.

    Fetches the latest version from PyPI and compares with current version.
    Logs a warning if the version is >30 days old.

    Args:
        current_version: Current SDK version string (e.g., "1.0.0")
        timeout: Timeout for PyPI API request in seconds

    Returns:
        Dictionary with version info or None if check failed:
        {
            "latest_version": "1.0.1",
            "current_version": "1.0.0",
            "is_outdated": True,
            "age_days": 45
        }
    """
    try:
        import requests
    except ImportError:
        logger.debug("requests library not available, skipping version check")
        return None

    try:
        response = requests.get("https://pypi.org/pypi/mca-sdk/json", timeout=timeout)

        if response.status_code == 200:
            data = response.json()
            latest_version = data["info"]["version"]

            # Get release date for latest version
            releases = data.get("releases", {}).get(latest_version, [])
            if not releases:
                logger.debug("No release information available for latest version")
                return None

            # Get upload time from first release artifact
            upload_time_str = releases[0].get("upload_time")
            if not upload_time_str:
                logger.debug("No upload time available for latest version")
                return None

            # Parse release date (ISO format: "2026-01-15T10:30:00")
            release_dt = datetime.fromisoformat(upload_time_str.replace("Z", "+00:00"))
            age_days = (datetime.now(release_dt.tzinfo) - release_dt).days

            is_outdated = current_version != latest_version and age_days > 30

            # Log warning if outdated
            if is_outdated:
                logger.warning(
                    f"MCA SDK version {current_version} is outdated. "
                    f"Latest version is {latest_version} (released {age_days} days ago). "
                    f"Run: pip install --upgrade mca-sdk"
                )

            return {
                "latest_version": latest_version,
                "current_version": current_version,
                "is_outdated": is_outdated,
                "age_days": age_days,
            }

        else:
            logger.debug(f"PyPI API returned status {response.status_code}")
            return None

    except requests.exceptions.Timeout:
        logger.debug("Version check timed out (network unavailable)")
        return None
    except requests.exceptions.RequestException as e:
        logger.debug(f"Version check skipped (network error): {e}")
        return None
    except Exception as e:
        logger.debug(f"Version check failed (unexpected error): {e}")
        return None
