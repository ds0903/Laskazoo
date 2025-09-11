# apps/orders/session_cart.py
from decimal import Decimal
from dataclasses import dataclass
from typing import Dict, List, Tuple

CART_KEY = "cart"

@dataclass
class CartItem:
    kind: str      # 'variant' або 'product'
    id: int
    qty: int
    price: Decimal

def _normalize(session):
    if CART_KEY not in session or not isinstance(session[CART_KEY], list):
        session[CART_KEY] = []
        session.modified = True

def add_item(session, kind: str, obj_id: int, price: Decimal, inc: int = 1):
    _normalize(session)
    items: List[Dict] = session[CART_KEY]
    for it in items:
        if it.get("kind") == kind and it.get("id") == obj_id:
            it["qty"] = int(it.get("qty", 1)) + inc
            session.modified = True
            return
    items.append({"kind": kind, "id": int(obj_id), "qty": int(inc), "price": str(price)})
    session.modified = True

def set_qty(session, kind: str, obj_id: int, qty: int):
    _normalize(session)
    qty = max(1, int(qty))
    for it in session[CART_KEY]:
        if it.get("kind") == kind and it.get("id") == obj_id:
            it["qty"] = qty
            session.modified = True
            return

def inc(session, kind: str, obj_id: int):
    add_item(session, kind, obj_id, price=Decimal(session_price(session, kind, obj_id)), inc=1)

def dec(session, kind: str, obj_id: int):
    _normalize(session)
    items = session[CART_KEY]
    for it in list(items):
        if it.get("kind") == kind and it.get("id") == obj_id:
            if int(it.get("qty", 1)) > 1:
                it["qty"] = int(it["qty"]) - 1
            else:
                items.remove(it)
            session.modified = True
            return

def remove(session, kind: str, obj_id: int):
    _normalize(session)
    items = session[CART_KEY]
    before = len(items)
    items[:] = [it for it in items if not (it.get("kind") == kind and it.get("id") == obj_id)]
    if len(items) != before:
        session.modified = True

def clear(session):
    session[CART_KEY] = []
    session.modified = True

def session_price(session, kind: str, obj_id: int) -> str:
    _normalize(session)
    for it in session[CART_KEY]:
        if it.get("kind") == kind and it.get("id") == obj_id:
            return it.get("price", "0")
    return "0"

def summary(session) -> Tuple[int, int, Decimal]:
    """
    Повертає (lines, qty, total) для сесійного кошика.
    """
    _normalize(session)
    items: List[Dict] = session[CART_KEY]
    lines = len(items)
    qty = sum(int(it.get("qty", 0)) for it in items)
    total = sum(Decimal(it.get("price", "0")) * int(it.get("qty", 0)) for it in items)
    return lines, qty, total
