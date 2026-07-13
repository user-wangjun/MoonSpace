"""Apply staged large image_gen assets to runtime assets after confirmation."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from stage_imagegen_v4_large_assets import OUT_DIR as STAGED_DIR
from stage_imagegen_v4_large_assets import main as stage_large_assets


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_DIR = ROOT / "assets" / "sprites" / "moonspace"

FILES_TO_APPLY = (
    "courtyard_bg_large.png",
    "main_menu_bg.png",
    "opening_cg_room.png",
    "opening_cg_moonlight.png",
    "opening_cg_blood_moon.png",
    "opening_cg_blackout.png",
    "player_envoy_large.png",
    "wugang_chop_large.png",
    "yutu_pounding_large.png",
)


def target_name(filename: str) -> str:
    """Map staged filenames to runtime filenames."""
    return filename


def planned_copies() -> list[tuple[Path, Path]]:
    return [(STAGED_DIR / name, RUNTIME_DIR / target_name(name)) for name in FILES_TO_APPLY]


def ensure_sources_exist() -> None:
    missing = [str(source) for source, _target in planned_copies() if not source.exists()]
    if missing:
        raise FileNotFoundError("Missing staged assets:\n" + "\n".join(missing))


def print_plan() -> None:
    print("Planned large image_gen asset application:")
    for source, target in planned_copies():
        status = "exists" if target.exists() else "new"
        print(f"- {source} -> {target} ({status})")


def apply_assets() -> None:
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    for source, target in planned_copies():
        shutil.copy2(source, target)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--confirm-replace-runtime-assets",
        action="store_true",
        help="Actually copy staged assets into assets/sprites/moonspace.",
    )
    parser.add_argument(
        "--skip-stage",
        action="store_true",
        help="Use existing staged files instead of regenerating them first.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.skip_stage:
        stage_large_assets()
    ensure_sources_exist()
    print_plan()
    if not args.confirm_replace_runtime_assets:
        print("Dry run only. Pass --confirm-replace-runtime-assets to replace runtime assets.")
        return

    apply_assets()
    print(f"Applied {len(FILES_TO_APPLY)} assets into {RUNTIME_DIR}")


if __name__ == "__main__":
    main()
