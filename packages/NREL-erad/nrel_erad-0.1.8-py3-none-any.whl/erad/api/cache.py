"""Cache management for distribution and hazard models."""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict

from loguru import logger
from gdm.distribution import DistributionSystem

from .models import DistributionModelInfo, HazardModelInfo


# ========== Distribution Model Cache ==========


def get_cache_directory() -> Path:
    """Get the standard cache directory for ERAD models."""
    # Use platform-specific cache directory
    if os.name == "nt":  # Windows
        cache_base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    else:  # Unix-like (Linux, macOS)
        cache_base = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))

    cache_dir = cache_base / "erad" / "distribution_models"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def get_metadata_file() -> Path:
    """Get the metadata file path."""
    return get_cache_directory() / "models_metadata.json"


def load_metadata() -> Dict[str, DistributionModelInfo]:
    """Load model metadata from cache directory."""
    metadata_file = get_metadata_file()
    if metadata_file.exists():
        try:
            with open(metadata_file, "r") as f:
                data = json.load(f)
                return {name: DistributionModelInfo(**info) for name, info in data.items()}
        except Exception as e:
            logger.warning(f"Failed to load metadata: {e}")
            return {}
    return {}


def save_metadata(models: Dict[str, DistributionModelInfo]):
    """Save model metadata to cache directory."""
    metadata_file = get_metadata_file()
    try:
        data = {
            name: {
                "name": info.name,
                "description": info.description,
                "created_at": info.created_at.isoformat(),
                "file_path": info.file_path,
            }
            for name, info in models.items()
        }
        with open(metadata_file, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save metadata: {e}")


def scan_cache_directory() -> Dict[str, DistributionModelInfo]:
    """Scan cache directory for model files and update metadata."""
    cache_dir = get_cache_directory()
    models = {}

    # Get all JSON files in cache directory
    for file_path in cache_dir.glob("*.json"):
        if file_path.name == "models_metadata.json":
            logger.info("Skipping metadata file")
            continue

        try:
            # Extract model name from filename (remove timestamp suffix)
            filename = file_path.stem
            # Try to parse as name_timestamp format
            parts = filename.rsplit("_", 1)
            if len(parts) == 2 and parts[1].replace(".", "").isdigit():
                model_name = parts[0]
            else:
                model_name = filename

            # Get file stats
            stats = file_path.stat()
            created_at = datetime.fromtimestamp(stats.st_ctime)

            # Validate the file contains valid DistributionSystem data
            with open(file_path, "r") as f:
                data = json.load(f)
                _ = DistributionSystem(**data)  # Validate

            models[model_name] = DistributionModelInfo(
                name=model_name,
                description=f"Loaded from {file_path.name}",
                created_at=created_at,
                file_path=str(file_path),
            )
        except Exception as e:
            logger.warning(f"Skipping invalid model file {file_path}: {e}")
            continue

    return models


def refresh_models_from_cache(uploaded_models: Dict[str, DistributionModelInfo]):
    """Refresh in-memory models from cache directory."""
    # Load metadata
    metadata = load_metadata()
    # Scan directory for files
    scanned = scan_cache_directory()
    # Merge: prefer metadata but add new scanned files
    for name, info in scanned.items():
        if name not in metadata:
            metadata[name] = info
    # Verify all metadata files still exist
    valid_models = {name: info for name, info in metadata.items() if Path(info.file_path).exists()}
    uploaded_models.update(valid_models)
    save_metadata(uploaded_models)
    logger.info(f"Loaded {len(uploaded_models)} models from cache")


# ========== Hazard Model Cache ==========


def get_hazard_cache_directory() -> Path:
    """Get the standard cache directory for ERAD hazard models."""
    if os.name == "nt":  # Windows
        cache_base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    else:  # Unix-like (Linux, macOS)
        cache_base = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))

    cache_dir = cache_base / "erad" / "hazard_models"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def get_hazard_metadata_file() -> Path:
    """Get the hazard metadata file path."""
    return get_hazard_cache_directory() / "hazard_metadata.json"


def load_hazard_metadata() -> Dict[str, HazardModelInfo]:
    """Load hazard model metadata from cache directory."""
    metadata_file = get_hazard_metadata_file()
    if metadata_file.exists():
        try:
            with open(metadata_file, "r") as f:
                data = json.load(f)
                return {name: HazardModelInfo(**info) for name, info in data.items()}
        except Exception as e:
            logger.warning(f"Failed to load hazard metadata: {e}")
            return {}
    return {}


def save_hazard_metadata(models: Dict[str, HazardModelInfo]):
    """Save hazard model metadata to cache directory."""
    metadata_file = get_hazard_metadata_file()
    try:
        data = {
            name: {
                "name": info.name,
                "description": info.description,
                "created_at": info.created_at.isoformat(),
                "file_path": info.file_path,
            }
            for name, info in models.items()
        }
        with open(metadata_file, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save hazard metadata: {e}")


def refresh_hazard_models_from_cache(uploaded_hazard_models: Dict[str, HazardModelInfo]):
    """Refresh in-memory hazard models from cache directory."""
    metadata = load_hazard_metadata()
    # Verify all metadata files still exist
    valid_models = {name: info for name, info in metadata.items() if Path(info.file_path).exists()}
    uploaded_hazard_models.update(valid_models)
    save_hazard_metadata(uploaded_hazard_models)
    logger.info(f"Loaded {len(uploaded_hazard_models)} hazard models from cache")
