---
name: atoms-skill
description: Use ASE for atomistic and molecular simulation structure handling, including converting, slicing, and inspecting CIF, POSCAR/CONTCAR, VASP outputs, extxyz/xyz trajectories, LAMMPS-style structures where ASE supports them, and ABACUS STRU or STRU_ION*_D files. Use when the user asks to convert structures, extract selected frames, build trajectories from glob patterns, inspect atom counts, or normalize coordinate formats. Prefer running scripts through uv with ASE installed.
---

# Atoms Skill

Use this skill for atomistic and molecular simulation structure conversion, frame selection, and light inspection. ASE is required for conversion code.

## Default Workflow

1. Read the target file or directory before writing outputs.
2. Confirm the Python environment before conversion. Prefer Python 3.10. Verify `ase`, `numpy`, `pymatgen`, and `matplotlib` can import.
3. If the environment is missing or unsuitable, ask the user for an environment entry point instead of installing into an unknown system environment. Accept examples such as `module load ...`, `conda activate ...`, a venv path, or a project command such as `uv run --python 3.10 --with ...`.
4. Use `scripts/convert_structure.py` from the confirmed environment.
5. Preserve existing outputs unless the user explicitly asks to overwrite them; otherwise write a clearly named new file.
6. After conversion, verify atom count, frame count, cell/PBC metadata, and the first/last few lines of the output.
7. Report the exact output path and whether the structure is a final frame or trajectory.

## Environment Check

Run this before conversion:

```bash
python --version
python - <<'PY'
import ase, numpy, pymatgen, matplotlib
print("ase", ase.__version__)
print("numpy", numpy.__version__)
print("pymatgen", getattr(pymatgen, "__version__", "unknown"))
print("matplotlib", matplotlib.__version__)
PY
```

If no suitable environment is active, do not try to build heavy scientific packages on HPC login nodes by default. Ask the user to provide an environment entry point or permission to create one.

## Recommended Commands

Generic ASE-supported conversion. Inputs may be files or glob patterns; the final positional argument is always the output path. Default frame selection is the last frame, `--frames "-1"`.

```bash
python scripts/convert_structure.py input.cif output.xyz
python scripts/convert_structure.py CONTCAR final.xyz --input-format vasp
python scripts/convert_structure.py "relax_*.traj" selected.xyz --frames "0:20:2"
python scripts/convert_structure.py part1.xyz part2.xyz merged.xyz --frames ":"
python scripts/convert_structure.py input.xyz output.xyz --cell 20 20 30
```

Select frames from an ASE-readable trajectory:

```bash
python scripts/convert_structure.py relax_trajectory.xyz final.xyz
python scripts/convert_structure.py relax_trajectory.xyz all.xyz --frames ":"
python scripts/convert_structure.py relax_trajectory.xyz every_5.xyz --frames "::5"
```

Convert a single ABACUS `STRU` or `STRU_ION*_D` file to xyz:

```bash
python scripts/convert_structure.py OUT.3/STRU_ION92_D final_ion92.xyz --input-format abacus
```

Convert numbered ABACUS relaxation structures into an xyz trajectory:

```bash
python scripts/convert_structure.py "OUT.3/STRU_ION*_D" relax_trajectory.xyz --input-format abacus --frames ":"
```

## Frame Selection

- `--frames "-1"` writes the last frame and is the default.
- `--frames ":"` writes all frames.
- `--frames "a:b:c"` uses Python/ASE slice semantics, such as `0:10:2`.
- The command accepts any number of input paths or glob patterns; the last positional argument is the output.
- Glob inputs are expanded and sorted before reading. For normal ASE formats, sorting is lexicographic. For ABACUS `STRU_ION<N>_D`, sorting uses the integer `N`.
- When writing to a `.xyz` filename, the script defaults to ASE `extxyz` format so cell, PBC, and metadata are preserved while keeping the `.xyz` extension.
- Use `--cell x y z` to set an orthorhombic cell, or `--cell xx xy xz yx yy yz zx zy zz` to set a full 3x3 cell. This overrides the cell on every selected output frame and enables PBC.

## ABACUS Notes

- ABACUS parsing is implemented locally, then represented as ASE `Atoms` and written via ASE.
- `Direct` coordinates are converted through the cell; output xyz coordinates are Angstrom.
- If `LATTICE_CONSTANT` is present, ABACUS lattice vectors are treated as Bohr-scaled and converted to Angstrom before constructing ASE `Atoms`.
- ABACUS support is a convenience layer; this skill should still be treated as a general ASE-based structure workflow, not an ABACUS-specific workflow.
