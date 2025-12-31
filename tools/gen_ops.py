#!/usr/bin/env python3
"""Operator code generator.

Parses src/ops/kind.rs and generates:
1. src/py/op_generated.rs (Rust Op class)
2. pyropust/__init__.pyi (Python stub Op class)
"""
# ruff: noqa: T201  # Allow print() in this tool

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class OpParam:
    name: str
    py_type: str
    rust_type: str


@dataclass
class OpSpec:
    name: str
    py_name: str
    in_type: str
    out_type: str
    params: list[OpParam]
    variant_name: str
    ns: str | None = None  # Namespace: text, seq, map, coerce, core, etc.
    aliases: list[str] | None = None  # Additional namespaces to alias into


# Type mapping from Python stub types to Rust types
PY_TO_RUST_TYPE = {
    "str": "String",
    "int": "usize",
    "callable": "Py<PyAny>",
    "object": "Py<PyAny>",
}


def parse_kind_rs(path: Path) -> list[OpSpec]:
    """Parse src/ops/kind.rs and extract OpSpec for each variant."""
    content = path.read_text()

    specs: list[OpSpec] = []
    lines = content.split("\n")
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        # Look for doc comments starting with @op
        if line.startswith("/// @op"):
            meta_lines: list[str] = []
            j = i
            while j < len(lines) and lines[j].strip().startswith("///"):
                meta_lines.append(lines[j].strip()[4:])  # Remove "/// "
                j += 1

            # Next non-comment line should be the variant
            while j < len(lines) and not lines[j].strip():
                j += 1

            if j < len(lines):
                variant_line = lines[j].strip().rstrip(",")
                variant_name = variant_line.split("{")[0].split("(")[0].strip()

                spec = parse_meta(meta_lines, variant_name)
                if spec:
                    specs.append(spec)

                i = j + 1
            else:
                i += 1
        else:
            i += 1

    return specs


def parse_meta(meta_lines: list[str], variant_name: str) -> OpSpec | None:
    """Parse meta information from doc comments."""
    name: str | None = None
    py_name: str | None = None
    in_type: str | None = None
    out_type: str | None = None
    params: list[OpParam] = []
    ns: str | None = None
    aliases: list[str] = []

    for raw_line in meta_lines:
        line = raw_line.strip()

        # @op name=foo py=bar
        if line.startswith("@op "):
            parts = line[4:].split()
            for part in parts:
                if "=" in part:
                    key, value = part.split("=", 1)
                    if key == "name":
                        name = value
                    elif key == "py":
                        py_name = value

        # @sig in=Type out=Type
        elif line.startswith("@sig "):
            # Extract in= and out= values more carefully
            # in= value is everything between "in=" and " out="
            # out= value is everything after "out="
            if " in=" in line and " out=" in line:
                in_start = line.index(" in=") + 4
                out_start = line.index(" out=")
                in_type = line[in_start:out_start].strip()
                out_type = line[out_start + 5 :].strip()
            elif line.startswith("@sig in="):
                # Handle case where in= is first
                if " out=" in line:
                    parts = line[9:].split(" out=")
                    in_type = parts[0].strip()
                    out_type = parts[1].strip()
                else:
                    in_type = line[9:].strip()

        # @ns namespace
        elif line.startswith("@ns "):
            ns = line[4:].strip()

        # @alias namespace (for backward compatibility aliases)
        elif line.startswith("@alias "):
            alias_ns = line[7:].strip()
            if alias_ns:
                aliases.append(alias_ns)

        # @param name:type
        elif line.startswith("@param "):
            param_str = line[7:].strip()
            if ":" in param_str:
                param_name, py_type = param_str.split(":", 1)
                rust_type = PY_TO_RUST_TYPE.get(py_type, py_type)
                params.append(OpParam(param_name, py_type, rust_type))

    if name and py_name and in_type and out_type:
        return OpSpec(
            name, py_name, in_type, out_type, params, variant_name, ns, aliases if aliases else None
        )

    return None


def _generate_operator_method(spec: OpSpec) -> list[str]:
    """Generate a single operator method."""
    lines: list[str] = []
    param_list = ", ".join(f"{p.name}: {p.rust_type}" for p in spec.params)

    lines.append("    #[staticmethod]")
    lines.append(f"    pub fn {spec.py_name}({param_list}) -> Operator {{")

    if not spec.params:
        lines.append("        Operator {")
        lines.append(f"            kind: OperatorKind::{spec.variant_name},")
        lines.append("        }")
    else:
        param_init = ", ".join(f"{p.name}" for p in spec.params)
        lines.append("        Operator {")
        lines.append(f"            kind: OperatorKind::{spec.variant_name} {{ {param_init} }},")
        lines.append("        }")

    lines.append("    }")
    return lines


def _ns_to_class_name(ns: str) -> str:
    """Convert namespace to Rust class name (e.g., text -> OpText)."""
    return f"Op{ns.capitalize()}"


def _make_stub_signature(spec: OpSpec, indent: str = "") -> str:
    """Generate a Python stub method signature."""
    if spec.py_name == "map_py":
        return f"{indent}def map_py[T, U](func: Callable[[T], U]) -> Operator[T, U]: ..."
    if spec.py_name == "get_or":
        return f"{indent}def get_or[T](key: str, default: T) -> Operator[Mapping[str, T], T]: ..."
    param_list = ", ".join(f"{p.name}: {p.py_type}" for p in spec.params)
    ret_type = f"Operator[{spec.in_type}, {spec.out_type}]"
    return f"{indent}def {spec.py_name}({param_list}) -> {ret_type}: ..."


def _collect_ns_specs(specs: list[OpSpec]) -> tuple[dict[str, list[OpSpec]], list[OpSpec]]:
    """Group specs by namespace, including aliases."""
    ns_specs: dict[str, list[OpSpec]] = {}
    flat_specs: list[OpSpec] = []

    for spec in specs:
        if spec.ns:
            ns_specs.setdefault(spec.ns, []).append(spec)
            # Add to alias namespaces as well
            if spec.aliases:
                for alias_ns in spec.aliases:
                    ns_specs.setdefault(alias_ns, []).append(spec)
        else:
            flat_specs.append(spec)

    return ns_specs, flat_specs


def generate_rust_op(specs: list[OpSpec]) -> str:
    """Generate src/py/op_generated.rs content."""
    ns_specs, flat_specs = _collect_ns_specs(specs)

    lines: list[str] = [
        "// This file is auto-generated by tools/gen_ops.py",
        "// Do not edit manually!",
        "",
        "use crate::ops::OperatorKind;",
        "use crate::py::operator::Operator;",
        "use pyo3::prelude::*;",
        "",
    ]

    # Generate namespace classes (OpText, OpSeq, OpMap, etc.)
    for ns in sorted(ns_specs.keys()):
        ns_class = _ns_to_class_name(ns)
        lines.append(f"/// Namespace for {ns} operations")
        lines.append(f'#[pyclass(frozen, name = "{ns_class}")]')
        lines.append(f"pub struct {ns_class};")
        lines.append("")
        lines.append("#[pymethods]")
        lines.append(f"impl {ns_class} {{")

        ns_spec_list = ns_specs[ns]
        for i, spec in enumerate(ns_spec_list):
            lines.extend(_generate_operator_method(spec))
            if i < len(ns_spec_list) - 1:
                lines.append("")

        lines.append("}")
        lines.append("")

    # Generate main Op class
    lines.append("/// Static factory class for creating Operators")
    lines.append('#[pyclass(frozen, name = "Op")]')
    lines.append("pub struct Op;")
    lines.append("")
    lines.append("#[pymethods]")
    lines.append("impl Op {")

    # Add classattr for each namespace
    first_item = True
    for ns in sorted(ns_specs.keys()):
        if not first_item:
            lines.append("")
        first_item = False
        ns_class = _ns_to_class_name(ns)
        lines.append("    #[classattr]")
        lines.append(f"    fn {ns}() -> {ns_class} {{")
        lines.append(f"        {ns_class}")
        lines.append("    }")

    # Add flat methods (no namespace)
    for spec in flat_specs:
        lines.append("")
        lines.extend(_generate_operator_method(spec))

    # Add alias methods for backward compatibility (flat API)
    # Track added method names to avoid duplicates (aliases may appear in multiple ns)
    added_methods: set[str] = set()
    for ns in sorted(ns_specs.keys()):
        for spec in ns_specs[ns]:
            if spec.py_name in added_methods:
                continue  # Skip duplicates
            added_methods.add(spec.py_name)

            lines.append("")
            param_list = ", ".join(f"{p.name}: {p.rust_type}" for p in spec.params)
            param_call = ", ".join(f"{p.name}" for p in spec.params)
            # Use the original namespace (spec.ns), not the alias namespace
            ns_class = _ns_to_class_name(spec.ns) if spec.ns else ""

            lines.append("    /// Alias for backward compatibility")
            lines.append("    #[staticmethod]")
            lines.append(f"    pub fn {spec.py_name}({param_list}) -> Operator {{")
            lines.append(f"        {ns_class}::{spec.py_name}({param_call})")
            lines.append("    }")

    lines.append("}")

    return "\n".join(lines)


def generate_python_stub(specs: list[OpSpec]) -> str:
    """Generate the Op class stub content for __init__.pyi."""
    ns_specs, flat_specs = _collect_ns_specs(specs)

    lines: list[str] = []
    lines.append("# BEGIN GENERATED OP")

    # Add namespace class attributes
    for ns in sorted(ns_specs.keys()):
        ns_class = _ns_to_class_name(ns)
        lines.append(f"{ns}: {ns_class}")

    # Add flat methods (no namespace)
    for spec in flat_specs:
        lines.append("@staticmethod")
        lines.append(_make_stub_signature(spec))

    # Add alias methods for backward compatibility
    # Track added method names to avoid duplicates
    added_methods: set[str] = set()
    for ns in sorted(ns_specs.keys()):
        for spec in ns_specs[ns]:
            if spec.py_name in added_methods:
                continue  # Skip duplicates
            added_methods.add(spec.py_name)
            lines.append("@staticmethod")
            lines.append(_make_stub_signature(spec))

    lines.append("# END GENERATED OP")

    return "\n".join(lines)


def generate_ns_classes_stub(specs: list[OpSpec]) -> str:
    """Generate namespace class stubs (OpText, OpSeq, etc.) for __init__.pyi."""
    ns_specs, _ = _collect_ns_specs(specs)

    lines: list[str] = []
    lines.append("# BEGIN GENERATED NS")

    for ns in sorted(ns_specs.keys()):
        ns_class = _ns_to_class_name(ns)
        lines.append(f"class {ns_class}:")
        for spec in ns_specs[ns]:
            lines.append("    @staticmethod")
            lines.append(_make_stub_signature(spec, indent="    "))
        lines.append("")  # Two empty lines between classes (PEP 8)
        lines.append("")

    # Remove trailing empty lines
    while lines and lines[-1] == "":
        lines.pop()

    lines.append("# END GENERATED NS")

    return "\n".join(lines)


def _update_between_markers(content: str, begin: str, end: str, new_content: str) -> str:
    """Update content between markers, preserving indentation."""
    pattern = re.compile(
        rf"^(\s*)({re.escape(begin)}).*?({re.escape(end)})", re.MULTILINE | re.DOTALL
    )

    match = pattern.search(content)
    if not match:
        return content  # Markers not found, return unchanged

    # Get the indentation from the matched begin marker
    indent = match.group(1)

    # Apply the same indentation to all lines in new_content
    # For NS markers (no indent), don't add extra indentation
    indented_lines: list[str] = []
    for line in new_content.split("\n"):
        if line.strip():  # Non-empty line
            # Only add base indent if there's indentation in the original marker
            if indent and not line.startswith(" "):
                indented_lines.append(indent + line)
            else:
                indented_lines.append(line)
        else:
            indented_lines.append("")

    indented_content = "\n".join(indented_lines)

    return pattern.sub(indented_content, content)


def update_python_stub(pyi_path: Path, op_content: str, ns_content: str) -> None:
    """Update pyropust/__init__.pyi with new Op and namespace stub content."""
    content = pyi_path.read_text()

    # Update Op class content
    content = _update_between_markers(
        content, "# BEGIN GENERATED OP", "# END GENERATED OP", op_content
    )

    # Update namespace classes content
    content = _update_between_markers(
        content, "# BEGIN GENERATED NS", "# END GENERATED NS", ns_content
    )

    pyi_path.write_text(content)


def generate_mod_exports(specs: list[OpSpec]) -> str:
    """Generate py/mod.rs exports content."""
    ns_specs, _ = _collect_ns_specs(specs)
    namespaces = sorted(ns_specs.keys())
    ns_classes = ["Op"] + [_ns_to_class_name(ns) for ns in namespaces]
    exports = ", ".join(ns_classes)
    return (
        f"// BEGIN GENERATED EXPORTS\n"
        f"pub use op_generated::{{{exports}}};\n"
        f"// END GENERATED EXPORTS"
    )


def generate_lib_classes(specs: list[OpSpec]) -> str:
    """Generate lib.rs add_class content."""
    ns_specs, _ = _collect_ns_specs(specs)
    namespaces = sorted(ns_specs.keys())
    ns_classes = ["Op"] + [_ns_to_class_name(ns) for ns in namespaces]

    lines = ["    // BEGIN GENERATED CLASSES"]
    lines.extend(f"    m.add_class::<{cls}>()?;" for cls in ns_classes)
    lines.append("    // END GENERATED CLASSES")
    return "\n".join(lines)


def update_rust_file(path: Path, begin: str, end: str, new_content: str) -> None:
    """Update content between markers in a Rust file."""
    content = path.read_text()
    content = _update_between_markers(content, begin, end, new_content)
    path.write_text(content)


def main() -> None:
    """Run the operator code generator."""
    root = Path(__file__).parent.parent
    kind_rs = root / "src/ops/kind.rs"
    op_generated_rs = root / "src/py/op_generated.rs"
    mod_rs = root / "src/py/mod.rs"
    lib_rs = root / "src/lib.rs"
    pyi = root / "pyropust/__init__.pyi"

    print(f"📖 Parsing {kind_rs}...")
    specs = parse_kind_rs(kind_rs)
    print(f"   Found {len(specs)} operators")

    # Count by namespace
    ns_counts: dict[str, int] = {}
    flat_count = 0
    for spec in specs:
        if spec.ns:
            ns_counts[spec.ns] = ns_counts.get(spec.ns, 0) + 1
        else:
            flat_count += 1
    if ns_counts:
        ns_summary = ", ".join(f"{ns}={count}" for ns, count in sorted(ns_counts.items()))
        print(f"   Namespaces: {ns_summary}, flat={flat_count}")

    print(f"🦀 Generating {op_generated_rs}...")
    rust_code = generate_rust_op(specs)
    # Ensure trailing newline
    if not rust_code.endswith("\n"):
        rust_code += "\n"
    op_generated_rs.write_text(rust_code)

    print(f"🦀 Updating {mod_rs}...")
    mod_exports = generate_mod_exports(specs)
    update_rust_file(mod_rs, "// BEGIN GENERATED EXPORTS", "// END GENERATED EXPORTS", mod_exports)

    print(f"🦀 Updating {lib_rs}...")
    lib_classes = generate_lib_classes(specs)
    update_rust_file(lib_rs, "// BEGIN GENERATED CLASSES", "// END GENERATED CLASSES", lib_classes)

    print(f"🐍 Updating {pyi}...")
    op_stub_content = generate_python_stub(specs)
    ns_stub_content = generate_ns_classes_stub(specs)
    update_python_stub(pyi, op_stub_content, ns_stub_content)

    print("✅ Done!")


if __name__ == "__main__":
    main()
