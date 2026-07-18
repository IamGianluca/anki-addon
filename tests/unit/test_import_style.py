"""Guard the add-on import strategy: add-on source must use relative imports.

Anki loads the add-on as a relative package from the add-ons folder, so no
top-level 'addon' package exists at runtime there. Absolute 'from addon...'
imports only work in tests (where src/ is on sys.path) and crash Anki at
startup. Tests themselves may import absolutely; this scan only covers src/.
"""

import ast
from pathlib import Path

SRC_DIR = Path(__file__).parents[2] / "src" / "addon"


def _absolute_addon_imports(path: Path) -> list[str]:
    tree = ast.parse(path.read_text())
    offenders = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            if node.level == 0 and node.module.split(".")[0] == "addon":
                offenders.append(
                    f"{path}:{node.lineno} from {node.module} import ..."
                )
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] == "addon":
                    offenders.append(
                        f"{path}:{node.lineno} import {alias.name}"
                    )
    return offenders


def test_addon_source_uses_relative_imports_only() -> None:
    # Given / When — scan every add-on source file for absolute imports
    offenders = []
    for path in sorted(SRC_DIR.rglob("*.py")):
        offenders.extend(_absolute_addon_imports(path))

    # Then
    assert offenders == [], (
        "Absolute 'addon' imports break under Anki's add-on loading; "
        "use relative imports:\n" + "\n".join(offenders)
    )
