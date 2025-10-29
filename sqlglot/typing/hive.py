from __future__ import annotations

from sqlglot import exp
from sqlglot.typing import EXPRESSION_SPEC

# Hive-specific EXPRESSION_SPEC - merge base spec and add overrides
EXPRESSION_SPEC = {
    **EXPRESSION_SPEC.copy(),
    exp.If: {"annotator": lambda self, e: self._annotate_by_args(e, "true", "false", promote=True)},
    exp.Coalesce: {
        "annotator": lambda self, e: self._annotate_by_args(e, "this", "expressions", promote=True)
    },
}
