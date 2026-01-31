"""Hazard model endpoints for the ERAD REST API."""

import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, status
from loguru import logger

from .models import HazardModelInfo
from .cache import (
    get_hazard_cache_directory,
    save_hazard_metadata,
    refresh_hazard_models_from_cache,
)
from .helpers import _handle_zip_upload

from erad.systems import HazardSystem

router = APIRouter(prefix="/hazard-models", tags=["hazard-models"])


# In-memory storage - will be initialized from main.py
uploaded_hazard_models: Dict[str, HazardModelInfo] = {}


@router.post("", status_code=status.HTTP_201_CREATED)
async def upload_hazard_model(
    file: UploadFile = File(..., description="ZIP file containing hazard model data"),
    name: str = Form(..., description="Unique name for the hazard model"),
    description: Optional[str] = Form(None, description="Optional description"),
):
    """
    Upload a hazard model as a ZIP file.

    Supported format:
    - ZIP file: A ZIP archive containing:
       - A JSON file (e.g., `hazard_model.json`)
       - An optional time series folder (e.g., `hazard_model_time_series/`) with data files

    Supported hazard types: earthquake, flood, flood_area, wind, fire, fire_area.
    """
    try:
        # Validate hazard type

        # Check if name already exists
        if name in uploaded_hazard_models:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Hazard model '{name}' already exists",
            )

        # Validate file type
        content_type = file.content_type
        filename = file.filename or ""
        is_zip = content_type in [
            "application/zip",
            "application/x-zip-compressed",
        ] or filename.lower().endswith(".zip")

        if not is_zip:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Only ZIP files are allowed"
            )

        # Use hazard cache directory
        models_dir = get_hazard_cache_directory()
        timestamp = datetime.now().timestamp()

        # Handle ZIP file upload (don't validate as DistributionSystem)
        file_path, time_series_path = await _handle_zip_upload(
            file, name, models_dir, timestamp, validate_distribution=False
        )

        # Store metadata
        uploaded_hazard_models[name] = HazardModelInfo(
            name=name, description=description, created_at=datetime.now(), file_path=str(file_path)
        )

        # Persist metadata
        save_hazard_metadata(uploaded_hazard_models)

        logger.info(f"Uploaded hazard model '{name}' to cache: {file_path}")

        response = {
            "status": "success",
            "message": f"Hazard model '{name}' uploaded successfully",
            "name": name,
            "file_path": str(file_path),
        }

        if time_series_path:
            response["time_series_path"] = str(time_series_path)

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Hazard model upload failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Upload failed: {str(e)}"
        )


@router.get("", response_model=List[HazardModelInfo])
async def list_hazard_models(refresh: bool = False):
    """
    List all uploaded hazard models.

    Args:
        refresh: If True, refresh the list from cache directory
    """
    try:
        if refresh:
            refresh_hazard_models_from_cache(uploaded_hazard_models)

        models = list(uploaded_hazard_models.values())
        return models

    except Exception as e:
        logger.error(f"Failed to list hazard models: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list hazard models: {str(e)}",
        )


@router.get("/{model_name}")
async def get_hazard_model(model_name: str):
    """Get a specific hazard model by name."""
    try:
        if model_name not in uploaded_hazard_models:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Hazard model '{model_name}' not found",
            )

        model_info = uploaded_hazard_models[model_name]

        # Read file content
        hazard_system = HazardSystem.from_json(model_info.file_path)

        return {
            "name": model_name,
            "description": model_info.description,
            "created_at": model_info.created_at,
            "number_of_components": len(list(hazard_system.iter_all_components())),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve hazard model: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve hazard model: {str(e)}",
        )


@router.delete("/{model_name}")
async def delete_hazard_model(model_name: str):
    """Delete a hazard model by name."""
    try:
        if model_name not in uploaded_hazard_models:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Hazard model '{model_name}' not found",
            )

        model_info = uploaded_hazard_models[model_name]
        json_path = Path(model_info.file_path)

        # Derive time series folder path from JSON path
        # e.g., "hazard_model.json" -> "hazard_model_time_series"
        time_series_path = json_path.parent / f"{json_path.stem}_time_series"

        # Remove JSON file
        if json_path.exists():
            json_path.unlink()
            logger.info(f"Deleted hazard model file: {json_path}")

        # Remove time series folder if it exists
        if time_series_path.exists() and time_series_path.is_dir():
            shutil.rmtree(time_series_path)
            logger.info(f"Deleted time series folder: {time_series_path}")

        # Remove from memory
        del uploaded_hazard_models[model_name]

        # Update metadata
        save_hazard_metadata(uploaded_hazard_models)

        logger.info(f"Deleted hazard model '{model_name}'")

        return {
            "status": "success",
            "message": f"Hazard model '{model_name}' deleted successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete hazard model: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete hazard model: {str(e)}",
        )
