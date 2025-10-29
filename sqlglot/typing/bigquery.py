from __future__ import annotations

import typing as t

from sqlglot import exp
from sqlglot.typing import EXPRESSION_SPEC

if t.TYPE_CHECKING:
    from sqlglot.optimizer.annotate_types import TypeAnnotator


def _annotate_math_functions(self: TypeAnnotator, expression: exp.Expression) -> exp.Expression:
    """
    Many BigQuery math functions such as CEIL, FLOOR etc follow this return type convention:
    +---------+---------+---------+------------+---------+
    |  INPUT  | INT64   | NUMERIC | BIGNUMERIC | FLOAT64 |
    +---------+---------+---------+------------+---------+
    |  OUTPUT | FLOAT64 | NUMERIC | BIGNUMERIC | FLOAT64 |
    +---------+---------+---------+------------+---------+
    """
    self._annotate_args(expression)

    this: exp.Expression = expression.this

    self._set_type(
        expression,
        exp.DataType.Type.DOUBLE if this.is_type(*exp.DataType.INTEGER_TYPES) else this.type,
    )
    return expression


def _annotate_by_args_with_coerce(self: TypeAnnotator, expression: exp.Expression) -> exp.Expression:
    """
    +------------+------------+------------+-------------+---------+
    | INPUT      | INT64      | NUMERIC    | BIGNUMERIC  | FLOAT64 |
    +------------+------------+------------+-------------+---------+
    | INT64      | INT64      | NUMERIC    | BIGNUMERIC  | FLOAT64 |
    | NUMERIC    | NUMERIC    | NUMERIC    | BIGNUMERIC  | FLOAT64 |
    | BIGNUMERIC | BIGNUMERIC | BIGNUMERIC | BIGNUMERIC  | FLOAT64 |
    | FLOAT64    | FLOAT64    | FLOAT64    | FLOAT64     | FLOAT64 |
    +------------+------------+------------+-------------+---------+
    """
    self._annotate_args(expression)

    self._set_type(expression, self._maybe_coerce(expression.this.type, expression.expression.type))
    return expression


def _annotate_by_args_approx_top(self: TypeAnnotator, expression: exp.ApproxTopK) -> exp.ApproxTopK:
    self._annotate_args(expression)

    struct_type = exp.DataType(
        this=exp.DataType.Type.STRUCT,
        expressions=[expression.this.type, exp.DataType(this=exp.DataType.Type.BIGINT)],
        nested=True,
    )
    self._set_type(
        expression,
        exp.DataType(this=exp.DataType.Type.ARRAY, expressions=[struct_type], nested=True),
    )

    return expression


def _annotate_concat(self: TypeAnnotator, expression: exp.Concat) -> exp.Concat:
    annotated = self._annotate_by_args(expression, "expressions")

    # Args must be BYTES or types that can be cast to STRING, return type is either BYTES or STRING
    # https://cloud.google.com/bigquery/docs/reference/standard-sql/string_functions#concat
    if not annotated.is_type(exp.DataType.Type.BINARY, exp.DataType.Type.UNKNOWN):
        annotated.type = exp.DataType.Type.VARCHAR

    return annotated


def _annotate_array(self: TypeAnnotator, expression: exp.Array) -> exp.Array:
    array_args = expression.expressions

    # BigQuery behaves as follows:
    #
    # SELECT t, TYPEOF(t) FROM (SELECT 'foo') AS t            -- foo, STRUCT<STRING>
    # SELECT ARRAY(SELECT 'foo'), TYPEOF(ARRAY(SELECT 'foo')) -- foo, ARRAY<STRING>
    if (
        len(array_args) == 1
        and isinstance(select := array_args[0].unnest(), exp.Select)
        and (query_type := select.meta.get("query_type")) is not None
        and query_type.is_type(exp.DataType.Type.STRUCT)
        and len(query_type.expressions) == 1
        and isinstance(col_def := query_type.expressions[0], exp.ColumnDef)
        and (projection_type := col_def.kind) is not None
        and not projection_type.is_type(exp.DataType.Type.UNKNOWN)
    ):
        array_type = exp.DataType(
            this=exp.DataType.Type.ARRAY,
            expressions=[projection_type.copy()],
            nested=True,
        )
        return self._annotate_with_type(expression, array_type)

    return self._annotate_by_args(expression, "expressions", array=True)


# BigQuery-specific EXPRESSION_SPEC - merge base spec and add overrides
EXPRESSION_SPEC = {
    **EXPRESSION_SPEC.copy(),
    # BigQuery math functions with special return type logic
    **{
        expr_type: {"annotator": lambda self, e: _annotate_math_functions(self, e)}
        for expr_type in (exp.Floor, exp.Ceil, exp.Log, exp.Ln, exp.Sqrt, exp.Exp, exp.Round)
    },
    # BigQuery _annotate_by_args overrides
    **{
        expr_type: {"annotator": lambda self, e: self._annotate_by_args(e, "this")}
        for expr_type in (
            exp.Abs,
            exp.ArgMax,
            exp.ArgMin,
            exp.DateTrunc,
            exp.DatetimeTrunc,
            exp.FirstValue,
            exp.GroupConcat,
            exp.IgnoreNulls,
            exp.JSONExtract,
            exp.Lead,
            exp.Left,
            exp.Lower,
            exp.NthValue,
            exp.Pad,
            exp.PercentileDisc,
            exp.RegexpExtract,
            exp.RegexpReplace,
            exp.Repeat,
            exp.Replace,
            exp.RespectNulls,
            exp.Reverse,
            exp.Right,
            exp.SafeNegate,
            exp.Sign,
            exp.Substring,
            exp.TimestampTrunc,
            exp.Translate,
            exp.Trim,
            exp.Upper,
        )
    },
    # BigQuery-specific type overrides and additions
    exp.Acos: {"returns": exp.DataType.Type.DOUBLE},
    exp.Acosh: {"returns": exp.DataType.Type.DOUBLE},
    exp.Asin: {"returns": exp.DataType.Type.DOUBLE},
    exp.Asinh: {"returns": exp.DataType.Type.DOUBLE},
    exp.Atan: {"returns": exp.DataType.Type.DOUBLE},
    exp.Atanh: {"returns": exp.DataType.Type.DOUBLE},
    exp.Atan2: {"returns": exp.DataType.Type.DOUBLE},
    exp.ApproxTopSum: {"annotator": lambda self, e: _annotate_by_args_approx_top(self, e)},
    exp.ApproxTopK: {"annotator": lambda self, e: _annotate_by_args_approx_top(self, e)},
    exp.ApproxQuantiles: {"annotator": lambda self, e: self._annotate_by_args(e, "this", array=True)},
    exp.Array: {"annotator": _annotate_array},
    exp.ArrayConcat: {"annotator": lambda self, e: self._annotate_by_args(e, "this", "expressions")},
    exp.Ascii: {"returns": exp.DataType.Type.BIGINT},
    exp.BitwiseAndAgg: {"returns": exp.DataType.Type.BIGINT},
    exp.BitwiseOrAgg: {"returns": exp.DataType.Type.BIGINT},
    exp.BitwiseXorAgg: {"returns": exp.DataType.Type.BIGINT},
    exp.BitwiseCountAgg: {"returns": exp.DataType.Type.BIGINT},
    exp.ByteLength: {"returns": exp.DataType.Type.BIGINT},
    exp.ByteString: {"returns": exp.DataType.Type.BINARY},
    exp.Cbrt: {"returns": exp.DataType.Type.DOUBLE},
    exp.CodePointsToBytes: {"returns": exp.DataType.Type.BINARY},
    exp.CodePointsToString: {"returns": exp.DataType.Type.VARCHAR},
    exp.Concat: {"annotator": _annotate_concat},
    exp.Corr: {"returns": exp.DataType.Type.DOUBLE},
    exp.Cot: {"returns": exp.DataType.Type.DOUBLE},
    exp.CosineDistance: {"returns": exp.DataType.Type.DOUBLE},
    exp.Coth: {"returns": exp.DataType.Type.DOUBLE},
    exp.CovarPop: {"returns": exp.DataType.Type.DOUBLE},
    exp.CovarSamp: {"returns": exp.DataType.Type.DOUBLE},
    exp.Csc: {"returns": exp.DataType.Type.DOUBLE},
    exp.Csch: {"returns": exp.DataType.Type.DOUBLE},
    exp.CumeDist: {"returns": exp.DataType.Type.DOUBLE},
    exp.DateFromUnixDate: {"returns": exp.DataType.Type.DATE},
    exp.DenseRank: {"returns": exp.DataType.Type.BIGINT},
    exp.EuclideanDistance: {"returns": exp.DataType.Type.DOUBLE},
    exp.FarmFingerprint: {"returns": exp.DataType.Type.BIGINT},
    exp.Unhex: {"returns": exp.DataType.Type.BINARY},
    exp.Float64: {"returns": exp.DataType.Type.DOUBLE},
    exp.Format: {"returns": exp.DataType.Type.VARCHAR},
    exp.GenerateTimestampArray: {
        "annotator": lambda self, e: self._annotate_with_type(
            e, exp.DataType.build("ARRAY<TIMESTAMP>", dialect="bigquery")
        )
    },
    exp.Grouping: {"returns": exp.DataType.Type.BIGINT},
    exp.IsInf: {"returns": exp.DataType.Type.BOOLEAN},
    exp.IsNan: {"returns": exp.DataType.Type.BOOLEAN},
    exp.JSONArray: {"returns": exp.DataType.Type.JSON},
    exp.JSONArrayAppend: {"returns": exp.DataType.Type.JSON},
    exp.JSONArrayInsert: {"returns": exp.DataType.Type.JSON},
    exp.JSONBool: {"returns": exp.DataType.Type.BOOLEAN},
    exp.JSONExtractScalar: {"returns": exp.DataType.Type.VARCHAR},
    exp.JSONExtractArray: {"annotator": lambda self, e: self._annotate_by_args(e, "this", array=True)},
    exp.JSONFormat: {
        "annotator": lambda self, e: self._annotate_with_type(
            e, exp.DataType.Type.JSON if e.args.get("to_json") else exp.DataType.Type.VARCHAR
        )
    },
    exp.JSONKeysAtDepth: {
        "annotator": lambda self, e: self._annotate_with_type(
            e, exp.DataType.build("ARRAY<VARCHAR>", dialect="bigquery")
        )
    },
    exp.JSONObject: {"returns": exp.DataType.Type.JSON},
    exp.JSONRemove: {"returns": exp.DataType.Type.JSON},
    exp.JSONSet: {"returns": exp.DataType.Type.JSON},
    exp.JSONStripNulls: {"returns": exp.DataType.Type.JSON},
    exp.JSONType: {"returns": exp.DataType.Type.VARCHAR},
    exp.JSONValueArray: {
        "annotator": lambda self, e: self._annotate_with_type(
            e, exp.DataType.build("ARRAY<VARCHAR>", dialect="bigquery")
        )
    },
    exp.Lag: {"annotator": lambda self, e: self._annotate_by_args(e, "this", "default")},
    exp.LowerHex: {"returns": exp.DataType.Type.VARCHAR},
    exp.LaxBool: {"returns": exp.DataType.Type.BOOLEAN},
    exp.LaxFloat64: {"returns": exp.DataType.Type.DOUBLE},
    exp.LaxInt64: {"returns": exp.DataType.Type.BIGINT},
    exp.LaxString: {"returns": exp.DataType.Type.VARCHAR},
    exp.MD5Digest: {"returns": exp.DataType.Type.BINARY},
    exp.Normalize: {"returns": exp.DataType.Type.VARCHAR},
    exp.Ntile: {"returns": exp.DataType.Type.BIGINT},
    exp.ParseTime: {"returns": exp.DataType.Type.TIME},
    exp.ParseDatetime: {"returns": exp.DataType.Type.DATETIME},
    exp.ParseBignumeric: {"returns": exp.DataType.Type.BIGDECIMAL},
    exp.ParseNumeric: {"returns": exp.DataType.Type.DECIMAL},
    exp.PercentileCont: {"annotator": lambda self, e: _annotate_by_args_with_coerce(self, e)},
    exp.PercentRank: {"returns": exp.DataType.Type.DOUBLE},
    exp.Rank: {"returns": exp.DataType.Type.BIGINT},
    exp.RangeBucket: {"returns": exp.DataType.Type.BIGINT},
    exp.RegexpExtractAll: {"annotator": lambda self, e: self._annotate_by_args(e, "this", array=True)},
    exp.RegexpInstr: {"returns": exp.DataType.Type.BIGINT},
    exp.RowNumber: {"returns": exp.DataType.Type.BIGINT},
    exp.Rand: {"returns": exp.DataType.Type.DOUBLE},
    exp.SafeConvertBytesToString: {"returns": exp.DataType.Type.VARCHAR},
    exp.SafeAdd: {"annotator": lambda self, e: _annotate_by_args_with_coerce(self, e)},
    exp.SafeMultiply: {"annotator": lambda self, e: _annotate_by_args_with_coerce(self, e)},
    exp.SafeSubtract: {"annotator": lambda self, e: _annotate_by_args_with_coerce(self, e)},
    exp.Sec: {"returns": exp.DataType.Type.DOUBLE},
    exp.Sech: {"returns": exp.DataType.Type.DOUBLE},
    exp.Soundex: {"returns": exp.DataType.Type.VARCHAR},
    exp.SHA: {"returns": exp.DataType.Type.BINARY},
    exp.SHA2: {"returns": exp.DataType.Type.BINARY},
    exp.Sin: {"returns": exp.DataType.Type.DOUBLE},
    exp.Sinh: {"returns": exp.DataType.Type.DOUBLE},
    exp.Split: {"annotator": lambda self, e: self._annotate_by_args(e, "this", array=True)},
    exp.TimestampFromParts: {"returns": exp.DataType.Type.DATETIME},
    exp.TimeFromParts: {"returns": exp.DataType.Type.TIME},
    exp.TimeTrunc: {"returns": exp.DataType.Type.TIME},
    exp.ToCodePoints: {
        "annotator": lambda self, e: self._annotate_with_type(
            e, exp.DataType.build("ARRAY<BIGINT>", dialect="bigquery")
        )
    },
    exp.TsOrDsToTime: {"returns": exp.DataType.Type.TIME},
    exp.Unicode: {"returns": exp.DataType.Type.BIGINT},
    exp.Uuid: {"returns": exp.DataType.Type.VARCHAR},
}
