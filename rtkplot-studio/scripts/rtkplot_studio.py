from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from rtkplot_data import RtkPlotError, parse_rtkplot, summarize_dataset
from rtkplot_plots import PLOT_TYPES, render_plot

VERSION = "0.1.0"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="rtkplot-studio",
        description="Inspect and plot 18-column RTKPlot solution text files.",
    )
    parser.add_argument("--version", action="version", version=f"RTKPlotStudio {VERSION}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect_parser = subparsers.add_parser("inspect", help="Summarize one or more inputs")
    inspect_parser.add_argument("--input", action="append", required=True, help="RTKPlot text path")
    inspect_parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")

    render_parser = subparsers.add_parser("render", help="Render one independent plot type")
    render_parser.add_argument("--input", action="append", required=True, help="RTKPlot text path")
    render_parser.add_argument("--plot", choices=PLOT_TYPES, required=True)
    render_parser.add_argument("--output", required=True, help="Output base path")
    render_parser.add_argument(
        "--formats",
        default="svg,png",
        help="Comma-separated output formats: svg,png",
    )
    render_parser.add_argument("--title", help="Optional figure title")
    render_parser.add_argument("--overwrite", action="store_true", help="Replace existing outputs")
    render_parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    return parser


def _emit(payload: dict[str, object], as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, ensure_ascii=True, indent=2))
        return
    for key, value in payload.items():
        print(f"{key}: {value}")


def _parse_formats(value: str) -> list[str]:
    formats = [item.strip().lower().lstrip(".") for item in value.split(",") if item.strip()]
    invalid = [item for item in formats if item not in {"svg", "png"}]
    if not formats or invalid:
        raise RtkPlotError("--formats must contain only svg and/or png")
    return list(dict.fromkeys(formats))


def _load_inputs(paths: Sequence[str]) -> list:
    datasets = []
    for raw_path in paths:
        path = Path(raw_path)
        if not path.is_file():
            raise RtkPlotError(f"input file does not exist: {path}")
        datasets.append(parse_rtkplot(path))
    return datasets


def run_inspect(args: argparse.Namespace) -> dict[str, object]:
    datasets = _load_inputs(args.input)
    return {
        "ok": True,
        "command": "inspect",
        "inputs": [summarize_dataset(dataset) for dataset in datasets],
    }


def run_render(args: argparse.Namespace) -> dict[str, object]:
    formats = _parse_formats(args.formats)
    datasets = _load_inputs(args.input)
    outputs = render_plot(
        datasets=datasets,
        plot_type=args.plot,
        output_base=Path(args.output),
        formats=formats,
        title=args.title,
        overwrite=args.overwrite,
    )
    return {
        "ok": True,
        "command": "render",
        "inputs": [str(dataset.path) for dataset in datasets],
        "plot": args.plot,
        "outputs": [str(path) for path in outputs],
        "sample_counts": [len(dataset.samples) for dataset in datasets],
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "inspect":
            payload = run_inspect(args)
        else:
            payload = run_render(args)
    except RtkPlotError as exc:
        command = getattr(args, "command", "rtkplot-studio")
        if getattr(args, "json", False):
            print(json.dumps({"ok": False, "command": command, "error": str(exc)}, indent=2))
        else:
            print(f"error: {exc}", file=sys.stderr)
        return 2
    _emit(payload, getattr(args, "json", False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
