"""Distribution model endpoints for the ERAD REST API."""

import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, status
from loguru import logger
from gdm.distribution import DistributionSystem

from .models import DistributionModelInfo
from .cache import get_cache_directory, save_metadata, refresh_models_from_cache
from .helpers import _handle_zip_upload


router = APIRouter(prefix="/distribution-models", tags=["distribution-models"])


# In-memory storage - will be initialized from main.py
uploaded_models: Dict[str, DistributionModelInfo] = {}


@router.post("", status_code=status.HTTP_201_CREATED)
async def upload_distribution_model(
    file: UploadFile = File(..., description="ZIP file containing distribution system data"),
    name: str = Form(..., description="Unique name for the distribution system"),
    description: Optional[str] = Form(None, description="Optional description"),
):
    """
    Upload a distribution system model as a ZIP file.

    Supported format:
    - ZIP file: A ZIP archive containing:
       - A JSON file (e.g., `model.json`)
       - An optional time series folder (e.g., `model_time_series/`) with data files

    The uploaded model will be stored and can be referenced by name in simulations.
    """
    try:
        # Check if name already exists
        if name in uploaded_models:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Distribution system '{name}' already exists",
            )

        # Get file content type and filename
        content_type = file.content_type
        filename = file.filename or ""

        # Determine file type
        is_zip = content_type in [
            "application/zip",
            "application/x-zip-compressed",
        ] or filename.lower().endswith(".zip")

        if not is_zip:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Only ZIP files are allowed"
            )

        # Use standard cache directory
        models_dir = get_cache_directory()
        timestamp = datetime.now().timestamp()

        # Handle ZIP file upload
        file_path, time_series_path = await _handle_zip_upload(file, name, models_dir, timestamp)

        # Store metadata
        uploaded_models[name] = DistributionModelInfo(
            name=name, description=description, created_at=datetime.now(), file_path=str(file_path)
        )

        # Persist metadata to disk
        save_metadata(uploaded_models)

        logger.info(f"Uploaded distribution system '{name}' to cache: {file_path}")

        response = {
            "status": "success",
            "message": f"Distribution system '{name}' uploaded successfully",
            "name": name,
            "file_path": str(file_path),
        }

        if time_series_path:
            response["time_series_path"] = str(time_series_path)

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Upload failed: {str(e)}"
        )


@router.get("", response_model=List[DistributionModelInfo])
async def list_distribution_models(refresh: bool = False):
    """
    List all uploaded distribution system models.

    Args:
        refresh: If True, refresh the list from cache directory
    """
    try:
        if refresh:
            refresh_models_from_cache(uploaded_models)
        return list(uploaded_models.values())
    except Exception as e:
        logger.error(f"Failed to list models: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list models: {str(e)}",
        )


@router.get("/{model_name}")
async def get_distribution_model(model_name: str):
    """Get a specific distribution system model by name."""
    try:
        if model_name not in uploaded_models:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Distribution system '{model_name}' not found",
            )

        model_info = uploaded_models[model_name]
        logger.info(f"Retrieving distribution system '{model_name}' from cache")
        logger.info(f"model_info: {model_info}")
        system = DistributionSystem.from_json(model_info.file_path)

        logger.info(
            f"Loaded distribution system '{model_name}' with "
            f"{len(list(system.iter_all_components()))} components"
        )

        return {
            "name": model_name,
            "description": model_info.description,
            "created_at": model_info.created_at,
            "number_of_components": len(list(system.iter_all_components())),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve model: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve model: {str(e)}",
        )


@router.delete("/{model_name}")
async def delete_distribution_model(model_name: str):
    """Delete a distribution system model by name."""
    try:
        if model_name not in uploaded_models:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Distribution system '{model_name}' not found",
            )

        model_info = uploaded_models[model_name]
        json_path = Path(model_info.file_path)

        # Derive time series folder path from JSON path
        # e.g., "model_123.json" -> "model_123_time_series"
        time_series_path = json_path.parent / f"{json_path.stem}_time_series"

        # Remove JSON file
        if json_path.exists():
            json_path.unlink()
            logger.info(f"Deleted JSON file: {json_path}")

        # Remove time series folder if it exists
        if time_series_path.exists() and time_series_path.is_dir():
            shutil.rmtree(time_series_path)
            logger.info(f"Deleted time series folder: {time_series_path}")

        # Remove from memory
        del uploaded_models[model_name]

        # Update metadata
        save_metadata(uploaded_models)

        logger.info(f"Deleted distribution system '{model_name}'")

        return {
            "status": "success",
            "message": f"Distribution system '{model_name}' deleted successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete model: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete model: {str(e)}",
        )
