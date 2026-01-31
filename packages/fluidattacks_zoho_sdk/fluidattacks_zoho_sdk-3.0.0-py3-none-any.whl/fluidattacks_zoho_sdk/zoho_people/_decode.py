from datetime import date, datetime, time

from fa_purity import (
    FrozenList,
    Maybe,
    PureIterFactory,
    Result,
    ResultE,
    ResultTransform,
    Unsafe,
)
from fa_purity.json import JsonObj, JsonPrimitiveUnfolder, JsonUnfolder, Unfolder
from fluidattacks_etl_utils import smash
from fluidattacks_etl_utils.decode import DecodeUtils

from fluidattacks_zoho_sdk.zoho_people.core import Leave, LeaveDay

from .decoders_ids import decode_employee_id, decode_leave_id, decode_leave_type_id, decode_zuid


def parse_date(value: str) -> ResultE[date]:
    try:
        dt = datetime.strptime(value, "%d-%b-%Y")  # noqa: DTZ007
        return Result.success(date(dt.year, dt.month, dt.day))
    except ValueError as e:
        return Result.failure(e)


def parse_time(value: str) -> ResultE[time]:
    try:
        hours, minutes = map(int, value.split(":"))
        return Result.success(time(hour=hours, minute=minutes))
    except ValueError as e:
        return Result.failure(e)


def decode_leave(raw: JsonObj) -> ResultE[Leave]:
    firts = smash.smash_result_5(
        decode_leave_id(raw),
        JsonUnfolder.require(raw, "From", DecodeUtils.to_str).bind(lambda v: parse_date(v)),
        decode_leave_type_id(raw),
        JsonUnfolder.require(raw, "Unit", DecodeUtils.to_str),
        JsonUnfolder.require(raw, "ApprovalStatus", DecodeUtils.to_str),
    )

    second = smash.smash_result_5(
        JsonUnfolder.optional(raw, "Reason", DecodeUtils.to_opt_str).map(
            lambda v: v.bind(lambda j: j),
        ),
        JsonUnfolder.require(raw, "Type", DecodeUtils.to_str),
        JsonUnfolder.require(raw, "Employee", DecodeUtils.to_str),
        JsonUnfolder.require(raw, "Leavetype", DecodeUtils.to_str),
        JsonUnfolder.require(raw, "To", DecodeUtils.to_str).bind(lambda v: parse_date(v)),
    )

    third = smash.smash_result_4(
        JsonUnfolder.require(raw, "EmployeeId", DecodeUtils.to_str),
        decode_zuid(raw),
        decode_employee_id(raw),
        JsonUnfolder.require(raw, "DateOfRequest", DecodeUtils.to_str).bind(
            lambda v: parse_date(v),
        ),
    )

    return smash.smash_result_3(firts, second, third).map(lambda v: Leave(*v[0], *v[1], *v[2]))


def validate_float(item: str) -> Maybe[float]:
    try:
        return Maybe.some(float(item))
    except ValueError:
        return Maybe.empty()


def decode_leave_day(raw: JsonObj, key: str) -> ResultE[LeaveDay]:
    date_result = parse_date(key)
    first = smash.smash_result_3(
        date_result,
        JsonUnfolder.require(raw, "LeaveCount", DecodeUtils.to_str).map(
            lambda v: validate_float(v),
        ),
        JsonUnfolder.optional(
            raw,
            "StartTime",
            lambda v: Unfolder.to_primitive(v).bind(
                lambda j: parse_time(
                    JsonPrimitiveUnfolder.to_str(j).alt(Unsafe.raise_exception).to_union(),
                ),
            ),
        ),
    )
    second = smash.smash_result_2(
        JsonUnfolder.optional(
            raw,
            "EndTime",
            lambda v: Unfolder.to_primitive(v).bind(
                lambda j: parse_time(
                    JsonPrimitiveUnfolder.to_str(j).alt(Unsafe.raise_exception).to_union(),
                ),
            ),
        ),
        JsonUnfolder.optional(
            raw,
            "Session",
            lambda v: Unfolder.to_primitive(v).bind(JsonPrimitiveUnfolder.to_int),
        ),
    )

    return smash.smash_result_2(first, second).map(lambda v: LeaveDay(*v[0], *v[1]))


def decode_leaves_days(raw: JsonObj) -> ResultE[FrozenList[LeaveDay]]:
    obj: JsonObj = (
        JsonUnfolder.require(raw, "Days", lambda v: Unfolder.to_json(v))
        .alt(Unsafe.raise_exception)
        .to_union()
    )
    items = list(obj.items())
    if not items:
        return Result.failure(ValueError("Empty list"))

    return ResultTransform.all_ok(
        PureIterFactory.from_list(items)
        .map(lambda v: Unfolder.to_json(v[1]).bind(lambda obj: decode_leave_day(obj, v[0])))
        .to_list(),
    )


def decode_leaves(raw: JsonObj) -> ResultE[FrozenList[tuple[Leave, FrozenList[LeaveDay]]]]:
    obj = (
        JsonUnfolder.require(raw, "records", lambda v: Unfolder.to_json(v))
        .alt(Unsafe.raise_exception)
        .to_union()
    )
    items = list(obj.items())
    if not items:
        return Result.success(FrozenList[tuple[Leave, FrozenList[LeaveDay]]]([]))

    return ResultTransform.all_ok(
        PureIterFactory.from_list(items)
        .map(
            lambda v: Unfolder.to_json(v[1]).bind(
                lambda j: smash.smash_result_2(decode_leave(j), decode_leaves_days(j)),
            ),
        )
        .to_list(),
    )
