"""Helper functions for the ERAD REST API."""

import json
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import HTTPException, UploadFile, status
from loguru import logger
from gdm.distribution import DistributionSystem

from erad.systems.hazard_system import HazardSystem
from .models import HazardModelData, DistributionModelInfo


def _load_distribution_system(
    uploaded_models: Dict[str, DistributionModelInfo],
    system_name: Optional[str] = None,
) -> DistributionSystem:
    """Load a distribution system from name or data."""
    if system_name:
        if system_name not in uploaded_models:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Distribution system '{system_name}' not found",
            )
        file_path = uploaded_models[system_name].file_path
        return DistributionSystem.from_json(file_path)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either system_name or system_data must be provided",
        )


def _create_hazard_system(hazard_models: List[HazardModelData]) -> HazardSystem:
    """Create a hazard system from hazard model data."""
    hazard_system = HazardSystem()

    for model_data in hazard_models:
        # Import the appropriate hazard type dynamically
        from erad.models.hazard import (
            EarthQuakeModel,
            FloodModel,
            FloodModelArea,
            WindModel,
            FireModel,
            FireModelArea,
        )

        hazard_type_mapping = {
            "earthquake": EarthQuakeModel,
            "flood": FloodModel,
            "flood_area": FloodModelArea,
            "wind": WindModel,
            "fire": FireModel,
            "fire_area": FireModelArea,
        }

        hazard_class = hazard_type_mapping.get(model_data.hazard_type.lower())
        if not hazard_class:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown hazard type: {model_data.hazard_type}",
            )

        hazard_model = hazard_class(
            name=model_data.name, timestamp=model_data.timestamp, **model_data.model_data
        )
        hazard_system.add_component(hazard_model)

    return hazard_system


async def _handle_zip_upload(  # noqa: C901
    file: UploadFile,
    name: str,
    models_dir: Path,
    timestamp: float,
    validate_distribution: bool = True,
) -> tuple[Path, Optional[Path]]:
    """
    Handle ZIP file upload.

    Expected ZIP structure:
    - A JSON file (e.g., model.json or p1rhs7_1247.json)
    - An optional time series folder (e.g., model_time_series/ or p1rhs7_1247_time_series/)

    Args:
        validate_distribution: If True, validates JSON as DistributionSystem (default).
                              Set to False for hazard models.

    Returns:
        tuple: (json_file_path, time_series_folder_path or None)
    """
    content = await file.read()

    # Create temporary directory for extraction
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        zip_path = temp_path / "uploaded.zip"

        # Write zip file
        with open(zip_path, "wb") as f:
            f.write(content)

        # Validate and extract ZIP
        try:
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                # Check for malicious paths (zip slip vulnerability)
                for member in zip_ref.namelist():
                    member_path = Path(member)
                    if member_path.is_absolute() or ".." in member_path.parts:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Invalid path in ZIP file: {member}",
                        )

                zip_ref.extractall(temp_path / "extracted")
        except zipfile.BadZipFile:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or corrupted ZIP file"
            )

        extract_dir = temp_path / "extracted"

        # Find JSON file(s) in the extracted content
        # Handle case where files might be in a subdirectory
        json_files = list(extract_dir.rglob("*.json"))

        if not json_files:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ZIP file must contain at least one JSON file",
            )

        # Use the first JSON file found (or filter to find the main one)
        # Prefer JSON files at the root level
        root_json_files = [
            f
            for f in json_files
            if f.parent == extract_dir
            or (f.parent.parent == extract_dir and not f.parent.name.endswith("_time_series"))
        ]

        if root_json_files:
            json_file = root_json_files[0]
        else:
            json_file = json_files[0]

        # Read and validate JSON
        try:
            with open(json_file, "r") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid JSON format in {json_file.name}: {str(e)}",
            )

        # Validate that data can create a DistributionSystem (only for distribution models)
        if validate_distribution:
            try:
                _ = DistributionSystem(**data)
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid distribution system data: {str(e)}",
                )

        # Determine base name from JSON file
        json_base_name = json_file.stem  # e.g., "p1rhs7_1247"

        # Look for corresponding time series folder
        time_series_folder_name = f"{json_base_name}_time_series"
        time_series_folders = list(extract_dir.rglob(time_series_folder_name))

        # Also check for folder in same directory as JSON
        if not time_series_folders:
            potential_ts_folder = json_file.parent / time_series_folder_name
            if potential_ts_folder.exists() and potential_ts_folder.is_dir():
                time_series_folders = [potential_ts_folder]

        # Save JSON file to cache - retain original filename
        dest_json_path = models_dir / json_file.name
        with open(dest_json_path, "w") as f:
            json.dump(data, f, indent=2)

        # Copy time series folder if it exists - retain original folder name
        dest_time_series_path = None
        if time_series_folders:
            time_series_folder = time_series_folders[0]
            dest_time_series_path = models_dir / time_series_folder.name

            # Remove existing folder if it exists
            if dest_time_series_path.exists():
                shutil.rmtree(dest_time_series_path)

            shutil.copytree(time_series_folder, dest_time_series_path)

            # Count files in time series folder
            ts_files = list(dest_time_series_path.rglob("*"))
            ts_file_count = len([f for f in ts_files if f.is_file()])
            logger.info(f"Copied {ts_file_count} time series files to {dest_time_series_path}")

        return dest_json_path, dest_time_series_path
