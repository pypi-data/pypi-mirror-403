"""Load SVG diagrams from YAML specifications."""

from pathlib import Path

import yaml

from .animations import create_animated_diagram


def _load_library(library_path: str | Path) -> dict:
    """Load definitions from a library file.

    Args:
        library_path: Path to the library YAML file.

    Returns:
        Dictionary of definitions from the library.

    Raises:
        FileNotFoundError: If the library file doesn't exist.
    """
    path = Path(library_path)
    if not path.exists():
        raise FileNotFoundError(f"Library file not found: {library_path}")

    content = path.read_text()
    return yaml.safe_load(content) or {}


def _load_all_definitions(spec: dict) -> dict:
    """Load and merge definitions from libraries and local definitions.

    Libraries are loaded first, then local definitions override them.

    Args:
        spec: The parsed YAML specification.

    Returns:
        Merged dictionary of all definitions.
    """
    definitions = {}

    # Load from library files first
    for library_path in spec.get("libraries", []):
        library_defs = _load_library(library_path)
        definitions.update(library_defs)

    # Local definitions override library definitions
    definitions.update(spec.get("definitions", {}))

    return definitions


def _expand_element(element: dict, definitions: dict) -> dict:
    """Expand a 'use' reference into a full element spec.

    Args:
        element: Element dict, possibly containing a 'use' key.
        definitions: Dictionary of available definitions.

    Returns:
        Expanded element dict with definition merged with overrides.

    Raises:
        ValueError: If the referenced definition doesn't exist.
    """
    if "use" not in element:
        return element

    def_name = element["use"]
    if def_name not in definitions:
        raise ValueError(f"Unknown definition: {def_name}")

    # Start with a copy of the definition
    expanded = definitions[def_name].copy()

    # Apply overrides from the use statement (except 'use' itself)
    for key, value in element.items():
        if key != "use":
            expanded[key] = value

    return expanded


def _expand_definitions(spec: dict) -> dict:
    """Expand all 'use' references in a specification.

    Args:
        spec: The parsed YAML specification.

    Returns:
        Specification with all 'use' references expanded.
    """
    definitions = _load_all_definitions(spec)
    elements = spec.get("elements", [])

    expanded_elements = [_expand_element(el, definitions) for el in elements]

    result = spec.copy()
    result["elements"] = expanded_elements
    # Remove definitions and libraries from output (not needed by create_animated_diagram)
    result.pop("definitions", None)
    result.pop("libraries", None)

    return result


def create_diagram_from_yaml(yaml_content: str) -> str:
    """Create an SVG diagram from a YAML specification.

    Args:
        yaml_content: YAML string containing the diagram specification.
            Should have the same structure as the dict passed to
            create_animated_diagram:
            - width: Canvas width (default 400)
            - height: Canvas height (default 300)
            - definitions: Optional dict of reusable element definitions
            - elements: List of shape specifications (can use 'use' to
                reference definitions)

    Returns:
        SVG content as a string.

    Raises:
        ValueError: If the YAML contains invalid element specifications.
        yaml.YAMLError: If the YAML is malformed.
    """
    spec = yaml.safe_load(yaml_content)
    expanded_spec = _expand_definitions(spec)
    return create_animated_diagram(expanded_spec)
