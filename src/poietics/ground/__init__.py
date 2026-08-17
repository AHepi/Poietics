"""Stable public surface for the substrate-independent ground engine."""

from .errors import GroundProgramError, GroundProgramErrorCode
from .evaluate import evaluate
from .model import (
    AtomRef,
    Evaluation,
    GroundProgram,
    GroundRule,
    RuleRef,
    Status,
)

__all__ = [
    "AtomRef",
    "Evaluation",
    "GroundProgram",
    "GroundProgramError",
    "GroundProgramErrorCode",
    "GroundRule",
    "RuleRef",
    "Status",
    "evaluate",
]

