from fa_purity import ResultE
from fa_purity.json import JsonObj, JsonUnfolder
from fluidattacks_etl_utils.decode import DecodeUtils
from fluidattacks_etl_utils.natural import NaturalOperations

from fluidattacks_zoho_sdk.zoho_people.ids import EmployeeId, LeaveId, LeaveTypeId, ZuId


def decode_leave_id(raw: JsonObj) -> ResultE[LeaveId]:
    return JsonUnfolder.require(raw, "Zoho.ID", DecodeUtils.to_int).map(
        lambda v: LeaveId(NaturalOperations.absolute(v)),
    )


def decode_leave_type_id(raw: JsonObj) -> ResultE[LeaveTypeId]:
    return JsonUnfolder.require(raw, "Leavetype.ID", DecodeUtils.to_int).map(
        lambda v: LeaveTypeId(NaturalOperations.absolute(v)),
    )


def decode_zuid(raw: JsonObj) -> ResultE[ZuId]:
    return JsonUnfolder.require(raw, "ZUID", DecodeUtils.to_int).map(
        lambda v: ZuId(NaturalOperations.absolute(v)),
    )


def decode_employee_id(raw: JsonObj) -> ResultE[EmployeeId]:
    return JsonUnfolder.require(raw, "Employee.ID", DecodeUtils.to_int).map(
        lambda v: EmployeeId(NaturalOperations.absolute(v)),
    )
