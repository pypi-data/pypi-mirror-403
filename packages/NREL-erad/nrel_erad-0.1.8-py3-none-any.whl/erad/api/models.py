"""Pydantic models for the ERAD REST API."""

from datetime import datetime
from typing import List, Dict, Any, Optional

from pydantic import BaseModel, Field


class AssetStateData(BaseModel):
    """Model for asset state data."""

    timestamp: datetime
    survival_probability: float = Field(ge=0.0, le=1.0)
    hazard_type: Optional[str] = None
    hazard_value: Optional[float] = None


class AssetData(BaseModel):
    """Model for asset data."""

    name: str
    distribution_asset: str
    asset_state: List[AssetStateData] = []


class HazardModelData(BaseModel):
    """Model for hazard model data."""

    name: str
    timestamp: datetime
    model_data: Dict[str, Any]


class SimulationRequest(BaseModel):
    """Request model for running a simulation."""

    distribution_system_name: str = Field(..., description="Name of the cached distribution model")
    hazard_system_name: str = Field(..., description="Name of the cached hazard model")
    curve_set: str = Field(default="DEFAULT_CURVES", description="Fragility curve set to use")


class ScenarioGenerationRequest(BaseModel):
    """Request model for generating hazard scenarios."""

    distribution_system_name: Optional[str] = None
    hazard_system_name: str = Field(..., description="Name of the cached hazard model")
    number_of_samples: int = Field(default=1, ge=1, description="Number of scenarios to generate")
    seed: int = Field(default=0, ge=0, description="Random seed for reproducibility")
    curve_set: str = "DEFAULT_CURVES"


class PropertyEditData(BaseModel):
    """Model for property edit data."""

    component_uuid: str
    name: str
    value: Any


class TrackedChangeData(BaseModel):
    """Model for tracked change data."""

    scenario_name: str
    timestamp: datetime
    edits: List[PropertyEditData]


class SimulationResponse(BaseModel):
    """Response model for simulation."""

    status: str
    message: str
    asset_count: int
    hazard_count: int
    timestamps: List[datetime]


class DistributionModelInfo(BaseModel):
    """Model for distribution system information."""

    name: str
    description: Optional[str] = None
    created_at: datetime
    file_path: str


class HazardModelInfo(BaseModel):
    """Model for hazard model information."""

    name: str
    description: Optional[str] = None
    created_at: datetime
    file_path: str


class HealthCheckResponse(BaseModel):
    """Health check response model."""

    status: str
    timestamp: datetime
    version: str


class ErrorResponse(BaseModel):
    """Error response model."""

    detail: str
    status_code: int
