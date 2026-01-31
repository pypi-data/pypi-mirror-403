"""
PyCells — мини-табличный движок с формулами, таблицами, листами и курсором.
"""

from .session import init_db
from .core import PyCells

__all__ = ["init_db", "PyCells"]

__version__ = "0.2.5"
__author__ = "Zhandos Mambetali <zhandos.mambetali@gmail.com>"
