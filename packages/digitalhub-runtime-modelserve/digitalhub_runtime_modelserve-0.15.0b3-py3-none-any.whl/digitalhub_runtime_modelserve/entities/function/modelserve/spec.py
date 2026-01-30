# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.entities.function._base.spec import FunctionSpec, FunctionValidator


class FunctionSpecModelserve(FunctionSpec):
    """
    FunctionSpecModelserve specifications.
    """

    def __init__(
        self,
        image: str | None = None,
    ) -> None:
        super().__init__()
        self.image = image


class FunctionValidatorModelserve(FunctionValidator):
    """
    FunctionValidatorModelserve validator.
    """

    image: str | None = None
    "Image where the function will be executed"
