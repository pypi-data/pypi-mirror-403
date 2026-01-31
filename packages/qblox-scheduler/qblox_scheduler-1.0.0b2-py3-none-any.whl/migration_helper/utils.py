# Repository: https://gitlab.com/qblox/packages/software/qblox-scheduler
# Licensed according to the LICENSE file on the main branch
"""Utils for migration CLI."""

import base64
import contextlib
import difflib
import json
import tempfile
from collections.abc import Callable
from copy import deepcopy
from pathlib import Path
from typing import Any

import numpy as np
import ruamel.yaml
from rich.console import Console
from rich.text import Text


def find_and_replace_in_file(
    list_of_config_files: list[Path],
    verbose: bool = False,
    dry_run: bool = False,
) -> tuple[list[str], list[str]]:
    """
    Find and replaces mentions of 'quantify_scheduler' in the JSON
    and YAML configuration files of quantify with 'qblox_scheduler'.

    Args:
        list_of_config_files: List of configuration files to migrate
        verbose: If True, prints verbose output related to errors
        dry_run: If True, shows changes without applying them

    Returns:
    -------
        A list of the migrated and non-migrated files.

    """
    migrated_files: list[str] = []
    non_migrated_files: list[str] = []

    for config_file in list_of_config_files:
        if config_file.suffix in (".yaml", ".yml"):
            result = transform_yaml_file(config_file, config_file, verbose=verbose, dry_run=dry_run)
        else:
            result = transform_json_file(config_file, config_file, verbose=verbose, dry_run=dry_run)

        if result:
            migrated_files.append(config_file.name)
        else:
            non_migrated_files.append(config_file.name)

    return migrated_files, non_migrated_files


def show_transformation_diff(
    input_file: str | Path,
    transformed_data: dict[str, Any],
    serializer_func: Callable,
    verbose: bool = False,
) -> bool:
    """
    Show the diff of transformation changes.

    Args:
        input_file: Path to the input file
        transformed_data: Transformed data object
        serializer_func: Function to serialize data (e.g., yaml.dump, json.dump)
        verbose: If True, prints verbose output

    Returns:
        True if changes were shown, False otherwise

    """
    with open(input_file) as f:
        original_content = f.read()

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=Path(input_file).suffix, delete=False
    ) as temp_file:
        temp_path = Path(temp_file.name)

    try:
        serializer_func(transformed_data, temp_path)
        with open(temp_path) as f:
            transformed_content = f.read()

        if original_content != transformed_content:
            console = Console()
            console.print(f"\n[bold blue]Changes for {Path(input_file).name}:[/bold blue]")

            diff = difflib.unified_diff(
                original_content.splitlines(keepends=True),
                transformed_content.splitlines(keepends=True),
                fromfile=f"{Path(input_file).name} (original)",
                tofile=f"{Path(input_file).name} (transformed)",
                lineterm="",
            )

            for line in diff:
                if line.startswith(("---", "+++")):
                    console.print(f"[bold]{line.rstrip()}[/bold]")
                elif line.startswith("@@"):
                    console.print(f"[cyan]{line.rstrip()}[/cyan]")
                elif line.startswith("-"):
                    console.print(f"[red]{line.rstrip()}[/red]")
                elif line.startswith("+"):
                    console.print(f"[green]{line.rstrip()}[/green]")
                else:
                    console.print(line.rstrip())

            console.print()
            return True
        else:
            if verbose:
                console = Console()
                console.print(f"[yellow]No changes needed for {Path(input_file).name}[/yellow]")
            return False
    finally:
        temp_path.unlink(missing_ok=True)


def convert_ndarray_to_base64(data: list[Any], dtype: str = "float64") -> dict[str, Any]:
    """
    Convert numpy array data to base64 encoded format.

    Args:
        data: List of values to convert
        dtype: Data type for the array

    Returns:
        Dictionary with data, shape, and dtype

    """
    if not data:
        return {"data": "", "shape": [0], "dtype": dtype}

    arr = np.array(data, dtype=dtype)

    encoded_data = base64.b64encode(arr.tobytes()).decode("utf-8")

    return {"data": encoded_data, "shape": list(arr.shape), "dtype": str(arr.dtype)}


def extract_short_type_name(deserialization_type: str) -> str:
    """
    Extract short type name from full deserialization type.

    Args:
        deserialization_type: Full type name like "quantify_scheduler.BasicTransmonElement"

    Returns:
        Short type name like "BasicTransmonElement"

    """
    return deserialization_type.split(".")[-1]


def transform_acq_weights(weights_data: dict[str, Any]) -> dict[str, Any]:
    """
    Transform acquisition weights from old format to new format.

    Args:
        weights_data: Old format weights data

    Returns:
        New format weights data

    """
    if weights_data.get("deserialization_type") == "ndarray":
        data = weights_data.get("data", [])
        return convert_ndarray_to_base64(data)
    return weights_data


def transform_element(element_data: dict[str, Any]) -> dict[str, Any]:
    """
    Transform a single element from old format to new format.

    Args:
        element_data: Element data in old format

    Returns:
        Element data in new format

    """
    if isinstance(element_data, str):
        element_data = json.loads(element_data)
    data = element_data.get("data", {})

    deserialization_type = element_data.get("deserialization_type", "")
    element_type = extract_short_type_name(deserialization_type)

    transformed = deepcopy(data)
    transformed["element_type"] = element_type

    if "measure" in transformed and isinstance(transformed["measure"], dict):
        measure = transformed["measure"]
        if "acq_weights_a" in measure:
            measure["acq_weights_a"] = transform_acq_weights(measure["acq_weights_a"])
        if "acq_weights_b" in measure:
            measure["acq_weights_b"] = transform_acq_weights(measure["acq_weights_b"])

        if "acq_weights_sampling_rate" in measure and measure["acq_weights_sampling_rate"] is None:
            measure["acq_weights_sampling_rate"] = 1.0

    if "rxy" in transformed and isinstance(transformed["rxy"], dict):
        rxy = transformed["rxy"]
        if "motzoi" in rxy:
            motzoi_value = rxy.pop("motzoi")
            duration = rxy.get("duration", 8)
            rxy["beta"] = motzoi_value * duration / 8

    for key, value in transformed.items():
        if isinstance(value, dict) and "name" not in value:
            value["name"] = key

    return transformed


def transform_edge(edge_data: dict[str, Any]) -> dict[str, Any]:
    """
    Transform a single edge from old format to new format.

    Args:
        edge_data: Edge data in old format

    Returns:
        Edge data in new format

    """
    if isinstance(edge_data, str):
        edge_data = json.loads(edge_data)
    data = edge_data.get("data", {})

    deserialization_type = edge_data.get("deserialization_type", "")
    edge_type = extract_short_type_name(deserialization_type)

    transformed = deepcopy(data)
    transformed["edge_type"] = edge_type

    if "name" not in transformed:
        parent = transformed.get("parent_element_name", "")
        child = transformed.get("child_element_name", "")
        if parent and child:
            transformed["name"] = f"{parent}_{child}"

    for key, value in transformed.items():
        if isinstance(value, dict) and "name" not in value:
            value["name"] = key
            if "q0_phase_correction" in value:
                value["parent_phase_correction"] = value.pop("q0_phase_correction")
            if "q1_phase_correction" in value:
                value["child_phase_correction"] = value.pop("q1_phase_correction")

    return transformed


def transform_quantum_device(old_data: dict[str, Any]) -> dict[str, Any]:
    """
    Transform the entire quantum device configuration.

    Args:
        old_data: Old format device data

    Returns:
        New format device data

    """
    device_data = old_data.get("data", {})

    transformed = deepcopy(device_data)

    if "elements" in transformed:
        new_elements = {}
        for element_name, element_data in transformed["elements"].items():
            new_elements[element_name] = transform_element(element_data)
        transformed["elements"] = new_elements

    if "edges" in transformed:
        new_edges = {}
        for edge_name, edge_data in transformed["edges"].items():
            new_edges[edge_name] = transform_edge(edge_data)
        transformed["edges"] = new_edges

    if "cfg_sched_repetitions" in transformed:
        reps = transformed["cfg_sched_repetitions"]
        if isinstance(reps, str):
            with contextlib.suppress(ValueError):
                transformed["cfg_sched_repetitions"] = int(reps)

    return transformed


def transform_hardware_config(old_data: dict[str, Any]) -> dict[str, Any]:
    """
    Transform hardware configuration from old format to new format.

    Args:
        old_data: Old format hardware config data

    Returns:
        New format hardware config data

    """
    transformed = deepcopy(old_data)
    transformed["config_type"] = "QbloxHardwareCompilationConfig"

    return transformed


def transform_yaml_file(
    input_file: str | Path, output_file: str | Path, verbose: bool = False, dry_run: bool = False
) -> bool:
    """
    Transform a YAML file to rename motzoi to beta in BasicTransmonElement rxy sections.

    Args:
        input_file: Path to input YAML file
        output_file: Path to output YAML file
        verbose: If True, prints verbose output related to errors
        dry_run: If True, shows changes without applying them

    Returns:
        True if the file was transformed, False otherwise

    """
    yaml = ruamel.yaml.YAML()
    yaml.preserve_quotes = True
    yaml.width = 4096

    try:
        with open(input_file) as file:
            old_data = yaml.load(file)
        new_data = deepcopy(old_data)

        if "elements" in new_data:
            for element_obj in new_data["elements"].values():
                if "rxy" in element_obj and "motzoi" in element_obj["rxy"]:
                    old_value = element_obj["rxy"].pop("motzoi")
                    duration = element_obj["rxy"].get("duration", 8)
                    element_obj["rxy"]["beta"] = old_value * duration / 8
        else:
            return False

        if new_data != old_data:
            if dry_run:
                return show_transformation_diff(input_file, new_data, yaml.dump, verbose)
            else:
                with open(output_file, "w") as file:
                    yaml.dump(new_data, file)
                return True

        return False

    except Exception as e:  # noqa: BLE001
        if verbose:
            console = Console()
            console.print(Text(f"Error processing YAML file: {input_file}", style="yellow"))
            console.print(Text(f"Error: {e}", style="red"))
        return False


def transform_json_file(
    input_file: str | Path, output_file: str | Path, verbose: bool = False, dry_run: bool = False
) -> bool:
    """
    Transform a JSON file from old format to new format.
    Automatically detects whether it's a quantum device or hardware config.

    Args:
        input_file: Path to input JSON file
        output_file: Path to output JSON file
        verbose: If True, prints verbose output related to errors
        dry_run: If True, shows changes without applying them

    Returns:
        True if the file was transformed, False otherwise

    """
    try:
        with open(input_file) as f:
            old_data = json.load(f)

        if "QuantumDevice" in old_data.get("deserialization_type", ""):
            new_data = transform_quantum_device(old_data)
        elif ".QbloxHardwareCompilationConfig" in old_data.get("config_type", ""):
            new_data = transform_hardware_config(old_data)
        else:
            return False

        def json_dump(data: dict[str, Any], path: str | Path) -> None:
            with open(path, "w") as f:
                json.dump(data, f, indent=4)

        if dry_run:
            return show_transformation_diff(input_file, new_data, json_dump, verbose)
        else:
            json_dump(new_data, output_file)
            return True

    except Exception as e:  # noqa: BLE001
        if verbose:
            console = Console()
            console.print(Text(f"Error loading JSON file: {input_file}", style="yellow"))
            console.print(Text(f"Error: {e}", style="red"))
        return False
