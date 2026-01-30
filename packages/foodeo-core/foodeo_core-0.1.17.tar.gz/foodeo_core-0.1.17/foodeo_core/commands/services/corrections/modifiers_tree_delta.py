from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Callable, TypeVar

from foodeo_core.shared.entities.irequests import (
    IModifierRequest,
    IOptionRequest,
    IModifierChildRequest,
    IOptionChildRequest,
)

T = TypeVar("T")


def _index_by(items: list[T] | None, key_fn: Callable[[T], int | None]) -> dict[int, T]:
    out: dict[int, T] = {}
    for it in (items or []):
        k = key_fn(it)
        if k is None:
            continue
        out[k] = it
    return out


def _neg_qty(qty: int) -> int:
    return -abs(int(qty))


@dataclass(frozen=True)
class OptionsChildDeltaService:
    def diff(self, db: list[IOptionChildRequest] | None, cmd: list[IOptionChildRequest] | None) -> list[
        IOptionChildRequest]:
        db_by = _index_by(db, lambda x: x.id)
        cmd_by = _index_by(cmd, lambda x: x.id)
        out: list[IOptionChildRequest] = []

        for oid, db_item in db_by.items():
            cmd_item = cmd_by.get(oid)

            # deleted
            if cmd_item is None:
                d = deepcopy(db_item)
                d.qty = _neg_qty(db_item.qty)
                out.append(d)
                continue

            # reduced
            if cmd_item.qty < db_item.qty:
                d = deepcopy(db_item)
                d.qty = _neg_qty(db_item.qty - cmd_item.qty)
                out.append(d)

        return out


@dataclass(frozen=True)
class ModifierChildDeltaService:
    option_child_service: OptionsChildDeltaService

    def diff(self, db: list[IModifierChildRequest] | None, cmd: list[IModifierChildRequest] | None) -> list[
        IModifierChildRequest]:
        db_by = _index_by(db, lambda x: x.id)
        cmd_by = _index_by(cmd, lambda x: x.id)
        out: list[IModifierChildRequest] = []

        for mid, db_item in db_by.items():
            cmd_item = cmd_by.get(mid)

            # deleted child => negate all option_children
            if cmd_item is None:
                option_deltas = []
                for oc in (db_item.options or []):
                    d = deepcopy(oc)
                    d.qty = _neg_qty(oc.qty)
                    option_deltas.append(d)
                if option_deltas:
                    dchild = deepcopy(db_item)
                    dchild.options = option_deltas
                    out.append(dchild)
                continue

            option_deltas = self.option_child_service.diff(db_item.options, cmd_item.options)
            if option_deltas:
                dchild = deepcopy(db_item)
                dchild.options = option_deltas
                out.append(dchild)

        return out


@dataclass(frozen=True)
class OptionDeltaService:
    modifier_child_service: ModifierChildDeltaService

    def diff(self, db: list[IOptionRequest] | None, cmd: list[IOptionRequest] | None) -> list[IOptionRequest]:
        db_by = _index_by(db, lambda x: x.id)
        cmd_by = _index_by(cmd, lambda x: x.id)
        out: list[IOptionRequest] = []

        for oid, db_item in db_by.items():
            cmd_item = cmd_by.get(oid)

            # deleted option => qty negative total + (opcional) nested deletions en child tree
            if cmd_item is None:
                dopt = deepcopy(db_item)
                dopt.qty = _neg_qty(db_item.qty)

                # si querés ser estricto: al borrar la opción, también borrar su nested
                # (si tu motor ya entiende que borrar opción borra todo, podés dejar modifiers=[]).
                child_deltas = self.modifier_child_service.diff(db_item.modifiers, None)
                dopt.modifiers = child_deltas
                out.append(dopt)
                continue

            qty_delta = 0
            if cmd_item.qty < db_item.qty:
                qty_delta = _neg_qty(db_item.qty - cmd_item.qty)

            child_deltas = self.modifier_child_service.diff(db_item.modifiers, cmd_item.modifiers)

            if qty_delta != 0 or child_deltas:
                dopt = deepcopy(db_item)
                # contrato contextual: si solo cambió nested, mandamos qty vigente de option
                dopt.qty = qty_delta if qty_delta != 0 else cmd_item.qty
                dopt.modifiers = child_deltas
                out.append(dopt)

        return out


class ModifierChildNegativeDeltaService:
    def __init__(self, option_child_service):
        self.option_child_service = option_child_service

    def diff(self, db, cmd):
        db_by_id = _index_by(db, lambda x: x.id)
        cmd_by_id = _index_by(cmd, lambda x: x.id)
        deltas = []
        for mid, db_item in db_by_id.items():
            cmd_item = cmd_by_id.get(mid)
            if not cmd_item:
                continue
            opt_deltas = self.option_child_service.diff(db_item.options, cmd_item.options)
            if opt_deltas:
                delta = deepcopy(db_item)
                delta.options = opt_deltas
                deltas.append(delta)
        return deltas


@dataclass(frozen=True)
class OptionNegativeDeltaService:
    modifier_child_service: ModifierChildNegativeDeltaService

    def diff(
            self,
            db: list[IOptionRequest] | None,
            cmd: list[IOptionRequest] | None,
    ) -> list[IOptionRequest]:
        db_by_id = _index_by(db, lambda x: x.id)
        cmd_by_id = _index_by(cmd, lambda x: x.id)

        deltas: list[IOptionRequest] = []
        for oid, db_item in db_by_id.items():
            cmd_item = cmd_by_id.get(oid)
            if not cmd_item:
                continue  # eliminados: luego

            qty_delta = 0
            if cmd_item.qty < db_item.qty:
                qty_delta = -(db_item.qty - cmd_item.qty)

            child_mod_deltas = self.modifier_child_service.diff(db_item.modifiers, cmd_item.modifiers)

            if qty_delta != 0 or child_mod_deltas:
                delta = deepcopy(db_item)
                # Contrato contextual: si no cambia qty pero cambia nested, mandamos qty vigente
                delta.qty = qty_delta if qty_delta != 0 else cmd_item.qty
                delta.modifiers = child_mod_deltas
                deltas.append(delta)

        return deltas


@dataclass(frozen=True)
class ModifierNegativeDeltaService:
    option_service: OptionNegativeDeltaService

    def diff(
            self,
            db: list[IModifierRequest] | None,
            cmd: list[IModifierRequest] | None,
    ) -> list[IModifierRequest]:
        db_by_mid = _index_by(db, lambda x: x.modifiers_id)
        cmd_by_mid = _index_by(cmd, lambda x: x.modifiers_id)

        deltas: list[IModifierRequest] = []
        for mid, db_item in db_by_mid.items():
            cmd_item = cmd_by_mid.get(mid)
            if not cmd_item:
                continue  # eliminados: luego

            db_qty = db_item.qty or 0
            cmd_qty = cmd_item.qty or 0

            qty_delta = 0
            if cmd_qty < db_qty:
                qty_delta = -(db_qty - cmd_qty)

            option_deltas = self.option_service.diff(db_item.options, cmd_item.options)

            if qty_delta != 0 or option_deltas:
                delta = deepcopy(db_item)
                delta.qty = qty_delta if qty_delta != 0 else cmd_item.qty  # qty contextual
                delta.options = option_deltas
                deltas.append(delta)

        return deltas


@dataclass(frozen=True)
class ModifierDeltaService:
    option_service: OptionDeltaService

    def diff(self, db: list[IModifierRequest] | None, cmd: list[IModifierRequest] | None) -> list[IModifierRequest]:
        db_by = _index_by(db, lambda x: x.modifiers_id)
        cmd_by = _index_by(cmd, lambda x: x.modifiers_id)
        out: list[IModifierRequest] = []

        for mid, db_item in db_by.items():
            cmd_item = cmd_by.get(mid)

            # deleted modifier => negate ALL options in that modifier (and nested)
            if cmd_item is None:
                option_deltas = self.option_service.diff(db_item.options, None)
                if option_deltas:
                    dmod = deepcopy(db_item)
                    dmod.options = option_deltas
                    out.append(dmod)
                continue

            option_deltas = self.option_service.diff(db_item.options, cmd_item.options)
            if option_deltas:
                dmod = deepcopy(db_item)
                dmod.options = option_deltas
                out.append(dmod)

        return out


def build_modifiers_tree_negative_delta_service() -> ModifierDeltaService:
    oc = OptionsChildDeltaService()
    mc = ModifierChildDeltaService(option_child_service=oc)
    op = OptionDeltaService(modifier_child_service=mc)
    mo = ModifierDeltaService(option_service=op)
    return mo
