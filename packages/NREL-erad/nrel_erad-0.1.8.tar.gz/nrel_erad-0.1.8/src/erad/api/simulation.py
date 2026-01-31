"""Simulation endpoints for the ERAD REST API."""

from tempfile import NamedTemporaryFile, TemporaryDirectory
from typing import Dict
from pathlib import Path
import zipfile


from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse
from loguru import logger


from erad.runner import HazardSimulator, HazardScenarioGenerator
from erad.systems.asset_system import AssetSystem
from erad.models.asset import Asset


from .models import (
    ScenarioGenerationRequest,
    DistributionModelInfo,
    SimulationRequest,
    HazardModelInfo,
)
from .helpers import _load_distribution_system


router = APIRouter(tags=["simulation"])


# In-memory storage - will be initialized from main.py
uploaded_models: Dict[str, DistributionModelInfo] = {}
uploaded_hazard_models: Dict[str, HazardModelInfo] = {}


@router.post("/simulate")
async def run_simulation(request: SimulationRequest):
    """
    Run a hazard simulation on a distribution system using cached models.

    This endpoint loads distribution and hazard models from cache by name,
    then runs a simulation and returns the results as a downloadable SQLite file.
    """
    try:
        logger.info(
            f"Starting hazard simulation with distribution model '{request.distribution_system_name}' and hazard model '{request.hazard_system_name}'"
        )

        # Load distribution system from cache
        if request.distribution_system_name not in uploaded_models:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Distribution model '{request.distribution_system_name}' not found in cache",
            )
        dist_system = _load_distribution_system(
            uploaded_models,
            request.distribution_system_name,
        )

        # Load hazard system from cache
        if request.hazard_system_name not in uploaded_hazard_models:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Hazard model '{request.hazard_system_name}' not found in cache",
            )

        from erad.systems.hazard_system import HazardSystem

        hazard_model_path = uploaded_hazard_models[request.hazard_system_name].file_path
        hazard_system = HazardSystem.from_json(hazard_model_path)

        # Create asset system
        asset_system = AssetSystem.from_gdm(dist_system)

        # Run simulation
        simulator = HazardSimulator(asset_system)
        simulator.run(hazard_system, request.curve_set)

        # Get results
        assets = list(asset_system.get_components(Asset))
        hazard_count = len(list(hazard_system.iter_all_components()))

        # Export results to a temporary file
        # Create a temporary file that won't be automatically deleted
        temp_file = NamedTemporaryFile(mode="wb", suffix=".sqlite", delete=False)
        results_path = temp_file.name
        temp_file.close()

        asset_system.export_results(results_path)

        logger.info(
            f"Simulation completed for {len(assets)} assets with {hazard_count} hazard models"
        )
        logger.info(f"Results exported to {results_path}")

        # Return the file as a downloadable response
        filename = (
            f"{request.distribution_system_name}_{request.hazard_system_name}_results.sqlite"
        )
        return FileResponse(
            path=results_path,
            media_type="application/x-sqlite3",
            filename=filename,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Simulation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Simulation failed: {str(e)}",
        )


@router.post("/generate-scenarios")
async def generate_scenarios(request: ScenarioGenerationRequest):
    """
    Generate hazard scenarios for a distribution system.

    This endpoint runs simulation and generates sample scenarios with
    specific asset outages based on survival probabilities.
    Returns a ZIP file containing tracked_changes.json and time series folder.
    """
    try:
        logger.info(f"Generating {request.number_of_samples} scenarios with seed {request.seed}")

        # Load distribution system from cache
        if request.distribution_system_name not in uploaded_models:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Distribution model '{request.distribution_system_name}' not found in cache",
            )
        dist_system = _load_distribution_system(
            uploaded_models,
            request.distribution_system_name,
        )

        # Create asset system
        asset_system = AssetSystem.from_gdm(dist_system)

        from erad.systems.hazard_system import HazardSystem

        hazard_model_path = uploaded_hazard_models[request.hazard_system_name].file_path
        hazard_system = HazardSystem.from_json(hazard_model_path)

        # Generate scenarios
        generator = HazardScenarioGenerator(
            asset_system=asset_system, hazard_system=hazard_system, curve_set=request.curve_set
        )

        tracked_changes = generator.samples(
            number_of_samples=request.number_of_samples, seed=request.seed
        )

        # Create system with tracked changes
        from gdm.distribution import DistributionSystem

        logger.info(f"Creating distribution system with {len(tracked_changes)} tracked changes")

        system = DistributionSystem(auto_add_composed_components=True)
        logger.info("Adding original components from distribution system")
        system.add_components(*tracked_changes)

        logger.info("Packaging scenarios into ZIP file")

        # Create temporary directory for output files
        with TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Export tracked changes to JSON
            json_path = tmpdir_path / "tracked_changes.json"

            system.to_json(str(json_path))
            time_series_folder = tmpdir_path / "tracked_changes_time_series"

            # Create ZIP file
            temp_zip = NamedTemporaryFile(mode="wb", suffix=".zip", delete=False)
            zip_path = temp_zip.name
            temp_zip.close()

            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                # Add tracked_changes.json
                zipf.write(json_path, "tracked_changes.json")

                # Add time series folder if it exists
                if time_series_folder.exists() and time_series_folder.is_dir():
                    logger.info(f"Adding time series folder: {time_series_folder}")
                    for file_path in time_series_folder.rglob("*"):
                        if file_path.is_file():
                            arcname = f"{time_series_folder.name}/{file_path.relative_to(time_series_folder)}"
                            zipf.write(file_path, arcname)
                else:
                    logger.info("No time series folder found for distribution model")

        logger.info(f"Generated {len(tracked_changes)} scenario changes and packaged in ZIP")

        # Return the ZIP file as a downloadable response
        filename = (
            f"{request.distribution_system_name}_scenarios_{request.number_of_samples}samples.zip"
        )
        return FileResponse(
            path=zip_path,
            media_type="application/zip",
            filename=filename,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Scenario generation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Scenario generation failed: {str(e)}",
        )
