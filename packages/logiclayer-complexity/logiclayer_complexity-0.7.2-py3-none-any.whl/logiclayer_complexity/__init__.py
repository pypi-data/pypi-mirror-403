__title__ = "logiclayer-complexity"
__description__ = (
    "LogicLayer module to enable Economic Complexity calculation, "
    "using data from a tesseract-olap server."
)
__version__ = "0.7.2"

__all__ = ("ComplexityException", "EconomicComplexityModule")

from .exceptions import ComplexityException
from .module import EconomicComplexityModule
