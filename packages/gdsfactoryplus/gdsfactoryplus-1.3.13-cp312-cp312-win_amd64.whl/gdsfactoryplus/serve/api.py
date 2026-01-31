"""API module for the application."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING, Literal, cast

from fastapi import BackgroundTasks
from fastapi.exceptions import HTTPException
from fastapi.responses import FileResponse

from .app import app, logger

if TYPE_CHECKING:
    import sax
    import yaml
    from gdsfactory.read import from_yaml_gen

    import gdsfactoryplus.core.bbox as bb
    import gdsfactoryplus.core.database as db
    import gdsfactoryplus.core.export_spice as spe
    import gdsfactoryplus.core.parse_spice as spp
    import gdsfactoryplus.core.pdk as gfp_pdk
    import gdsfactoryplus.models as m
    import gdsfactoryplus.simulate as s
    from gdsfactoryplus import settings
    from gdsfactoryplus.core import build, kcl
else:
    from gdsfactoryplus.core.lazy import lazy_import

    sax = lazy_import("sax")
    yaml = lazy_import("yaml")

    bb = lazy_import("gdsfactoryplus.core.bbox")
    db = lazy_import("gdsfactoryplus.core.database")
    spe = lazy_import("gdsfactoryplus.core.export_spice")
    spp = lazy_import("gdsfactoryplus.core.parse_spice")
    gfp_pdk = lazy_import("gdsfactoryplus.core.pdk")
    m = lazy_import("gdsfactoryplus.models")
    settings = lazy_import("gdsfactoryplus.settings")
    s = lazy_import("gdsfactoryplus.simulate")
    build = lazy_import("gdsfactoryplus.core.build")
    kcl = lazy_import("gdsfactoryplus.core.kcl")
    from_yaml_gen = lazy_import("gdsfactory.read.from_yaml_gen")


@app.get("/tree")
def tree() -> dict:
    """Tree is used as health check."""
    return {}


@app.get("/health")
def health() -> dict:
    """Health check endpoint for the API server."""
    return {"status": "healthy", "service": "gdsfactoryplus"}


def _build_cell(
    name: str, *, with_metadata: bool = True, register: bool = True
) -> None:
    """Build a GDS cell by name (background task).

    Args:
        name: Name of the cell to build.
        with_metadata: Whether to include metadata in the GDS file.
        register: Whether to re-register the cell in the KLayout cache.
    """
    paths = db.get_factory_sources_by_name(name)
    if register and paths:
        names, _ = gfp_pdk.register_cells(paths=paths.values())
        kcl.clear_cells_from_cache(*names)
    else:
        kcl.clear_cells_from_cache(name)
    build.build_by_names(name, with_metadata=with_metadata)


@app.get("/api/build-cell")
def build_cell(
    name: str,
    background_tasks: BackgroundTasks,
    *,
    with_metadata: bool = True,
    register: bool = True,
) -> dict:
    """Build a GDS cell by name.

    Args:
        name: Name of the cell to build.
        background_tasks: Fastapi background tasks
        with_metadata: Whether to include metadata in the GDS file.
        register: Whether to re-register the cell in the KLayout cache.
    """
    background_tasks.add_task(
        _build_cell, name, with_metadata=with_metadata, register=register
    )
    return {"detail": f"building {name} in background."}


def _build_cells(
    names: list[str],
    *,
    with_metadata: bool = True,
    register: bool = True,
) -> None:
    """Build multiple GDS cells by names (background task).

    Args:
        names: List of cell names to build.
        with_metadata: Whether to include metadata in the GDS files.
        register: Whether to re-register the cells in the KLayout cache.
    """
    logger.debug(f"{names}")
    paths = db.get_factory_sources_by_name(*names)
    if register and paths:
        registered_names, _ = gfp_pdk.register_cells(paths=paths.values())
        kcl.clear_cells_from_cache(*registered_names)
        names = list({*names, *registered_names})
    else:
        kcl.clear_cells_from_cache(*names)
    build.build_by_names(*names, with_metadata=with_metadata)


@app.post("/api/build-cells")
def build_cells(
    names: list[str],
    background_tasks: BackgroundTasks,
    *,
    with_metadata: bool = True,
    register: bool = True,
) -> dict:
    """Build multiple GDS cells by names.

    Args:
        names: List of cell names to build.
        background_tasks: Fastapi background tasks
        with_metadata: Whether to include metadata in the GDS files.
        register: Whether to re-register the cells in the KLayout cache.
    """
    background_tasks.add_task(
        _build_cells, names, with_metadata=with_metadata, register=register
    )
    return {"detail": f"building {len(names)} cells in background."}


@app.post("/api/simulate")
def simulate(
    sim: m.Simulation,
    how: Literal["from_layout", "from_netlist"] = "from_layout",
) -> m.SerializedSimulationResult | dict[str, str]:
    """Simulate a factory.

    Args:
        sim: Simulation object containing the name, layout, and model.
        how: Method to use for simulation, either "from_layout" or "from_netlist".

    Returns:
        SerializedSimulationResult: The result of the simulation, serialized.
    """
    try:
        sdict = sax.sdict(
            s.simulate(sim.name, layout=sim.layout, model=sim.model, how=how)
        )
        result: m.SerializedSimulationResult = {}
        for (p, q), v in sdict.items():
            if (abs(v) < 1e-7).all():
                continue
            if p not in result:
                result[p] = {}
            result[p][q] = m.SerializedComplexArray.from_numpy(v)
    except Exception as e:  # noqa: BLE001
        return {"detail": str(e)}
    return result


@app.get("/api/simulate")
def simulate_get(
    name: str,
) -> m.SerializedSimulationResult | dict[str, str]:
    """Simulate a factory.

    Args:
        name: name of the factory to simulate with default arguments.

    Returns:
        SerializedSimulationResult: The result of the simulation, serialized.
    """
    return simulate(m.Simulation(name=name, layout={}, model={}))


@app.post("/api/parse-spice")
def parse_spice_api(request: m.ParseSpiceRequest) -> dict[str, str]:
    """Parse a SPICE file to YAML format.

    Args:
        request: ParseSpiceRequest containing path and flavor.

    Returns:
        dict: Either {'content': yaml_string} on success
            or {'detail': error_message} on error.
    """
    try:
        logger.info(
            f"Parse SPICE API called with path: {request.path}, "
            f"flavor: {request.flavor}"
        )

        if request.flavor.lower().strip() != "oc":
            error_msg = (
                f"Invalid spice flavor. Currently only 'oc' is supported."
                f" Got: {request.flavor}."
            )
            logger.warning(error_msg)
            return {"detail": error_msg}

        file_path = Path(request.path).expanduser().resolve()
        logger.info(f"Resolved file path: {file_path}")

        if not file_path.exists():
            error_msg = f"File {file_path} does not exist."
            logger.error(error_msg)
            return {"detail": error_msg}

        if file_path.suffix.lower() not in (".sp", ".spice"):
            error_msg = f"File {file_path} is not a SPICE file (.sp or .spice)."
            logger.error(error_msg)
            return {"detail": error_msg}

        logger.info("Registering cells...")
        # Register cells before parsing
        gfp_pdk.register_cells()

        logger.info("Parsing SPICE file...")
        # Parse the SPICE file
        recnet = spp.parse_oc_spice(file_path)

        logger.info(f"Parsed netlist type: {type(recnet)}")
        logger.info(
            f"Parsed netlist keys: {
                list(recnet.keys()) if isinstance(recnet, dict) else 'Not a dict'
            }"
        )

        logger.info("Converting to YAML...")
        yaml_str = yaml.safe_dump(recnet, sort_keys=False)
        logger.info(f"Generated YAML length: {len(yaml_str)}")

    except Exception as e:  # noqa: BLE001
        error_msg = f"SPICE parsing failed: {e!s}"
        logger.error(error_msg)
        logger.error(f"Exception type: {type(e).__name__}")
        logger.error(f"Exception args: {e.args}")
        return {"detail": error_msg}

    else:
        return {"content": yaml_str}


@app.post("/api/export-spice")
def export_spice_api(request: m.ExportSpiceRequest) -> dict[str, str]:
    """Export a GDS file to SPICE format.

    Args:
        request: ExportSpiceRequest containing path and flavor.

    Returns:
        dict: Either {'content': spice_string} on success
            or {'detail': error_message} on error.
    """
    try:
        # Validate flavor
        supported_flavors = ["spectre", "xyce", "ngspice"]
        flavor = request.flavor.lower().strip()
        if flavor not in supported_flavors:
            return {
                "detail": f"Invalid flavor '{flavor}'. "
                f"Supported export formats: {supported_flavors}."
            }

        file_path = Path(request.path).expanduser().resolve()
        if not file_path.exists():
            return {"detail": f"File {file_path} does not exist."}

        if file_path.suffix.lower() not in (".gds", ".oas"):
            return {"detail": f"File {file_path} is not a GDS or OAS file."}

        # Register cells before exporting
        gfp_pdk.register_cells()

        # Export to SPICE
        spice_content = spe.export_spice(file_path, cast(spe.SpiceFlavor, flavor))

    except Exception as e:  # noqa: BLE001
        logger.error(f"SPICE export failed: {e}")
        return {"detail": f"SPICE export failed: {e!s}"}

    else:
        return {"content": spice_content}


@app.post("/api/schematic-to-python")
def schematic_to_python_api(request: m.SchematicToPythonRequest) -> dict[str, str]:
    """Convert a schematic YAML file to Python code.

    Args:
        request: SchematicToPythonRequest containing path and function_name.

    Returns:
        dict: Either {'content': python_code} on success
            or {'detail': error_message} on error.
    """
    try:
        file_path = Path(request.path).expanduser().resolve()
        logger.info(f"Converting schematic to Python: {file_path}")

        if not file_path.exists():
            return {"detail": f"File {file_path} does not exist."}

        if file_path.suffix.lower() not in (".yml", ".yaml"):
            return {"detail": f"File {file_path} is not a YAML file."}

        # Read the YAML content
        yaml_content = file_path.read_text()

        # Generate Python code using gdsfactory's from_yaml_gen module
        python_code = from_yaml_gen.from_yaml_to_code(
            yaml_content,
            function_name=request.function_name,
        )

    except Exception as e:  # noqa: BLE001
        error_msg = f"Schematic to Python conversion failed: {e!s}"
        logger.error(error_msg)
        return {"detail": error_msg}

    else:
        return {"content": python_code}


@app.get("/api/port-center")
def port_center(netlist: str, instance: str, port: str) -> dict[str, float]:
    """Get the center coordinates of a port in a netlist."""
    c = gfp_pdk.get_pdk().get_component(netlist)
    x, y = c.insts[instance].ports[port].center
    return {"x": x, "y": y}


@app.post("/api/bbox")
def bbox_api(request: m.BboxRequest) -> dict[str, str]:
    """Generate a bounding box GDS file from an input GDS.

    Args:
        request: BboxRequest containing path and bbox parameters.

    Returns:
        dict: Either {'outpath': output_file_path} on success
            or {'detail': error_message} on error.
    """
    try:
        file_path = Path(request.path).expanduser().resolve()
        if not file_path.exists():
            return {"detail": f"File {file_path} does not exist."}

        if file_path.suffix.lower() not in (".gds", ".oas"):
            return {"detail": f"File {file_path} is not a GDS or OAS file."}

        # Register cells before processing
        gfp_pdk.register_cells()

        # Call the bbox function
        bb.bbox(
            str(file_path),
            request.outpath,
            request.layers_to_keep,
            request.bbox_layer,
            ignore_ports=request.ignore_ports,
        )

        # Return the output path (bbox function handles default naming if outpath empty)
        if request.outpath:
            outpath = Path(request.outpath).expanduser().resolve()
        else:
            # Use the same logic as in bbox._validate_args for default naming
            ext = "gds" if file_path.suffix.lower() == ".gds" else "oas"
            outpath = file_path.with_suffix(f"-bbox.{ext}")

    except Exception as e:  # noqa: BLE001
        logger.error(f"Bbox generation failed: {e}")
        return {"detail": f"Bbox generation failed: {e!s}"}

    else:
        return {"outpath": str(outpath)}


@app.get("/api/download/{path:path}.gds")
def download_gds(path: str) -> FileResponse:
    """Download a GDS file from the project directory.

    Args:
        path: Relative path to the GDS file (without .gds extension).
        background_tasks: FastAPI background tasks for async operations.

    Returns:
        FileResponse: The GDS file as an octet-stream download.
    """
    parts = Path(path).parts
    is_build_path = (parts[0] == "build") and (parts[1] == "gds")
    with_metadata = parts[2] != "no-meta"

    project_dir = settings.get_project_dir()
    file_path = (project_dir / f"{path}.gds").resolve()
    if not file_path.is_relative_to(project_dir):
        logger.error(f"Path traversal attempt: {path}")
        raise HTTPException(status_code=403, detail="Forbidden: Invalid file path.")

    if not file_path.exists() and is_build_path:
        cell_name = parts[-1]
        _build_cell(
            cell_name,
            with_metadata=with_metadata,
            register=False,
        )

    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        raise HTTPException(status_code=404, detail=f"File {file_path} not found.")

    if file_path.suffix.lower() != ".gds":
        logger.error(f"Not a GDS file: {file_path}")
        raise HTTPException(
            status_code=400, detail=f"File {file_path} is not a GDS file."
        )

    return FileResponse(
        path=str(file_path),
        media_type="application/octet-stream",
        filename=file_path.name,
    )


def _get_ngspice() -> Path:
    """Get the path to the ngspice executable."""
    if os.name == "nt":
        strpath = shutil.which("ngspice.exe")
    else:
        strpath = shutil.which("ngspice")
    if strpath is None:
        msg = "Ngspice executable not found in PATH."
        raise FileNotFoundError(msg)
    return Path(strpath).resolve()


def _read_spice_output(path: Path) -> dict[str, list[float]]:
    """Read a typical output file from a spice simulation.

    Args:
        path: Path to the spice output file.

    Returns:
        Dictionary mapping column names to lists of values.
    """
    lines = path.read_text().splitlines()
    lines = [
        re.sub("[ ][ ]*", ",", re.sub("^[ ][ ]*", "", re.sub("[ ][ ]*$", "", line)))
        for line in lines
    ]
    csv_content = "\n".join(lines)

    # Parse CSV manually to avoid pandas dependency
    csv_lines = csv_content.strip().split("\n")
    if not csv_lines:
        return {}

    headers = csv_lines[0].split(",")
    result: dict[str, list[float]] = {h: [] for h in headers}

    for line in csv_lines[1:]:
        values = line.split(",")
        for i, h in enumerate(headers):
            if i < len(values):
                try:
                    result[h].append(float(values[i]))
                except ValueError:
                    result[h].append(0.0)

    return result


def _validate_spice_file(file_path: Path) -> str | None:
    """Validate a SPICE file path.

    Returns:
        Error message if validation fails, None if valid.
    """
    if not file_path.exists():
        return f"File {file_path} does not exist."
    if file_path.suffix.lower() not in (".sp", ".spice", ".cir"):
        return f"File {file_path} is not a SPICE file (.sp, .spice, or .cir)."
    return None


@app.post("/api/check-drc")
def check_drc_api(request: m.DrcRequest) -> dict[str, str]:
    """Run a DRC (Design Rule Check) on a GDS file.

    This uploads the file to a remote DRC server and runs the full design rule
    check for the specified PDK and process.

    Args:
        request: DrcRequest containing the path and optional DRC parameters.

    Returns:
        dict: Either {'content': xml_string} on success
            or {'detail': error_message} on error.
    """
    try:
        file_path = Path(request.path).expanduser().resolve()
        logger.info(f"Running DRC check on: {file_path}")

        if not file_path.exists():
            return {"detail": f"File {file_path} does not exist."}

        if file_path.suffix.lower() not in (".gds", ".oas"):
            return {"detail": f"File {file_path} is not a GDS or OAS file."}

        # Import here to avoid circular imports and for lazy loading
        from gdsfactoryplus.core.check import check_drc
        from gdsfactoryplus.settings import get_settings

        SETTINGS = get_settings()

        # Use provided values or fall back to settings defaults
        pdk = request.pdk or SETTINGS["drc"]["pdk"] or SETTINGS["pdk"]["name"]
        process = request.process or SETTINGS["drc"]["process"]
        timeout = request.timeout or SETTINGS["drc"]["timeout"]
        host = request.host or SETTINGS["drc"]["host"]
        api_key = SETTINGS["api"]["key"]

        xml_content = check_drc(
            str(file_path),
            pdk=pdk,
            process=process,
            timeout=timeout,
            host=host,
            api_key=api_key,
            verbose=False,
        )
        logger.info("DRC check completed successfully")

    except Exception as e:  # noqa: BLE001
        error_msg = f"DRC check failed: {e!s}"
        logger.error(error_msg)
        return {"detail": error_msg}

    else:
        return {"content": xml_content}


@app.post("/api/check-connectivity")
def check_connectivity_api(request: m.ConnectivityRequest) -> dict[str, str]:
    """Run a connectivity check on a GDS file.

    This runs a local connectivity check to verify all layers are properly connected.

    Args:
        request: ConnectivityRequest containing the path to the GDS file.

    Returns:
        dict: Either {'content': xml_string} on success
            or {'detail': error_message} on error.
    """
    try:
        file_path = Path(request.path).expanduser().resolve()
        logger.info(f"Running connectivity check on: {file_path}")

        if not file_path.exists():
            return {"detail": f"File {file_path} does not exist."}

        if file_path.suffix.lower() not in (".gds", ".oas"):
            return {"detail": f"File {file_path} is not a GDS or OAS file."}

        # Import here to avoid circular imports and for lazy loading
        from gdsfactoryplus.core.check import check_conn

        xml_content = check_conn(str(file_path), verbose=False)
        logger.info("Connectivity check completed successfully")

    except Exception as e:  # noqa: BLE001
        error_msg = f"Connectivity check failed: {e!s}"
        logger.error(error_msg)
        return {"detail": error_msg}

    else:
        return {"content": xml_content}


@app.post("/api/check-lvs")
def check_lvs_api(request: m.LvsRequest) -> dict[str, str]:
    """Run an LVS check on a cell against a reference netlist.

    Args:
        request: LvsRequest containing the cell name, netlist path, and optional args.

    Returns:
        dict: Either {'content': xml_string} on success
            or {'detail': error_message} on error.
    """
    try:
        import json
        import secrets
        import tempfile
        from contextlib import suppress

        netpath = Path(request.netpath).expanduser().resolve()
        logger.info(f"Running LVS check: cell={request.cell}, netpath={netpath}")

        if not netpath.exists():
            return {"detail": f"Netlist file {netpath} does not exist."}

        if netpath.suffix.lower() not in (".yml", ".yaml"):
            return {"detail": f"File {netpath} is not a YAML file."}

        # Import here to avoid circular imports and for lazy loading
        from gdsfactoryplus.core.lvs import optical_lvs

        # Register cells before running LVS
        gfp_pdk.register_cells()

        pdk = gfp_pdk.get_pdk()
        cell_func = pdk.cells.get(request.cell, None)
        if cell_func is None:
            return {"detail": f"Cell {request.cell!r} not found in PDK."}

        # Create the cell with optional arguments
        if not request.cellargs:
            cell = cell_func()
        else:
            cell = cell_func(**json.loads(request.cellargs))

        # Run LVS and save to temp file
        temppath = Path(tempfile.gettempdir()) / "lvs" / f"{secrets.token_hex(8)}.lyrdb"
        temppath.parent.mkdir(parents=True, exist_ok=True)

        try:
            rdb = optical_lvs(cell=cell, ref=str(netpath))
            rdb.save(filename=str(temppath))
            xml_content = temppath.read_text()
        finally:
            with suppress(PermissionError):
                temppath.unlink()

        logger.info("LVS check completed successfully")

    except Exception as e:  # noqa: BLE001
        error_msg = f"LVS check failed: {e!s}"
        logger.error(error_msg)
        return {"detail": error_msg}

    else:
        return {"content": xml_content}


@app.post("/api/spice")
def spice_api(request: m.SpiceRequest) -> dict[str, str | dict[str, list[float]]]:
    """Run an ngspice simulation on a SPICE file.

    Args:
        request: SpiceRequest containing the path to the SPICE file.

    Returns:
        dict: Either {'data': simulation_data} on success
            or {'detail': error_message} on error.
    """
    try:
        file_path = Path(request.path).expanduser().resolve()
        logger.info(f"Running ngspice simulation on: {file_path}")

        if error := _validate_spice_file(file_path):
            return {"detail": error}

        # Get ngspice executable
        try:
            ngspice = _get_ngspice()
        except FileNotFoundError as e:
            return {"detail": str(e)}

        # Run ngspice in batch mode
        logger.info(f"Running: {ngspice} -b {file_path}")
        result = subprocess.run(
            [str(ngspice), "-b", str(file_path)],
            cwd=file_path.parent,
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            error_msg = result.stderr or result.stdout or "Unknown error"
            logger.error(f"ngspice failed: {error_msg}")
            return {"detail": f"ngspice simulation failed: {error_msg}"}

        # Look for output.csv in the same directory
        csv_path = file_path.parent / "output.csv"
        if not csv_path.exists():
            return {
                "detail": "output.csv was not created. "
                "Make sure the SPICE file includes a 'wrdata output.csv' command."
            }

        # Read and parse the output
        data = _read_spice_output(csv_path)
        logger.info(f"Parsed ngspice output with columns: {list(data.keys())}")

    except Exception as e:  # noqa: BLE001
        error_msg = f"Spice simulation failed: {e!s}"
        logger.error(error_msg)
        return {"detail": error_msg}

    else:
        return {"data": data}


@app.get("/api/cells")
def list_cells() -> list[str]:
    """List all available cells/components that can be built.

    Returns:
        List of cell/component names from the PDK registry
    """
    try:
        cell_names = db.get_all_factory_names()
        logger.info(f"Retrieved {len(cell_names)} factory names")
    except Exception as e:
        logger.error(f"Failed to list cells: {e!s}")
        raise HTTPException(
            status_code=500, detail=f"Failed to list cells: {e!s}"
        ) from e
    else:
        return cell_names


@app.get("/api/cell-info")
def get_cell_info(name: str) -> dict:
    """Get detailed information about a specific cell/component.

    Args:
        name: Name of the cell/component

    Returns:
        Dictionary with cell metadata including source file and other details
    """
    try:
        factories = db.get_factories_by_name(name)
        if not factories:
            raise HTTPException(status_code=404, detail=f"Cell '{name}' not found")  # noqa: TRY301

        factory_record = factories[name]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get cell info for '{name}': {e!s}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get cell info: {e!s}"
        ) from e
    else:
        return {
            "name": name,
            "source": factory_record.source,
            "status": factory_record.status,
            "message": factory_record.message,
            "pdk_type": factory_record.pdk_type,
            "is_partial": factory_record.is_partial,
            "has_model": factory_record.has_model,
        }
