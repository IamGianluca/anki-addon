"""Entry point for: uv run python -m tests.evals.viewer [--dir PATH]

Point --dir at the addon's traces/ folder to review production
sessions; without it, the viewer shows tests/evals/results/.
"""

import argparse
import os


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Viewer for eval results and production traces"
    )
    parser.add_argument(
        "--dir",
        help="Directory of run folders to view "
        "(default: tests/evals/results). Point at the addon's traces/ "
        "folder to review production sessions.",
    )
    args = parser.parse_args()
    if args.dir:
        os.environ["EVAL_VIEWER_DIR"] = args.dir

    import uvicorn
    from tests.evals.viewer import app

    uvicorn.run(app, host="127.0.0.1", port=5000)


if __name__ == "__main__":
    main()
