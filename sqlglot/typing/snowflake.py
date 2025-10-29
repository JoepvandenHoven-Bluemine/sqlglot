from __future__ import annotations

import typing as t

from sqlglot import exp
from sqlglot.typing import EXPRESSION_SPEC

if t.TYPE_CHECKING:
    from sqlglot.optimizer.annotate_types import TypeAnnotator


def _annotate_reverse(self: TypeAnnotator, expression: exp.Reverse) -> exp.Reverse:
    expression = self._annotate_by_args(expression, "this")
    if expression.is_type(exp.DataType.Type.NULL):
        # Snowflake treats REVERSE(NULL) as a VARCHAR
        self._set_type(expression, exp.DataType.Type.VARCHAR)

    return expression


# Snowflake-specific EXPRESSION_SPEC - merge base spec and add overrides
EXPRESSION_SPEC = {
    **EXPRESSION_SPEC.copy(),
    # Snowflake _annotate_by_args overrides
    **{
        expr_type: {"annotator": lambda self, e: self._annotate_by_args(e, "this")}
        for expr_type in (
            exp.AddMonths,
            exp.Floor,
            exp.Left,
            exp.Pad,
            exp.Right,
            exp.Stuff,
            exp.Substring,
            exp.Round,
            exp.Ceil,
            exp.DateTrunc,
            exp.TimestampTrunc,
        )
    },
    # Snowflake NUMBER type for regexp functions
    **{
        expr_type: {
            "annotator": lambda self, e: self._annotate_with_type(
                e, exp.DataType.build("NUMBER", dialect="snowflake")
            )
        }
        for expr_type in (
            exp.RegexpCount,
            exp.RegexpInstr,
        )
    },
    # Snowflake-specific overrides
    exp.ConcatWs: {"annotator": lambda self, e: self._annotate_by_args(e, "expressions")},
    exp.ConvertTimezone: {
        "annotator": lambda self, e: self._annotate_with_type(
            e,
            exp.DataType.Type.TIMESTAMPNTZ
            if e.args.get("source_tz")
            else exp.DataType.Type.TIMESTAMPTZ,
        )
    },
    exp.Reverse: {"annotator": _annotate_reverse},
}
