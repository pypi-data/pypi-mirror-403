import argparse
import gzip
import hashlib
import json
import os
import sys
import tempfile
import multiprocessing as mp
from pathlib import Path

from tqdm import tqdm
from rdkit import Chem
from rdkit import rdBase
from rdkit.Chem import AllChem
from rdkit.Chem.Scaffolds import MurckoScaffold


_WORKER_CFG: dict | None = None


def sha1_hex(text: str) -> str:
    h = hashlib.sha1()
    h.update(text.encode("utf-8"))
    return h.hexdigest()


def ensure_dir(path: Path) -> None:
    if path.exists() is False:
        path.mkdir(parents=True, exist_ok=True)


def atomic_write_text(path: Path, data: str) -> None:
    ensure_dir(path.parent)
    fd = None
    tmp_path = None

    try:
        fd, tmp_path_str = tempfile.mkstemp(prefix=path.name + ".", dir=str(path.parent))
        tmp_path = Path(tmp_path_str)

        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            f.write(data)

        os.replace(str(tmp_path), str(path))
        tmp_path = None
    finally:
        if tmp_path is not None:
            try:
                tmp_path.unlink()
            except Exception:
                pass


def atomic_write_gzip_json(path: Path, obj: object) -> None:
    ensure_dir(path.parent)
    fd = None
    tmp_path = None

    try:
        fd, tmp_path_str = tempfile.mkstemp(prefix=path.name + ".", dir=str(path.parent))
        tmp_path = Path(tmp_path_str)

        with os.fdopen(fd, "wb") as raw:
            with gzip.GzipFile(fileobj=raw, mode="wb") as gz:
                payload = json.dumps(obj, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
                gz.write(payload)

        os.replace(str(tmp_path), str(path))
        tmp_path = None
    finally:
        if tmp_path is not None:
            try:
                tmp_path.unlink()
            except Exception:
                pass


def read_json(path: Path) -> object | None:
    try:
        with open(path, "r", encoding="utf-8") as f:
            obj = json.load(f)
        return obj
    except Exception:
        return None


def count_nonempty_lines(path: Path) -> int:
    n = 0
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            s = line.strip()
            if s != "":
                n += 1
    return n


def iter_smiles(path: Path):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            s = line.strip()
            if s == "":
                continue
            parts = s.split()
            if len(parts) == 0:
                continue
            yield parts[0]


def murcko_scaffold_smiles(mol: Chem.Mol) -> str:
    scaf = MurckoScaffold.GetScaffoldForMol(mol)
    if scaf is None:
        return "[NO_SCAFFOLD]"
    s = Chem.MolToSmiles(scaf, isomericSmiles=False)
    if s == "":
        return "[NO_SCAFFOLD]"
    return s


def set_embed_parameter(params: object, name: str, value: object) -> bool:
    try:
        getattr(params, name)
    except Exception:
        return False

    try:
        setattr(params, name, value)
        return True
    except Exception:
        return False


def configure_etkdg_params(seed: int, max_attempts: int, prune_rms: float | None):
    params = AllChem.ETKDGv3()

    set_embed_parameter(params, "randomSeed", int(seed))

    done = False
    if done is False:
        ok = set_embed_parameter(params, "maxAttempts", int(max_attempts))
        if ok is True:
            done = True

    if done is False:
        ok = set_embed_parameter(params, "maxIterations", int(max_attempts))
        if ok is True:
            done = True

    if done is False:
        ok = set_embed_parameter(params, "maxIters", int(max_attempts))
        if ok is True:
            done = True

    if prune_rms is not None:
        set_embed_parameter(params, "pruneRmsThresh", float(prune_rms))

    return params


def best_optimize_method(mol_h: Chem.Mol, prefer_mmff: bool) -> str:
    if prefer_mmff is True:
        props = AllChem.MMFFGetMoleculeProperties(mol_h, mmffVariant="MMFF94")
        if props is not None:
            return "MMFF"
    return "UFF"


def embed_and_optimize_conformers(
    mol: Chem.Mol,
    num_confs: int,
    seed: int,
    max_attempts: int,
    prefer_mmff: bool,
    prune_rms: float | None,
) -> dict:
    mol_h = Chem.AddHs(mol)

    params = configure_etkdg_params(seed=seed, max_attempts=max_attempts, prune_rms=prune_rms)
    conf_ids = AllChem.EmbedMultipleConfs(mol_h, numConfs=int(num_confs), params=params)

    conf_id_list = []
    for cid in conf_ids:
        conf_id_list.append(int(cid))

    method = best_optimize_method(mol_h, prefer_mmff)
    energies = []

    if len(conf_id_list) > 0:
        if method == "MMFF":
            props = AllChem.MMFFGetMoleculeProperties(mol_h, mmffVariant="MMFF94")
            if props is not None:
                results = AllChem.MMFFOptimizeMoleculeConfs(mol_h, numThreads=1, mmffVariant="MMFF94")
                for r in results:
                    status = int(r[0])
                    energy = float(r[1])
                    if status == 0 or status == 1:
                        energies.append(energy)
                    else:
                        energies.append(float("nan"))
            else:
                method = "UFF"

        if method == "UFF":
            results = AllChem.UFFOptimizeMoleculeConfs(mol_h, numThreads=1)
            for r in results:
                status = int(r[0])
                energy = float(r[1])
                if status == 0 or status == 1:
                    energies.append(energy)
                else:
                    energies.append(float("nan"))

    atoms = []
    for atom in mol_h.GetAtoms():
        atoms.append(atom.GetSymbol())

    conformers = []
    i = 0
    while i < mol_h.GetNumConformers():
        conf = mol_h.GetConformer(i)
        coords = []
        aidx = 0
        while aidx < mol_h.GetNumAtoms():
            p = conf.GetAtomPosition(aidx)
            coords.append([float(p.x), float(p.y), float(p.z)])
            aidx += 1
        conformers.append(coords)
        i += 1

    payload = {
        "atoms": atoms,
        "conformers": conformers,
        "energies": energies,
        "method": method,
    }
    return payload


def cache_paths(cache_dir: Path, canonical_smiles: str) -> tuple[Path, Path]:
    h = sha1_hex(canonical_smiles)
    pfx = h[0:2]
    meta_path = cache_dir / "molecules" / pfx / (h + ".json")
    conf_path = cache_dir / "conformers" / pfx / (h + ".json.gz")
    return meta_path, conf_path


def worker_init(cfg: dict) -> None:
    global _WORKER_CFG
    _WORKER_CFG = cfg
    rdBase.DisableLog("rdApp.error")
    rdBase.DisableLog("rdApp.warning")


def process_one_smiles(raw_smiles: str) -> dict:
    cfg = _WORKER_CFG
    if cfg is None:
        return {"status": "error", "reason": "worker not initialized"}

    cache_dir = Path(cfg["cache_dir"])
    num_confs = int(cfg["num_confs"])
    max_attempts = int(cfg["max_attempts"])
    prefer_mmff = bool(cfg["prefer_mmff"])
    prune_rms = cfg["prune_rms"]
    rdkit_version = str(cfg["rdkit_version"])
    cache_version = int(cfg["cache_version"])

    mol = Chem.MolFromSmiles(raw_smiles)
    if mol is None:
        return {"status": "invalid"}

    canonical = Chem.MolToSmiles(mol, isomericSmiles=True)
    meta_path, conf_path = cache_paths(cache_dir, canonical)

    meta = None
    if meta_path.exists() is True:
        meta_obj = read_json(meta_path)
        if isinstance(meta_obj, dict) is True:
            meta = meta_obj

    if meta is not None:
        ok = True

        if int(meta.get("cache_version", -1)) != cache_version:
            ok = False
        if str(meta.get("rdkit_version", "")) != rdkit_version:
            ok = False
        if int(meta.get("num_confs", -1)) != num_confs:
            ok = False
        if int(meta.get("max_attempts", -1)) != max_attempts:
            ok = False
        if bool(meta.get("prefer_mmff", False)) != prefer_mmff:
            ok = False
        if meta.get("prune_rms", None) != prune_rms:
            ok = False
        if str(meta.get("canonical_smiles", "")) != canonical:
            ok = False
        if str(meta.get("status", "")) != "ok":
            ok = False
        if conf_path.exists() is False:
            ok = False

        if ok is True:
            scaf = str(meta.get("scaffold_smiles", "[NO_SCAFFOLD]"))
            return {"status": "ok", "canonical": canonical, "scaffold": scaf}

    scaf = murcko_scaffold_smiles(mol)

    seed_hex = sha1_hex(canonical)[0:8]
    seed_int = int(seed_hex, 16) & 0x7FFFFFFF

    conf_payload = embed_and_optimize_conformers(
        mol=mol,
        num_confs=num_confs,
        seed=seed_int,
        max_attempts=max_attempts,
        prefer_mmff=prefer_mmff,
        prune_rms=prune_rms,
    )

    atomic_write_gzip_json(conf_path, conf_payload)

    new_meta = {
        "cache_version": cache_version,
        "rdkit_version": rdkit_version,
        "status": "ok",
        "canonical_smiles": canonical,
        "scaffold_smiles": scaf,
        "num_confs": num_confs,
        "max_attempts": max_attempts,
        "prefer_mmff": prefer_mmff,
        "prune_rms": prune_rms,
        "conformers_path": str(conf_path.relative_to(cache_dir)),
    }

    atomic_write_text(meta_path, json.dumps(new_meta, ensure_ascii=False, separators=(",", ":")))
    return {"status": "ok", "canonical": canonical, "scaffold": scaf}


def write_pairs_stream(pairs_path: Path, results_iter, total: int) -> tuple[int, int]:
    valid = 0
    invalid = 0

    ensure_dir(pairs_path.parent)
    with open(pairs_path, "w", encoding="utf-8", newline="\n") as out:
        with tqdm(total=total, unit="smiles", mininterval=0.2, dynamic_ncols=True, desc="Processing") as bar:
            for r in results_iter:
                bar.update(1)

                if isinstance(r, dict) is False:
                    invalid += 1
                    continue

                if r.get("status") != "ok":
                    invalid += 1
                    continue

                scaf = r.get("scaffold")
                can = r.get("canonical")

                if isinstance(scaf, str) is False:
                    invalid += 1
                    continue

                if isinstance(can, str) is False:
                    invalid += 1
                    continue

                out.write(scaf)
                out.write("\t")
                out.write(can)
                out.write("\n")
                valid += 1

    return valid, invalid


def sort_chunks(pairs_path: Path, tmp_dir: Path, chunk_lines: int, total_lines: int) -> list[Path]:
    chunk_paths: list[Path] = []
    buf: list[tuple[str, str]] = []
    chunk_idx = 0

    with open(pairs_path, "r", encoding="utf-8", errors="replace") as f:
        with tqdm(total=total_lines, unit="pair", mininterval=0.2, dynamic_ncols=True, desc="Chunk sorting") as bar:
            for line in f:
                bar.update(1)
                s = line.rstrip("\n")
                if s == "":
                    continue

                parts = s.split("\t")
                if len(parts) != 2:
                    continue

                scaf = parts[0]
                can = parts[1]
                buf.append((scaf, can))

                if len(buf) >= chunk_lines:
                    buf.sort()
                    chunk_path = tmp_dir / ("chunk_" + str(chunk_idx) + ".tsv")

                    with open(chunk_path, "w", encoding="utf-8", newline="\n") as out:
                        i = 0
                        while i < len(buf):
                            out.write(buf[i][0])
                            out.write("\t")
                            out.write(buf[i][1])
                            out.write("\n")
                            i += 1

                    chunk_paths.append(chunk_path)
                    buf = []
                    chunk_idx += 1

    if len(buf) > 0:
        buf.sort()
        chunk_path = tmp_dir / ("chunk_" + str(chunk_idx) + ".tsv")

        with open(chunk_path, "w", encoding="utf-8", newline="\n") as out:
            i = 0
            while i < len(buf):
                out.write(buf[i][0])
                out.write("\t")
                out.write(buf[i][1])
                out.write("\n")
                i += 1

        chunk_paths.append(chunk_path)

    return chunk_paths


def read_pair_line(f) -> tuple[str, str] | None:
    line = f.readline()
    if line == "":
        return None

    s = line.rstrip("\n")
    if s == "":
        return None

    parts = s.split("\t")
    if len(parts) != 2:
        return None

    return parts[0], parts[1]


def merge_files(in_paths: list[Path], out_path: Path) -> None:
    import heapq

    files = []
    heap = []

    ensure_dir(out_path.parent)

    i = 0
    while i < len(in_paths):
        p = in_paths[i]
        f = open(p, "r", encoding="utf-8", errors="replace")
        files.append(f)

        pair = read_pair_line(f)
        if pair is not None:
            heapq.heappush(heap, (pair[0], pair[1], i))
        i += 1

    with open(out_path, "w", encoding="utf-8", newline="\n") as out:
        while len(heap) > 0:
            scaf, can, idx = heapq.heappop(heap)

            out.write(scaf)
            out.write("\t")
            out.write(can)
            out.write("\n")

            nxt = read_pair_line(files[idx])
            if nxt is not None:
                heapq.heappush(heap, (nxt[0], nxt[1], idx))

    i = 0
    while i < len(files):
        try:
            files[i].close()
        except Exception:
            pass
        i += 1


def merge_many(chunk_paths: list[Path], tmp_dir: Path, max_open: int) -> Path:
    stage = 0
    current = chunk_paths

    if len(current) == 0:
        merged = tmp_dir / "pairs.sorted.tsv"
        with open(merged, "w", encoding="utf-8", newline="\n") as out:
            out.write("")
        return merged

    while len(current) > 1:
        next_round: list[Path] = []
        i = 0

        while i < len(current):
            group = current[i:i + max_open]
            out_path = tmp_dir / ("merge_s" + str(stage) + "_b" + str(len(next_round)) + ".tsv")

            if len(group) == 1:
                os.replace(str(group[0]), str(out_path))
            else:
                merge_files(group, out_path)

                j = 0
                while j < len(group):
                    try:
                        group[j].unlink()
                    except Exception:
                        pass
                    j += 1

            next_round.append(out_path)
            i += max_open

        current = next_round
        stage += 1

    return current[0]


def write_grouped_json(sorted_pairs_path: Path, out_json_path: Path, total_pairs: int) -> int:
    group_id = 0
    current_scaffold: str | None = None
    first_group = True
    first_item = True
    last_smiles: str | None = None

    ensure_dir(out_json_path.parent)

    with open(sorted_pairs_path, "r", encoding="utf-8", errors="replace") as f:
        with open(out_json_path, "w", encoding="utf-8", newline="\n") as out:
            out.write("{\n")

            with tqdm(total=total_pairs, unit="pair", mininterval=0.2, dynamic_ncols=True, desc="Writing groups") as bar:
                for line in f:
                    bar.update(1)
                    s = line.rstrip("\n")
                    if s == "":
                        continue

                    parts = s.split("\t")
                    if len(parts) != 2:
                        continue

                    scaf = parts[0]
                    can = parts[1]

                    if current_scaffold is None:
                        current_scaffold = scaf
                        group_id += 1

                        if first_group is False:
                            out.write(",\n")

                        out.write('  "')
                        out.write(str(group_id))
                        out.write('": [')

                        first_group = False
                        first_item = True
                        last_smiles = None

                    if scaf != current_scaffold:
                        out.write("]\n")

                        current_scaffold = scaf
                        group_id += 1

                        out.write(",\n")
                        out.write('  "')
                        out.write(str(group_id))
                        out.write('": [')

                        first_item = True
                        last_smiles = None

                    if last_smiles is not None:
                        if can == last_smiles:
                            continue

                    if first_item is True:
                        out.write("\n    ")
                        out.write(json.dumps(can, ensure_ascii=False))
                        first_item = False
                    else:
                        out.write(",\n    ")
                        out.write(json.dumps(can, ensure_ascii=False))

                    last_smiles = can

            if current_scaffold is not None:
                out.write("\n  ]\n")

            out.write("}\n")

    return group_id


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Input text file (one SMILES per line; extra columns ignored)")
    parser.add_argument("--output", required=True, help="Output JSON: {\"1\": [...], \"2\": [...], ...}")
    parser.add_argument("--cache-dir", default=".cache_bm", help="Cache directory for metadata and conformers")
    parser.add_argument("--tmp-dir", default=None, help="Temp directory for external sort files (optional)")
    parser.add_argument("--num-confs", type=int, default=20, help="Number of 3D conformers per molecule")
    parser.add_argument("--max-attempts", type=int, default=20, help="Max ETKDG attempts/iterations (version-dependent)")
    parser.add_argument("--prefer-mmff", action="store_true", help="Prefer MMFF optimization when available; otherwise UFF")
    parser.add_argument("--prune-rms", type=float, default=None, help="Prune conformers closer than this RMS threshold (Å)")
    parser.add_argument("--chunk-lines", type=int, default=300000, help="Lines per chunk for external sorting")
    parser.add_argument("--max-open", type=int, default=64, help="Max open files during merge")
    parser.add_argument("--nprocs", type=int, default=0, help="Worker processes (0 = all available cores)")
    parser.add_argument("--start-method", default="auto", choices=["auto", "fork", "spawn"], help="multiprocessing start method")
    parser.add_argument("--keep-temp", action="store_true", help="Keep temporary files (debugging)")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    cache_dir = Path(args.cache_dir)

    if input_path.exists() is False:
        sys.stderr.write("Input file not found: " + str(input_path) + "\n")
        sys.exit(2)

    if args.tmp_dir is None:
        tmp_dir = Path(tempfile.mkdtemp(prefix="bm_tmp_"))
    else:
        tmp_dir = Path(args.tmp_dir)
        ensure_dir(tmp_dir)

    ensure_dir(cache_dir)

    total_smiles = count_nonempty_lines(input_path)

    nprocs = int(args.nprocs)
    if nprocs <= 0:
        cpu = os.cpu_count()
        if cpu is None:
            cpu = 1
        nprocs = int(cpu)

    methods = mp.get_all_start_methods()
    chosen_method = None

    if args.start_method == "auto":
        if "fork" in methods:
            chosen_method = "fork"
        else:
            chosen_method = "spawn"
    else:
        chosen_method = args.start_method

    ctx = mp.get_context(chosen_method)

    cfg = {
        "cache_dir": str(cache_dir),
        "num_confs": int(args.num_confs),
        "max_attempts": int(args.max_attempts),
        "prefer_mmff": bool(args.prefer_mmff),
        "prune_rms": args.prune_rms,
        "rdkit_version": str(rdBase.rdkitVersion),
        "cache_version": 2,
    }

    pairs_path = tmp_dir / "pairs.tsv"

    with ctx.Pool(processes=nprocs, initializer=worker_init, initargs=(cfg,)) as pool:
        smiles_it = iter_smiles(input_path)
        results_it = pool.imap_unordered(process_one_smiles, smiles_it, chunksize=200)
        valid_pairs, invalid_smiles = write_pairs_stream(pairs_path, results_it, total_smiles)

    if valid_pairs == 0:
        atomic_write_text(output_path, "{}\n")
        sys.stderr.write("No valid SMILES were found.\n")
        sys.stderr.write("Cache directory: " + str(cache_dir) + "\n")
        return

    chunk_paths = sort_chunks(pairs_path, tmp_dir, int(args.chunk_lines), valid_pairs)

    try:
        pairs_path.unlink()
    except Exception:
        pass

    sorted_pairs_path = merge_many(chunk_paths, tmp_dir, int(args.max_open))
    scaffolds_written = write_grouped_json(sorted_pairs_path, output_path, valid_pairs)

    if args.keep_temp is False:
        try:
            sorted_pairs_path.unlink()
        except Exception:
            pass

        try:
            tmp_dir.rmdir()
        except Exception:
            pass

    sys.stderr.write("Total non-empty input lines: " + str(total_smiles) + "\n")
    sys.stderr.write("Valid SMILES processed: " + str(valid_pairs) + "\n")
    sys.stderr.write("Invalid SMILES skipped: " + str(invalid_smiles) + "\n")
    sys.stderr.write("Unique scaffolds written: " + str(scaffolds_written) + "\n")
    sys.stderr.write("Output JSON: " + str(output_path) + "\n")
    sys.stderr.write("Cache directory: " + str(cache_dir) + "\n")


if __name__ == "__main__":
    main()
