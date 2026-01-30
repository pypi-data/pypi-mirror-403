# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.entities.function._base.spec import FunctionSpec, FunctionValidator

from digitalhub_runtime_modelserve.entities.function.kubeaiserve.models import KubeaiAdapter


class FunctionSpecKubeaiserve(FunctionSpec):
    """
    FunctionSpecKubeaiserve specifications.
    """

    def __init__(
        self,
        image: str | None = None,
        adapters: list[dict] | None = None,
    ) -> None:
        super().__init__()
        self.image = image
        self.adapters = adapters


class FunctionValidatorKubeaiserve(FunctionValidator):
    """
    FunctionValidatorKubeaiserve validator.
    """

    image: str | None = None
    "Image where the function will be executed."

    adapters: list[KubeaiAdapter] | None = None
    "Adapters."
