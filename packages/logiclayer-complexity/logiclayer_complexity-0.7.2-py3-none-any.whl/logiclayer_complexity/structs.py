from typing import Any, Literal

from pydantic import BaseModel, model_validator

Order = Literal["asc", "desc"]


class TopkIntent(BaseModel):
    """Intent for top-k filtering of results."""

    amount: int
    level: list[str]
    measure: str
    order: Order

    @model_validator(mode="before")
    @classmethod
    def parse_search(cls, value: Any):
        """Parse top-k intent from a string format."""
        if isinstance(value, str):
            amount, level, measure, order = value.split(".")
            return {
                "amount": amount,
                "level": [token.strip() for token in level.split(",")],
                "measure": measure,
                "order": order,
            }
        return value
