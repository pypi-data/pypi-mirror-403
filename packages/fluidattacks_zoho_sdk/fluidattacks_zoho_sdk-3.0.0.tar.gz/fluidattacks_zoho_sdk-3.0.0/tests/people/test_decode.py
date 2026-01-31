from pathlib import Path

from fa_purity import Maybe, Unsafe
from fa_purity.json import JsonObj, JsonValueFactory, Unfolder
from fluidattacks_etl_utils.natural import NaturalOperations

from fluidattacks_zoho_sdk.zoho_people._decode import decode_leaves, parse_date, parse_time
from fluidattacks_zoho_sdk.zoho_people.core import Leave, LeaveDay
from fluidattacks_zoho_sdk.zoho_people.ids import EmployeeId, LeaveId, LeaveTypeId, ZuId


def read_json(name_file: str) -> JsonObj:
    raw_data_contact = Path(__file__).parent / name_file
    return (
        JsonValueFactory.load(raw_data_contact.open(encoding="utf-8"))
        .bind(Unfolder.to_json)
        .alt(Unsafe.raise_exception)
        .to_union()
    )


def test_decode() -> None:
    leaves_expected = (
        (
            Leave(
                LeaveId(NaturalOperations.absolute(794097000002012009)),
                parse_date("18-Dec-2024").alt(Unsafe.raise_exception).to_union(),
                LeaveTypeId(NaturalOperations.absolute(7940970000002615)),
                "Days",
                "Approved",
                Maybe.some("Vacaciones"),
                "PAID",
                "User fluid",
                "Vacations",
                parse_date("10-Jan-2025").alt(Unsafe.raise_exception).to_union(),
                "jfluid",
                ZuId(NaturalOperations.absolute(769891221)),
                EmployeeId(NaturalOperations.absolute(794097000000266450)),
                parse_date("07-Oct-2024").alt(Unsafe.raise_exception).to_union(),
            ),
            (
                LeaveDay(
                    parse_date("26-Dec-2024").alt(Unsafe.raise_exception).to_union(),
                    Maybe.some(float("1.0")),
                    Maybe.some(parse_time("09:00").alt(Unsafe.raise_exception).to_union()),
                    Maybe.some(parse_time("18:00").alt(Unsafe.raise_exception).to_union()),
                    Maybe.empty(),
                ),
                LeaveDay(
                    parse_date("29-Dec-2024").alt(Unsafe.raise_exception).to_union(),
                    Maybe.some(float("0.0")),
                    Maybe.empty(),
                    Maybe.empty(),
                    Maybe.some(1),
                ),
            ),
        ),
        (
            Leave(
                LeaveId(NaturalOperations.absolute(894097000002012009)),
                parse_date("11-Dec-2024").alt(Unsafe.raise_exception).to_union(),
                LeaveTypeId(NaturalOperations.absolute(7940970000002615)),
                "Days",
                "Approved",
                Maybe.some("Vacaciones"),
                "PAID",
                "User fluid",
                "Vacations",
                parse_date("10-Jan-2025").alt(Unsafe.raise_exception).to_union(),
                "jfluid",
                ZuId(NaturalOperations.absolute(769891221)),
                EmployeeId(NaturalOperations.absolute(794097000000266450)),
                parse_date("07-Oct-2024").alt(Unsafe.raise_exception).to_union(),
            ),
            (
                LeaveDay(
                    parse_date("11-Dec-2024").alt(Unsafe.raise_exception).to_union(),
                    Maybe.some(float("1.0")),
                    Maybe.some(parse_time("09:00").alt(Unsafe.raise_exception).to_union()),
                    Maybe.some(parse_time("18:00").alt(Unsafe.raise_exception).to_union()),
                    Maybe.empty(),
                ),
                LeaveDay(
                    parse_date("12-Dec-2024").alt(Unsafe.raise_exception).to_union(),
                    Maybe.some(float("0.0")),
                    Maybe.empty(),
                    Maybe.empty(),
                    Maybe.some(1),
                ),
            ),
        ),
    )

    path_file = "data_leaves.json"
    decode_data = decode_leaves(read_json(path_file)).alt(Unsafe.raise_exception).to_union()
    assert leaves_expected == decode_data
