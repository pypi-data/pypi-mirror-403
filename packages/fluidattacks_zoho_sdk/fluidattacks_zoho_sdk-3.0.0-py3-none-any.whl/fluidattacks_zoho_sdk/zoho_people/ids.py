from __future__ import annotations

from dataclasses import dataclass

from fluidattacks_etl_utils.natural import Natural


@dataclass(frozen=True)
class LeaveId:
    id_leave: Natural


@dataclass(frozen=True)
class LeaveTypeId:
    id_type: Natural


@dataclass(frozen=True)
class EmployeeId:
    id_employee: Natural


@dataclass(frozen=True)
class ZuId:
    id_zuid: Natural
