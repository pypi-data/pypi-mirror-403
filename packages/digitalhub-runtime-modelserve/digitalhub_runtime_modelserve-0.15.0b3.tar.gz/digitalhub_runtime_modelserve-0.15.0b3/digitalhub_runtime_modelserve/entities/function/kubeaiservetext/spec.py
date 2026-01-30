# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub_runtime_modelserve.entities.function.kubeaiserve.spec import (
    FunctionSpecKubeaiserve,
    FunctionValidatorKubeaiserve,
)
from digitalhub_runtime_modelserve.entities.function.kubeaiservetext.enums import KubeaiEngine, KubeaiFeature


class FunctionSpecKubeaiserveText(FunctionSpecKubeaiserve):
    """
    FunctionSpecKubeaiserveText specifications.
    """

    def __init__(
        self,
        image: str | None = None,
        adapters: list[dict] | None = None,
        features: list[dict] | None = None,
        engine: str | None = None,
    ) -> None:
        super().__init__(image, adapters)
        self.features = features
        self.engine = engine


class FunctionValidatorKubeaiserveText(FunctionValidatorKubeaiserve):
    """
    FunctionValidatorKubeaiserveText validator.
    """

    features: list[KubeaiFeature] | None = None
    "Features."

    engine: KubeaiEngine | None = None
    "Engine."
