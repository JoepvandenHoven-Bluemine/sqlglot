from sqlglot import exp
from sqlglot.helper import subclasses


EXPRESSION_SPEC = {
    **{
        expr_type: {"returns": exp.DataType.Type.BIGINT}
        for expr_type in {
            exp.ApproxDistinct,
            exp.ArraySize,
            exp.CountIf,
            exp.Int64,
            exp.Length,
            exp.UnixDate,
            exp.UnixSeconds,
            exp.UnixMicros,
            exp.UnixMillis,
        }
    },
    **{
        expr_type: {"returns": exp.DataType.Type.BINARY}
        for expr_type in {
            exp.FromBase32,
            exp.FromBase64,
        }
    },
    **{
        expr_type: {"returns": exp.DataType.Type.BOOLEAN}
        for expr_type in {
            exp.Between,
            exp.Boolean,
            exp.Contains,
            exp.EndsWith,
            exp.In,
            exp.LogicalAnd,
            exp.LogicalOr,
            exp.Not
            exp.RegexpLike,
            exp.StartsWith,
        }
    },
    **{
        expr_type: {"returns": exp.DataType.Type.DATE}
        for expr_type in {
            exp.CurrentDate,
            exp.Date,
            exp.DateFromParts,
            exp.DateStrToDate,
            exp.DiToDate,
            exp.LastDay,
            exp.StrToDate,
            exp.TimeStrToDate,
            exp.TsOrDsToDate,
        }
    },
    **{
        expr_type: {"returns": exp.DataType.Type.DATETIME}
        for expr_type in {
            exp.CurrentDatetime,
            exp.Datetime,
            exp.DatetimeAdd,
            exp.DatetimeSub,
        }
    },
    **{
        expr_type: {"returns": exp.DataType.Type.DOUBLE}
        for expr_type in {
            exp.ApproxQuantile,
            exp.Avg,
            exp.Exp,
            exp.Ln,
            exp.Log,
            exp.Pi,
            exp.Pow,
            exp.Quantile,
            exp.Radians,
            exp.Round,
            exp.SafeDivide,
            exp.Sqrt,
            exp.Stddev,
            exp.StddevPop,
            exp.StddevSamp,
            exp.ToDouble,
            exp.Variance,
            exp.VariancePop,
        }
    },
    **{
        expr_type: {"returns": exp.DataType.Type.INT}
        for expr_type in {
            exp.Ascii,
            exp.Ceil,
            exp.DatetimeDiff,
            exp.DateDiff,
            exp.TimestampDiff,
            exp.TimeDiff,
            exp.Unicode,
            exp.DateToDi,
            exp.Levenshtein,
            exp.Sign,
            exp.StrPosition,
            exp.TsOrDiToDi,
        }
    },
    **{
        expr_type: {"returns": exp.DataType.Type.INTERVAL}
        for expr_type in {
            exp.Interval,
            exp.JustifyDays,
            exp.JustifyHours,
            exp.JustifyInterval,
            exp.MakeInterval,
        }
    },
    **{
        expr_type: {"returns": exp.DataType.Type.JSON}
        for expr_type in {
            exp.ParseJSON,
        }
    },
    **{
        expr_type: {"returns": exp.DataType.Type.TIME}
        for expr_type in {
            exp.CurrentTime,
            exp.Time,
            exp.TimeAdd,
            exp.TimeSub,
        }
    },
    **{
        expr_type: {"returns": exp.DataType.Type.TIMESTAMPTZ}
        for expr_type in {
            exp.CurrentTimestampLTZ,
        }
    },
    **{
        expr_type: {"returns": exp.DataType.Type.TIMESTAMP}
        for expr_type in {
            exp.CurrentTimestamp,
            exp.StrToTime,
            exp.TimeStrToTime,
            exp.TimestampAdd,
            exp.TimestampSub,
            exp.UnixToTime,
        }
    },
    **{
        expr_type: {"returns": exp.DataType.Type.TINYINT}
        for expr_type in {
            exp.Day,
            exp.Month,
            exp.Week,
            exp.Year,
            exp.Quarter,
        }
    },
    **{
        expr_type: {"returns": exp.DataType.Type.VARCHAR}
        for expr_type in {
            exp.ArrayToString,
            exp.Concat,
            exp.ConcatWs,
            exp.Chr,
            exp.DateToDateStr,
            exp.DPipe,
            exp.GroupConcat,
            exp.Initcap,
            exp.Lower,
            exp.Substring,
            exp.String,
            exp.TimeToStr,
            exp.TimeToTimeStr,
            exp.Trim,
            exp.ToBase32,
            exp.ToBase64,
            exp.TsOrDsToDateStr,
            exp.UnixToStr,
            exp.UnixToTimeStr,
            exp.Upper,
        }
    },
    **{
        expr_type: {"annotator": lambda self, e: self._annotate_binary(e)}
        for expr_type in subclasses(exp.__name__, exp.Binary)
    },
    **{
        expr_type: {"returns": "this"}
        for expr_type in subclasses(exp.__name__, (exp.Unary, exp.Alias), {exp.Not})
    },
    **{
        expr_type: {"returns": exp.DataType.Type.BOOLEAN}
        for expr_type in subclasses(exp.__name__, (exp.Connector, exp.Predicate))
    },
    exp.Abs: {"annotator": lambda self, e: self._annotate_by_args(e, "this")},
    exp.Anonymous: {"returns": exp.DataType.Type.UNKNOWN},
    exp.Array: {"annotator": lambda self, e: self._annotate_by_args(e, "expressions", array=True)},
    exp.AnyValue: {"annotator": lambda self, e: self._annotate_by_args(e, "this")},
    exp.ArrayAgg: {"annotator": lambda self, e: self._annotate_by_args(e, "this", array=True)},
    exp.ArrayConcat: {"annotator": lambda self, e: self._annotate_by_args(e, "this", "expressions")},
    exp.ArrayConcatAgg: {"annotator": lambda self, e: self._annotate_by_args(e, "this")},
    exp.ArrayFirst: {"annotator": lambda self, e: self._annotate_by_array_element(e)},
    exp.ArrayLast: {"annotator": lambda self, e: self._annotate_by_array_element(e)},
    exp.ArrayReverse: {"annotator": lambda self, e: self._annotate_by_args(e, "this")},
    exp.ArraySlice: {"annotator": lambda self, e: self._annotate_by_args(e, "this")},
    exp.Bracket: {"annotator": lambda self, e: self._annotate_bracket(e)},
    exp.Cast: {"annotator": lambda self, e: self._annotate_with_type(e, e.args["to"])},
    exp.Case: {"annotator": lambda self, e: self._annotate_by_args(e, "default", "ifs")},
    exp.Coalesce: {"annotator": lambda self, e: self._annotate_by_args(e, "this", "expressions")},
    exp.Count: {
        "annotator": lambda self, e: self._annotate_with_type(
            e, exp.DataType.Type.BIGINT if e.args.get("big_int") else exp.DataType.Type.INT
        )
    },
    exp.DataType: {"annotator": lambda self, e: self._annotate_with_type(e, e.copy())},
    exp.DateAdd: {"annotator": lambda self, e: self._annotate_timeunit(e)},
    exp.DateSub: {"annotator": lambda self, e: self._annotate_timeunit(e)},
    exp.DateTrunc: {"annotator": lambda self, e: self._annotate_timeunit(e)},
    exp.Distinct: {"annotator": lambda self, e: self._annotate_by_args(e, "expressions")},
    exp.Div: {"annotator": lambda self, e: self._annotate_div(e)},
    exp.Dot: {"annotator": lambda self, e: self._annotate_dot(e)},
    exp.Explode: {"annotator": lambda self, e: self._annotate_explode(e)},
    exp.Extract: {"annotator": lambda self, e: self._annotate_extract(e)},
    exp.Filter: {"annotator": lambda self, e: self._annotate_by_args(e, "this")},
    exp.GenerateSeries: {
        "annotator": lambda self, e: self._annotate_by_args(e, "start", "end", "step", array=True)
    },
    exp.GenerateDateArray: {
        "annotator": lambda self, e: self._annotate_with_type(e, exp.DataType.build("ARRAY<DATE>"))
    },
    exp.GenerateTimestampArray: {
        "annotator": lambda self, e: self._annotate_with_type(e, exp.DataType.build("ARRAY<TIMESTAMP>"))
    },
    exp.Greatest: {"annotator": lambda self, e: self._annotate_by_args(e, "this", "expressions")},
    exp.If: {"annotator": lambda self, e: self._annotate_by_args(e, "true", "false")},
    exp.Least: {"annotator": lambda self, e: self._annotate_by_args(e, "this", "expressions")},
    exp.Literal: {"annotator": lambda self, e: self._annotate_literal(e)},
    exp.LastValue: {"annotator": lambda self, e: self._annotate_by_args(e, "this")},
    exp.Map: {"annotator": lambda self, e: self._annotate_map(e)},
    exp.Max: {"annotator": lambda self, e: self._annotate_by_args(e, "this", "expressions")},
    exp.Min: {"annotator": lambda self, e: self._annotate_by_args(e, "this", "expressions")},
    exp.Null: {"returns": exp.DataType.Type.NULL},
    exp.Nullif: {"annotator": lambda self, e: self._annotate_by_args(e, "this", "expression")},
    exp.PropertyEQ: {"annotator": lambda self, e: self._annotate_by_args(e, "expression")},
    exp.Slice: {"returns": exp.DataType.Type.UNKNOWN},
    exp.Struct: {"annotator": lambda self, e: self._annotate_struct(e)},
    exp.Sum: {"annotator": lambda self, e: self._annotate_by_args(e, "this", "expressions", promote=True)},
    exp.SortArray: {"annotator": lambda self, e: self._annotate_by_args(e, "this")},
    exp.Timestamp: {
        "annotator": lambda self, e: self._annotate_with_type(
            e,
            exp.DataType.Type.TIMESTAMPTZ if e.args.get("with_tz") else exp.DataType.Type.TIMESTAMP,
        )
    },
    exp.ToMap: {"annotator": lambda self, e: self._annotate_to_map(e)},
    exp.TryCast: {"annotator": lambda self, e: self._annotate_with_type(e, e.args["to"])},
    exp.Unnest: {"annotator": lambda self, e: self._annotate_unnest(e)},
    exp.VarMap: {"annotator": lambda self, e: self._annotate_map(e)},
    exp.Window: {"annotator": lambda self, e: self._annotate_by_args(e, "this")},
}
