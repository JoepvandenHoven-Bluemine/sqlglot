from __future__ import annotations

from sqlglot import exp
from sqlglot.typing import EXPRESSION_SPEC

# TSQL-specific EXPRESSION_SPEC - merge base spec and add overrides
EXPRESSION_SPEC = {
    **EXPRESSION_SPEC.copy(),
    exp.Radians: {"annotator": lambda self, e: self._annotate_by_args(e, "this")},
}
