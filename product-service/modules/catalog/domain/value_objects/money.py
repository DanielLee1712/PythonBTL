"""
Money Value Object
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Money:
    """Immutable Money value object."""
    
    amount: float
    currency: str = 'VND'

    def __post_init__(self):
        if self.amount < 0:
            raise ValueError("Amount cannot be negative.")

    def add(self, other: 'Money') -> 'Money':
        if self.currency != other.currency:
            raise ValueError("Cannot add different currencies.")
        return Money(amount=self.amount + other.amount, currency=self.currency)

    def subtract(self, other: 'Money') -> 'Money':
        if self.currency != other.currency:
            raise ValueError("Cannot subtract different currencies.")
        return Money(amount=self.amount - other.amount, currency=self.currency)

    def multiply(self, factor: float) -> 'Money':
        return Money(amount=self.amount * factor, currency=self.currency)

    def __str__(self):
        return f"{self.amount:,.0f} {self.currency}"
