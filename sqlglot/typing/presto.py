from __future__ import annotations

from sqlglot import exp
from sqlglot.typing import EXPRESSION_SPEC

# Presto-specific EXPRESSION_SPEC - merge base spec and add overrides
# The result of certain math functions in Presto/Trino is of type equal to the input type
# e.g: FLOOR(5.5/2) -> DECIMAL, FLOOR(5/2) -> BIGINT
EXPRESSION_SPEC = {
    **EXPRESSION_SPEC.copy(),
    **{
        expr_type: {"annotator": lambda self, e: self._annotate_by_args(e, "this")}
        for expr_type in (exp.Floor, exp.Ceil, exp.Round, exp.Sign, exp.Abs)
    },
    exp.Mod: {"annotator": lambda self, e: self._annotate_by_args(e, "this", "expression")},
    exp.Rand: {
        "annotator": lambda self, e: self._annotate_by_args(e, "this")
        if e.this
        else self._set_type(e, exp.DataType.Type.DOUBLE)
    },
}
