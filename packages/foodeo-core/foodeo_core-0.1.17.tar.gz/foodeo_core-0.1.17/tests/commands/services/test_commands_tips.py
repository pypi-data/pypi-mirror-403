import unittest
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel

from foodeo_core.commands.repositories.interfaces import IRequestsTableRepository
from foodeo_core.commands.services.request_for_corrections import CreateRequestForCorrectionsFromCommand
from foodeo_core.shared.entities import ProductInCommand, ProductInRequest
from foodeo_core.shared.entities.requests_tables import RequestsTableRow
from foodeo_core.shared.enums import RequestEnum, FromClientEnum


class FakeLocalCommand(BaseModel):
    id: int
    qr: str
    command_guests: Optional[int]
    details: str
    products: list[ProductInCommand]


class FakeRequestsTableRepository(IRequestsTableRepository):
    def __init__(self, rows: list[RequestsTableRow]):
        self._rows = rows

    def get_requests_tables_by_command(self, command_id: int) -> list[RequestsTableRow]:
        return list(self._rows)


def make_product_in_command(
        *,
        request_table: Optional[int],
        qty: int,
        name: str = "Prod",
) -> ProductInCommand:
    return ProductInCommand(
        request_table=request_table,
        qty=qty,
        name=name,
        price=Decimal("10.00"),
        amount=Decimal("10.00"),
        total_price=Decimal("10.00"),
        unit_price=Decimal("10.00"),
        modifiers=[],
    )


class TestCreateRequestForCorrectionsFromCommand(unittest.TestCase):
    def test_create_request_corrections_cases(self) -> None:
        cases = [
            {
                "name": "no_corrections_same_qty",
                "db_rows": [RequestsTableRow(id=1, product_id=100, qty=2)],
                "command_products": [make_product_in_command(request_table=1, qty=2, name="A")],
                "expected_has_request": False,
                "expected_products": [],
            },
            {
                "name": "creates_diff_when_command_qty_greater",
                "db_rows": [RequestsTableRow(id=1, product_id=100, qty=1)],
                "command_products": [make_product_in_command(request_table=1, qty=3, name="A")],
                "expected_has_request": True,
                "expected_products": [{"product_id": 100, "qty": 2}],
            },
            {
                "name": "ignores_db_row_not_present_in_command",
                "db_rows": [RequestsTableRow(id=999, product_id=200, qty=1)],
                "command_products": [make_product_in_command(request_table=1, qty=3, name="A")],
                "expected_has_request": False,
                "expected_products": [],
            },
            {
                "name": "does_not_create_when_command_qty_lower",
                "db_rows": [RequestsTableRow(id=1, product_id=100, qty=5)],
                "command_products": [make_product_in_command(request_table=1, qty=3, name="A")],
                "expected_has_request": False,
                "expected_products": [],
            },
            {
                "name": "multiple_rows_multiple_corrections",
                "db_rows": [
                    RequestsTableRow(id=1, product_id=100, qty=1),
                    RequestsTableRow(id=2, product_id=101, qty=2),
                ],
                "command_products": [
                    make_product_in_command(request_table=1, qty=2, name="A"),  # diff 1
                    make_product_in_command(request_table=2, qty=5, name="B"),  # diff 3
                ],
                "expected_has_request": True,
                "expected_products": [{"product_id": 100, "qty": 1}, {"product_id": 101, "qty": 3}],
            },
        ]

        for case in cases:
            with self.subTest(case=case["name"]):
                repo = FakeRequestsTableRepository(case["db_rows"])
                service = CreateRequestForCorrectionsFromCommand(repo)

                cmd = FakeLocalCommand(
                    id=10,
                    qr="qr-1",
                    command_guests=case.get("command_guests", 2),
                    details=case.get("details", ""),
                    products=case["command_products"],
                )

                result = service.create_request(cmd)
                self.assertTrue(result.is_success)

                req = result.value

                if not case["expected_has_request"]:
                    self.assertIsNone(req)
                    continue

                # Si esperas request, valida metadata
                self.assertIsNotNone(req)
                self.assertEqual(req.qr, "qr-1")
                self.assertEqual(req.command_id, 10)
                self.assertEqual(req.type, RequestEnum.local)
                self.assertEqual(req.from_client, FromClientEnum.web)

                # Valida productos (por id)
                self.assertTrue(hasattr(req, "products"))
                self.assertGreaterEqual(len(req.products), 1)

                by_id = {p.id: p for p in req.products}
                for expected in case["expected_products"]:
                    pid = expected["product_id"]
                    expected_qty = expected["qty"]
                    self.assertIn(pid, by_id)
                    p: ProductInRequest = by_id[pid]
                    self.assertEqual(p.qty, expected_qty)
                    self.assertEqual(p.id, pid)
