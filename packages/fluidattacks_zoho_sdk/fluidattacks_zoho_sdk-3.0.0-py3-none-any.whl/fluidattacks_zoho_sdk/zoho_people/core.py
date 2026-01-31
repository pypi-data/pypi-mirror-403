from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, time

from fa_purity import Cmd, FrozenList, Maybe, Stream

from fluidattacks_zoho_sdk._http_client.paginate import Limit

from .ids import EmployeeId, LeaveId, LeaveTypeId, ZuId


@dataclass(frozen=True)
class Leave:
    id_leave: LeaveId
    from_date: date
    leave_type_id: LeaveTypeId
    unit: str
    approval_status: str
    reason: Maybe[str]
    type_: str
    employee: str
    leave_type: str
    to: date
    employee_user: str
    zuid: ZuId
    employee_id: EmployeeId
    date_of_request: date


@dataclass(frozen=True)
class LeaveDay:
    date: date
    leave_count: Maybe[float]
    start_time: Maybe[time]
    end_time: Maybe[time]
    session: Maybe[int]


@dataclass(frozen=True)
class LeaveClient:
    get_leaves: Callable[
        [str, str, Limit],
        Cmd[Stream[FrozenList[tuple[Leave, FrozenList[LeaveDay]]]]],
    ]
