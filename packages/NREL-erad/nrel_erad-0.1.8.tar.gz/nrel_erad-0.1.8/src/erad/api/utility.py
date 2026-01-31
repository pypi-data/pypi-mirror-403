"""Utility endpoints for the ERAD REST API."""

from datetime import datetime
from typing import Dict

from fastapi import APIRouter, HTTPException, status
from loguru import logger

from .models import HealthCheckResponse, DistributionModelInfo, HazardModelInfo
from .cache import (
    get_cache_directory,
    get_hazard_cache_directory,
    refresh_models_from_cache,
    refresh_hazard_models_from_cache,
)


router = APIRouter(tags=["utility"])


# In-memory storage - will be initialized from main.py
uploaded_models: Dict[str, DistributionModelInfo] = {}
uploaded_hazard_models: Dict[str, HazardModelInfo] = {}


@router.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint."""
    return {"message": "ERAD Hazard Simulator API", "version": "1.0.0", "docs": "/docs"}


@router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Health check endpoint."""
    return HealthCheckResponse(status="healthy", timestamp=datetime.now(), version="1.0.0")


@router.get("/cache-info")
async def get_cache_info():
    """Get information about the cache directories."""
    try:
        # Distribution models cache
        dist_cache_dir = get_cache_directory()
        dist_model_files = list(dist_cache_dir.glob("*.json"))
        dist_model_files = [f for f in dist_model_files if f.name != "models_metadata.json"]
        dist_total_size = sum(f.stat().st_size for f in dist_model_files)

        # Hazard models cache
        hazard_cache_dir = get_hazard_cache_directory()
        hazard_model_files = list(hazard_cache_dir.glob("*.json"))
        hazard_model_files = [f for f in hazard_model_files if f.name != "hazard_metadata.json"]
        hazard_total_size = sum(f.stat().st_size for f in hazard_model_files)

        total_size = dist_total_size + hazard_total_size

        return {
            "distribution_models": {
                "cache_directory": str(dist_cache_dir),
                "total_models": len(uploaded_models),
                "total_files": len(dist_model_files),
                "total_size_bytes": dist_total_size,
                "total_size_mb": round(dist_total_size / (1024 * 1024), 2),
            },
            "hazard_models": {
                "cache_directory": str(hazard_cache_dir),
                "total_models": len(uploaded_hazard_models),
                "total_files": len(hazard_model_files),
                "total_size_bytes": hazard_total_size,
                "total_size_mb": round(hazard_total_size / (1024 * 1024), 2),
            },
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
        }
    except Exception as e:
        logger.error(f"Failed to get cache info: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get cache info: {str(e)}",
        )


@router.post("/refresh-cache")
async def refresh_cache():
    """
    Refresh the model lists from cache directories.

    This will scan the cache directories for model files and update the metadata.
    """
    try:
        refresh_models_from_cache(uploaded_models)
        refresh_hazard_models_from_cache(uploaded_hazard_models)
        return {
            "status": "success",
            "message": "Cache refreshed successfully",
            "total_distribution_models": len(uploaded_models),
            "total_hazard_models": len(uploaded_hazard_models),
            "distribution_models": list(uploaded_models.keys()),
            "hazard_models": list(uploaded_hazard_models.keys()),
        }
    except Exception as e:
        logger.error(f"Failed to refresh cache: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to refresh cache: {str(e)}",
        )


@router.get("/supported-hazard-types")
async def get_supported_hazard_types():
    """Get list of supported hazard types."""
    return {
        "hazard_types": ["earthquake", "flood", "flood_area", "wind", "fire", "fire_area"],
        "descriptions": {
            "earthquake": "Earthquake Model (EarthQuakeModel)",
            "flood": "Flood Model (FloodModel)",
            "flood_area": "Flood Area Model (FloodModelArea)",
            "wind": "Wind Model (WindModel)",
            "fire": "Fire Model (FireModel)",
            "fire_area": "Fire Area Model (FireModelArea)",
        },
    }


@router.get("/default-curve-sets")
async def get_default_curve_sets():
    """Get information about default fragility curve sets."""
    return {
        "curve_sets": ["DEFAULT_CURVES"],
        "default": "DEFAULT_CURVES",
        "description": "Default fragility curves for various hazard types and assets",
    }
