"""Command-line interface for JSON-to-cloned-conversation generation."""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from conversion.generator import generate_conversation
from conversion.profiles import resolve_locked_voice
from conversion.schema import load_conversation


def find_workspace(start: Path) -> Path:
    """Find the nearest parent containing the LPW project definition."""

    for candidate in (start.resolve(), *start.resolve().parents):
        if (candidate / "pyproject.toml").is_file() and (candidate / "src/lpw").is_dir():
            return candidate
    raise FileNotFoundError("could not find LPW workspace root")


def parse_args() -> argparse.Namespace:
    """Parse CLI options."""

    parser = argparse.ArgumentParser(
        description="Generate a cloned multi-character conversation from JSON."
    )
    parser.add_argument("conversation", type=Path, help="Conversation JSON file.")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--workspace-root", type=Path)
    parser.add_argument("--model-dir", type=Path)
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Validate JSON and locked speaker references without generating audio.",
    )
    return parser.parse_args()


def main() -> None:
    """Run JSON validation, clone generation, and audio assembly."""

    args = parse_args()
    script_path = args.conversation.expanduser().resolve()
    workspace = (
        args.workspace_root.expanduser().resolve()
        if args.workspace_root
        else find_workspace(Path.cwd())
    )
    spec = load_conversation(script_path)
    if args.validate_only:
        speakers = sorted({turn.speaker for turn in spec.turns})
        for speaker in speakers:
            reference = resolve_locked_voice(workspace, spec.project, speaker)
            print(
                f"OK {speaker}: {reference.audio_path} "
                f"sha256={reference.sha256}"
            )
        print(
            f"Valid conversation: {len(spec.turns)} turns, "
            f"{len(speakers)} speakers, target {spec.target_seconds:.2f}s"
        )
        return
    output_dir = (
        args.output_dir.expanduser().resolve()
        if args.output_dir
        else workspace
        / "outputs/qwen3-tts/cloned-conversations"
        / f"{script_path.stem}-{datetime.now().strftime('%Y%m%d-%H%M%S-%f')}"
    )
    result = generate_conversation(
        spec,
        workspace_root=workspace,
        output_dir=output_dir,
        model_dir=args.model_dir,
    )
    print(f"Conversation: {result}")


if __name__ == "__main__":
    main()
