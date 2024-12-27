from typing import Literal, TypedDict


class NumberConstraint(TypedDict):
    type: Literal["number"]
    step: int | float
    minimum: int
    maximum: int


class CheckboxConstraint(TypedDict):
    type: Literal["checkbox"]


class MultiCheckboxConstraint(TypedDict):
    type: Literal["multicheckbox"]
    choices: list[str]


class SelectConstraint(TypedDict):
    type: Literal["select"]
    choices: list[str]


ConfigConstraint = (
    NumberConstraint | CheckboxConstraint | MultiCheckboxConstraint | SelectConstraint
)


ConfigConstraintType = ConfigConstraint | dict[str, "ConfigConstraintType"]


def create_number_constraint(
    step: int | float = 1, minimum: int = 1, maximum: int = 999
) -> NumberConstraint:
    return NumberConstraint(type="number", step=step, minimum=minimum, maximum=maximum)


def create_checkbox_constraint() -> CheckboxConstraint:
    return CheckboxConstraint(type="checkbox")


def create_multi_checkbox_constraint(choices: list[str]) -> MultiCheckboxConstraint:
    return MultiCheckboxConstraint(type="multicheckbox", choices=choices)


def create_select_constraint(choices: list[str]) -> SelectConstraint:
    return SelectConstraint(type="select", choices=choices)
