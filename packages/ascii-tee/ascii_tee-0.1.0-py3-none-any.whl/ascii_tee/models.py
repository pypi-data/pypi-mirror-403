"""Data models for ASCII Tee."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal
import uuid

Color = Literal["black", "white"]
Size = Literal["S", "M", "L", "XL", "2XL"]

UNIT_PRICE_CENTS = 2000  # $20.00


@dataclass
class Design:
    """Represents an ASCII art design."""

    prompt: str
    ascii_art: str
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class Order:
    """Represents a t-shirt order."""

    design: Design
    color: Color = "black"
    size: Size = "L"
    quantity: int = 1

    @property
    def unit_price(self) -> int:
        """Price per shirt in cents."""
        return UNIT_PRICE_CENTS

    @property
    def subtotal(self) -> int:
        """Total price in cents."""
        return self.unit_price * self.quantity

    @property
    def subtotal_dollars(self) -> str:
        """Total price formatted as dollars."""
        return f"${self.subtotal / 100:.2f}"
