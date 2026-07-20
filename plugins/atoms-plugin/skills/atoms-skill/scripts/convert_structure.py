#!/usr/bin/env python3
"""Convert atomistic structures with ASE."""

from __future__ import annotations

import argparse
import glob
import math
import re
import textwrap
from pathlib import Path
from typing import Sequence

from ase import Atoms
from ase.io import read, write
from ase.units import Bohr

ABACUS_ION_RE = re.compile(r"STRU_ION(\d+)_D$")


def read_abacus_stru(path: Path) -> Atoms:
    lines = path.read_text(errors="ignore").splitlines()

    def line_index(keyword: str) -> int:
        for i, line in enumerate(lines):
            if line.strip().upper() == keyword:
                return i
        raise ValueError(f"{path}: missing {keyword}")

    def floats(line: str, n: int = 3) -> list[float]:
        values: list[float] = []
        for token in line.split("#", 1)[0].split():
            try:
                values.append(float(token))
            except ValueError:
                pass
            if len(values) == n:
                break
        return values

    lattice_factor = 1.0
    try:
        for line in lines[line_index("LATTICE_CONSTANT") + 1 :]:
            clean = line.split("#", 1)[0].strip()
            if clean:
                lattice_factor = float(clean.split()[0]) * Bohr
                break
    except ValueError:
        pass

    lattice_start = line_index("LATTICE_VECTORS") + 1
    cell = []
    for line in lines[lattice_start : lattice_start + 3]:
        vector = floats(line)
        if len(vector) != 3:
            raise ValueError(f"{path}: bad lattice vector: {line}")
        cell.append([x * lattice_factor for x in vector])

    i = line_index("ATOMIC_POSITIONS") + 1
    while i < len(lines) and not lines[i].strip():
        i += 1
    coord_mode = lines[i].strip().lower()
    i += 1

    symbols: list[str] = []
    positions: list[list[float]] = []
    while i < len(lines):
        while i < len(lines) and not lines[i].strip():
            i += 1
        if i >= len(lines):
            break

        symbol = lines[i].split()[0]
        i += 1

        while i < len(lines) and not lines[i].strip():
            i += 1
        i += 1  # magnetism line

        while i < len(lines) and not lines[i].strip():
            i += 1
        if i >= len(lines):
            break
        count = int(float(lines[i].split()[0]))
        i += 1

        for _ in range(count):
            while i < len(lines) and not lines[i].strip():
                i += 1
            xyz = floats(lines[i])
            i += 1
            if len(xyz) != 3:
                raise ValueError(f"{path}: bad coordinate line: {lines[i - 1]}")
            symbols.append(symbol)
            positions.append(xyz)

    if not symbols:
        raise ValueError(f"{path}: no atoms parsed")

    atoms = Atoms(symbols=symbols, cell=cell, pbc=True)
    if coord_mode.startswith("direct"):
        atoms.set_scaled_positions(positions)
    elif "bohr" in coord_mode:
        atoms.set_positions([[x * Bohr, y * Bohr, z * Bohr] for x, y, z in positions])
    else:
        atoms.set_positions(positions)
    atoms.info["source"] = path.name
    return atoms


def expand_paths(patterns: Sequence[str], *, abacus: bool) -> list[Path]:
    paths: list[Path] = []
    for pattern in patterns:
        matches = glob.glob(pattern) if any(c in pattern for c in "*?[") else [pattern]
        if not matches:
            raise FileNotFoundError(pattern)
        paths.extend(Path(match) for match in matches)

    def sort_key(path: Path) -> tuple[float, str]:
        match = ABACUS_ION_RE.search(path.name)
        return (float(match.group(1)), path.name) if match else (math.inf, str(path))

    paths.sort(key=sort_key if abacus else lambda path: str(path))
    return paths


def main(argv: Sequence[str] | None = None) -> int:
    argv = list(argv) if argv is not None else None
    raw_args = list(argv) if argv is not None else None
    if raw_args is None:
        import sys

        raw_args = sys.argv[1:]

    cell_values = None
    if "--cell" in raw_args:
        index = raw_args.index("--cell")
        cell_values = []
        end = index + 1
        while end < len(raw_args):
            try:
                cell_values.append(float(raw_args[end]))
            except ValueError:
                break
            end += 1
        if len(cell_values) not in (3, 9):
            raise SystemExit("--cell requires either 3 values (x y z) or 9 values (xx xy xz yx yy yz zx zy zz)")
        raw_args = raw_args[:index] + raw_args[end:]

    examples = """
Examples:
  uv run --with ase python convert_structure.py CONTCAR final.xyz --input-format vasp
  uv run --with ase python convert_structure.py "OUT.3/STRU_ION*_D" relax.xyz --input-format abacus --frames ":" --cell 26.8965 23.2147 36.1550
"""
    parser = argparse.ArgumentParser(
        description="Convert atomistic structures with ASE. Inputs can be files or glob patterns; the last path is output.",
        epilog=textwrap.dedent(examples),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("paths", nargs="+", metavar="PATH", help="Input file/glob pattern(s), followed by output path.")
    parser.add_argument("--input-format", default="auto", help="ASE input format, or 'abacus' for ABACUS STRU.")
    parser.add_argument("--output-format", default=None, help="ASE output format. Defaults to extxyz for .xyz.")
    parser.add_argument("--frames", default="-1", help="Frame selector, e.g. '-1', ':', '0:10:2'. Default: -1.")
    parser.add_argument("--cell", metavar="N", help="Cell override: 3 values (x y z) or 9 values (3x3 matrix).")
    args = parser.parse_args(raw_args)

    if len(args.paths) < 2:
        parser.error("provide at least one input and one output: INPUT [INPUT ...] OUTPUT")
    inputs, output = args.paths[:-1], args.paths[-1]

    atoms_list: list[Atoms] = []
    if args.input_format == "abacus":
        for path in expand_paths(inputs, abacus=True):
            atoms = read_abacus_stru(path)
            if match := ABACUS_ION_RE.search(path.name):
                atoms.info["ion_step"] = int(match.group(1))
            atoms_list.append(atoms)

        selector = int(args.frames) if ":" not in args.frames else slice(*[int(x) if x else None for x in (args.frames.split(":") + ["", ""])[:3]])
        selected = atoms_list[selector]
        atoms_list = selected if isinstance(selected, list) else [selected]
    else:
        fmt = None if args.input_format == "auto" else args.input_format
        for path in expand_paths(inputs, abacus=False):
            atoms = read(str(path), index=args.frames, format=fmt)
            atoms_list.extend(atoms if isinstance(atoms, list) else [atoms])

    if cell_values is not None:
        cell = cell_values if len(cell_values) == 3 else [cell_values[0:3], cell_values[3:6], cell_values[6:9]]
        for atoms in atoms_list:
            atoms.set_cell(cell)
            atoms.pbc = True

    output_format = args.output_format or ("extxyz" if Path(output).suffix.lower() == ".xyz" else None)
    write(output, atoms_list, format=output_format)
    print(f"wrote {output}")
    print(f"inputs={len(inputs)}")
    print(f"frames={len(atoms_list)}")
    print(f"atoms_per_last_frame={len(atoms_list[-1])}")
    print(f"output_format={output_format or 'auto'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
