"""Static type checks — run with `mypy tests/type_checks.py`.

These assertions are type-only; mypy analyzes them but they are never executed
at runtime. If Anki's AddonManager or our FakeAddonManager drift from the
Protocol, mypy will report an error.

Note: ty does not resolve `__new__` return types correctly, so use mypy here.
"""

from aqt.addons import AddonManager
from tests.fakes.aqt_fakes import FakeAddonManager

from addon.infrastructure.protocols import ConfigProvider


def _accept_protocol(_obj: ConfigProvider) -> None:
    """Type-checking helper — verifies structural Protocol compliance."""


# Real AddonManager must satisfy our Protocol.
# __new__ avoids needing real dependencies — mypy still checks the type.
_accept_protocol(AddonManager.__new__(AddonManager))

# Our fake must also satisfy the same Protocol.
# Catches us accidentally lagging behind when we extend the Protocol.
_accept_protocol(FakeAddonManager.__new__(FakeAddonManager))
