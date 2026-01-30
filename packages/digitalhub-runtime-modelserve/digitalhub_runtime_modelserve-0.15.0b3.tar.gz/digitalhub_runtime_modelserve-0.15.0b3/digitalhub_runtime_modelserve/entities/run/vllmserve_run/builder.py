# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.entities.run._base.builder import RunBuilder

from digitalhub_runtime_modelserve.entities._base.runtime_entity.builder import RuntimeEntityBuilderVllmserve
from digitalhub_runtime_modelserve.entities._commons.enums import EntityKinds
from digitalhub_runtime_modelserve.entities.run.vllmserve_run.entity import RunVllmserveRun
from digitalhub_runtime_modelserve.entities.run.vllmserve_run.spec import (
    RunSpecVllmserveRun,
    RunValidatorVllmserveRun,
)
from digitalhub_runtime_modelserve.entities.run.vllmserve_run.status import RunStatusVllmserveRun


class RunVllmserveRunBuilder(RunBuilder, RuntimeEntityBuilderVllmserve):
    """
    RunVllmserveRunBuilder runer.
    """

    ENTITY_CLASS = RunVllmserveRun
    ENTITY_SPEC_CLASS = RunSpecVllmserveRun
    ENTITY_SPEC_VALIDATOR = RunValidatorVllmserveRun
    ENTITY_STATUS_CLASS = RunStatusVllmserveRun
    ENTITY_KIND = EntityKinds.RUN_VLLMSERVE_SERVE.value
