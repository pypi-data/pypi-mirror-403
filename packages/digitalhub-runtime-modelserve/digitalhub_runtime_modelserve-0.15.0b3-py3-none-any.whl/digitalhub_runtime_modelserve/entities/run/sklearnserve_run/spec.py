# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from pydantic import Field

from digitalhub_runtime_modelserve.entities.run.modelserve_run.spec import (
    RunSpecModelserveRun,
    RunValidatorModelserveRun,
)

path_regex = r"^(store://([^/]+)/model/sklearn/.*)|.*\.pkl$|.*\.joblib$"


class RunSpecSklearnserveRun(RunSpecModelserveRun):
    """RunSpecSklearnserveRun specifications."""


class RunValidatorSklearnserveRun(RunValidatorModelserveRun):
    """RunValidatorSklearnserveRun validator."""

    path: str | None = Field(default=None, pattern=path_regex)
    "Path to the model files"
