from enum import Enum


class Opcode(Enum):
    AliveTick = 0
    CalculateExpression = 1
    CalculationResult = 2
