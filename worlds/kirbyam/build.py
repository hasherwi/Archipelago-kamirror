#!/usr/bin/env python3
"""
build_kirbyam_apworld.py

1) Runs the Kirby AM payload patch build (calls patch_rom.py) to generate base_patch.bsdiff4
2) Packages worlds/kirbyam into kirbyam.apworld
3) Installs it to Archipelago custom_worlds
4) Injects APContainer manifest fields (version/compatible_version) required for packaged .apworlds

Assumptions from your repo layout:
- This build script is located at:   repo_root/worlds/kirbyam/build_kirbyam_apworld.py
- patch_rom.py is located at:        repo_root/worlds/kirbyam/kirby_ap_payload/patch_rom.py
- clean ROM filename:               kirby.gba (in kirby_ap_payload/)
- base_patch output should be in:    repo_root/worlds/kirbyam/data/base_patch.bsdiff4
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Any


DEFAULT_WORLD_NAME = "kirbyam"  # must be lowercase
DEFAULT_APCONTAINER_VERSION = 7
DEFAULT_INSTALL_DIR_WINDOWS = r"C:\ProgramData\Archipelago\custom_worlds"


def rm_tree(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def copy_world(src: Path, dst: Path) -> None:
    """Copy contents of src directory into dst directory (like Copy-Item worlds\\name\\* dst)."""
    ensure_dir(dst)
    for item in src.iterdir():
        target = dst / item.name
        if item.is_dir():
            shutil.copytree(item, target, dirs_exist_ok=True)
        else:
            shutil.copy2(item, target)


def remove_junk(root: Path) -> None:
    """Remove __pycache__ directories and *.pyc files recursively."""
    for d in root.rglob("__pycache__"):
        if d.is_dir():
            shutil.rmtree(d, ignore_errors=True)
    for f in root.rglob("*.pyc"):
        if f.is_file():
            try:
                f.unlink()
            except OSError:
                pass


def load_json(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError as e:
        raise SystemExit(
            f"Missing manifest: {path}\n"
            f"Create worlds/{path.parent.name}/archipelago.json first."
        ) from e
    except json.JSONDecodeError as e:
        raise SystemExit(f"Invalid JSON in manifest: {path}\n{e}") from e


def write_pretty_json(path: Path, obj: dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
        f.write("\n")


def inject_apcontainer_fields(manifest_path: Path, apcontainer_version: int) -> None:
    manifest = load_json(manifest_path)
    if "version" not in manifest:
        manifest["version"] = apcontainer_version
    if "compatible_version" not in manifest:
        manifest["compatible_version"] = apcontainer_version
    write_pretty_json(manifest_path, manifest)


def zip_folder_with_top_level(folder_to_zip: Path, zip_path: Path) -> None:
    """
    Create a zip where the root entry is the folder name itself.
    Example: zipping build_apworld/kirbyam produces entries kirbyam/...
    """
    if zip_path.exists():
        zip_path.unlink()

    top_name = folder_to_zip.name

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for dirpath, dirnames, filenames in os.walk(folder_to_zip):
            dir_path = Path(dirpath)
            rel_dir = dir_path.relative_to(folder_to_zip)
            arc_dir = str(Path(top_name) / rel_dir).replace("\\", "/")

            if not filenames and not dirnames:
                zf.writestr(arc_dir.rstrip("/") + "/", "")

            for filename in filenames:
                file_path = dir_path / filename
                rel_file = file_path.relative_to(folder_to_zip)
                arc_name = str(Path(top_name) / rel_file).replace("\\", "/")
                zf.write(file_path, arc_name)


def run_patch_rom(repo_root: Path, world_name: str) -> None:
    """
    Calls patch_rom.py from:
      repo_root/worlds/<world_name>/kirby_ap_payload/patch_rom.py

    Runs it with cwd set to kirby_ap_payload/ so it can find Makefile/payload.bin as expected.

    Generates:
      base_patch.bsdiff4 into repo_root/worlds/<world_name>/data/base_patch.bsdiff4
    """
    world_root = repo_root / "worlds" / world_name
    payload_dir = world_root / "kirby_ap_payload"
    patch_script = payload_dir / "patch_rom.py"

    if not patch_script.exists():
        raise SystemExit(f"patch_rom.py not found: {patch_script}")

    in_rom = payload_dir / "kirby.gba"
    if not in_rom.exists():
        raise SystemExit(f"Clean ROM not found (expected kirby.gba): {in_rom}")

    # Baseline output (location doesn’t matter as long as patch_rom can write it)
    out_rom = payload_dir / "kirby_base.gba"

    # Where the world will read the patch payload from
    data_dir = world_root / "data"
    ensure_dir(data_dir)
    patch_out = data_dir / "base_patch.bsdiff4"

    print("Running patch_rom pipeline:")
    print(f"  Script:     {patch_script}")
    print(f"  CWD:        {payload_dir}")
    print(f"  Input ROM:  {in_rom}")
    print(f"  Output ROM: {out_rom}")
    print(f"  Patch out:  {patch_out}")

    # Use same interpreter running this build script
    cmd = [sys.executable, str(patch_script), str(in_rom.name), str(out_rom.name), str(patch_out)]
    # Note: we pass in_rom.name/out_rom.name because cwd=payload_dir; patch_out is absolute.

    try:
        proc = subprocess.run(
            cmd,
            cwd=str(payload_dir),
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        if proc.stdout:
            print(proc.stdout.rstrip())
    except subprocess.CalledProcessError as e:
        output = (e.stdout or "").rstrip()
        raise SystemExit(
            "patch_rom.py failed.\n"
            f"Command: {' '.join(cmd)}\n"
            f"{output}"
        ) from e

    if not patch_out.exists():
        raise SystemExit(f"patch_rom.py completed but patch file was not created: {patch_out}")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Build and install an Archipelago .apworld for kirbyam.")
    p.add_argument("--world", default=DEFAULT_WORLD_NAME, help="World folder name under worlds/ (lowercase).")
    p.add_argument("--apcontainer-version", type=int, default=DEFAULT_APCONTAINER_VERSION,
                   help="APContainer manifest version/compatible_version to inject.")
    p.add_argument("--install-dir", default=DEFAULT_INSTALL_DIR_WINDOWS,
                   help=r"Archipelago custom_worlds directory (default: C:\ProgramData\Archipelago\custom_worlds).")
    p.add_argument("--no-install", action="store_true", help="Build .apworld but do not copy into install dir.")
    p.add_argument("--skip-patch", action="store_true", help="Skip calling patch_rom.py before packaging.")
    return p.parse_args()


def main() -> None:
    args = parse_args()

    world_name = args.world
    if world_name.lower() != world_name:
        raise SystemExit("World name must be lowercase (folder name and .apworld name).")

    # Script is at repo_root/worlds/kirbyam/<thisfile>.py => repo_root is two levels up.
    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parents[1]

    world_source = repo_root / "worlds" / world_name
    staging_root = repo_root / "build_apworld"
    staging_world = staging_root / world_name
    zip_path = repo_root / f"{world_name}.zip"
    apworld_path = repo_root / f"{world_name}.apworld"
    install_dir = Path(args.install_dir)
    install_path = install_dir / f"{world_name}.apworld"
    manifest_path = staging_world / "archipelago.json"

    print(f"Repo root:    {repo_root}")
    print(f"World source: {world_source}")

    if not world_source.exists():
        raise SystemExit(f"World folder not found: {world_source}")

    # ---- 0) Build baseline + generate base_patch.bsdiff4 ----
    if not args.skip_patch:
        run_patch_rom(repo_root, world_name)
    else:
        print("Skipping patch_rom.py (--skip-patch)")

    # ---- 1) Clean staging ----
    rm_tree(staging_root)
    ensure_dir(staging_world)

    # ---- 2) Copy world ----
    copy_world(world_source, staging_world)

    # ---- 3) Remove junk ----
    remove_junk(staging_world)

    # ---- 4) Ensure archipelago.json exists and includes APContainer fields ----
    if not manifest_path.exists():
        raise SystemExit(
            f"Missing manifest: {manifest_path}\n"
            f"Create worlds/{world_name}/archipelago.json first."
        )

    inject_apcontainer_fields(manifest_path, int(args.apcontainer_version))

    # ---- 5) Create zip then rename to .apworld ----
    if apworld_path.exists():
        apworld_path.unlink()

    zip_folder_with_top_level(staging_world, zip_path)
    zip_path.replace(apworld_path)

    # ---- 6) Install to Archipelago ----
    if not args.no_install:
        if not install_dir.exists():
            raise SystemExit(f"Archipelago custom_worlds directory not found: {install_dir}")
        shutil.copy2(apworld_path, install_path)

    print("")
    print(f"Built:        {apworld_path}")
    if not args.no_install:
        print(f"Installed to: {install_path}")
    else:
        print("Install:      (skipped --no-install)")
    print("")
    print("Next steps:")
    print("1) Restart ArchipelagoLauncher.exe")
    print("2) Click 'Generate Template Settings' and look for: Kirby & The Amazing Mirror")


if __name__ == "__main__":
    main()
