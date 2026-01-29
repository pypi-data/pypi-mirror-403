## bm-group

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![tqdm](https://img.shields.io/badge/dependency-tqdm-orange.svg)](https://tqdm.github.io/)
[![RDKit](https://img.shields.io/badge/dependency-RDKit-blue.svg)](https://www.rdkit.org/)

CLI tool to group SMILES by Bemis–Murcko scaffold, with deterministic 3D conformer generation and on-disk caching (RDKit-based).

Summary
-------
Given an input text file containing one SMILES per line (extra columns are ignored), `bm_group.py`:

1. parses and canonicalizes each SMILES (isomeric SMILES),
2. computes its Bemis–Murcko scaffold,
3. (optionally) generates multiple 3D conformers (ETKDG v3) and optimizes them (MMFF if requested and available; otherwise UFF),
4. writes a JSON that groups canonical SMILES by scaffold.

To scale to large datasets, grouping is implemented via an external sort: it streams `scaffold<TAB>canonical_smiles` pairs to a temporary file, sorts them in chunks, merges the sorted chunks, then writes groups.

Features
--------
- **Scaffold grouping** via RDKit Murcko scaffolds.
- **Deterministic 3D cache** keyed by canonical SMILES hash (conformers + energies stored).
- **External sort** (chunk sort + k-way merge) for large inputs.
- **Multiprocessing** (configurable start method and worker count).
- **Atomic writes** for cache entries to reduce corruption risk.

Requirements
------------
- Python ≥ 3.10
- RDKit (tested with modern RDKit builds)
- tqdm

Installation
------------
This project is a single script. Create an environment with RDKit, then run it.

Conda (recommended)
```
conda create -n bm-group -c conda-forge python=3.11 rdkit tqdm
conda activate bm-group
```

pip 
```
pip install tqdm rdkit-pypi bm-group
```

Quick start
-----------
Input file (one SMILES per line; other columns are ignored):
```
CC[C@H](F)C(=O)O   some_id_1
c1ccccc1           benzene
```

Run:
```
python bm_group.py --input example_set.smiles --output example_set.json
```

With a custom cache dir and fewer workers:
```
python bm_group.py --input example_set.smiles --output example_set.json --cache-dir .cache_bm --nprocs 4
```

Prefer MMFF when available (otherwise fallback to UFF):
```
python bm_group.py --input example_set.smiles --output example_set.json --prefer-mmff
```

CLI
---
```
python bm_group.py --input INPUT --output OUTPUT [options]
```

Arguments
- `--input` (required): input text file (one SMILES per line; extra columns ignored).
- `--output` (required): output JSON path.

Options
- `--cache-dir`: cache directory for metadata and conformers (default: `.cache_bm`).
- `--tmp-dir`: temp directory for external sort files (default: auto-created).
- `--num-confs`: number of 3D conformers per molecule (default: `20`).
- `--max-attempts`: ETKDG attempts/iterations (RDKit-version dependent) (default: `20`).
- `--prefer-mmff`: if set, use MMFF optimization when possible; otherwise UFF.
- `--prune-rms`: prune conformers closer than this RMS threshold in Å (default: none).
- `--chunk-lines`: lines per chunk for external sorting (default: `300000`).
- `--max-open`: maximum open files during merge (default: `64`).
- `--nprocs`: number of worker processes (`0` = all available cores) (default: `0`).
- `--start-method`: multiprocessing start method: `auto`, `fork`, `spawn` (default: `auto`).
- `--keep-temp`: keep temporary sort/merge files (useful for debugging).

Output format
-------------
The output is a JSON object:

- keys are **stringified incremental group IDs** (`"1"`, `"2"`, ...),
- each value is a list of **canonical isomeric SMILES** belonging to the same scaffold group.

Example:
```
{
  "1": [
    "c1ccccc1"
  ],
  "2": [
    "CC[C@H](F)C(=O)O",
    "CCC(F)C(=O)O"
  ]
}
```

Notes:
- Group IDs are assigned in the **lexicographic order of scaffold SMILES** (because pairs are sorted by scaffold).
- Within each group, molecules are written in sorted order; exact duplicates are skipped during writing.

Cache
-----
`--cache-dir` stores two things per canonical SMILES (keyed by SHA1 hash):

- `molecules/<pfx>/<hash>.json` — metadata:
  - `cache_version`, `rdkit_version`, `canonical_smiles`, `scaffold_smiles`,
  - `num_confs`, `max_attempts`, `prefer_mmff`, `prune_rms`,
  - `conformers_path` (relative path to the gzipped payload)
- `conformers/<pfx>/<hash>.json.gz` — gzipped JSON:
  - `atoms`: list of atomic symbols (with explicit H),
  - `conformers`: list of conformers, each as `[[x,y,z], ...]`,
  - `energies`: per-conformer energies (NaN if optimization failed),
  - `method`: `"MMFF"` or `"UFF"`.

The cache is automatically reused only when the stored parameters match the current run (RDKit version and key settings).

How it works
------------
1. **Read** non-empty lines, take the first token as SMILES.
2. **Canonicalize** with RDKit (`isomericSmiles=True`).
3. **Compute scaffold** (RDKit Murcko scaffold).
4. **3D embedding + optimization** (optional but enabled by default because conformers are generated for the cache):
   - seed derived from canonical SMILES SHA1 (deterministic),
   - ETKDG v3 embedding,
   - MMFF (if `--prefer-mmff` and parameters available) or UFF.
5. **Stream pairs** `scaffold<TAB>canonical` to a temp file.
6. **External sort**: sort in chunks, then k-way merge.
7. **Write groups** as JSON.

Troubleshooting
---------------
Windows / multiprocessing:
- On Windows, the start method is typically `spawn`. If you hit multiprocessing or RDKit-related worker issues, try:
  - `--nprocs 1` (single process), or
  - explicitly `--start-method spawn`.

No valid SMILES:
- If every line is invalid, the script writes `{}` and prints a message on stderr.

License
-------
Released under the MIT License. See LICENSE.
