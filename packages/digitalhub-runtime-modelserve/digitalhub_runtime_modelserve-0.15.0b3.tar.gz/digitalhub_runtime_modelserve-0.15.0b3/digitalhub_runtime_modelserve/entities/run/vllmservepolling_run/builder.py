# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.entities.run._base.builder import RunBuilder

from digitalhub_runtime_modelserve.entities._base.runtime_entity.builder import RuntimeEntityBuilderVllmservePolling
from digitalhub_runtime_modelserve.entities._commons.enums import EntityKinds
from digitalhub_runtime_modelserve.entities.run.vllmservepolling_run.entity import RunVllmservepollingRun
from digitalhub_runtime_modelserve.entities.run.vllmservepolling_run.spec import (
    RunSpecVllmservepollingRun,
    RunValidatorVllmservepollingRun,
)
from digitalhub_runtime_modelserve.entities.run.vllmservepolling_run.status import RunStatusVllmservepollingRun


class RunVllmservepollingRunBuilder(RunBuilder, RuntimeEntityBuilderVllmservePolling):
    """
    RunVllmservepollingRunBuilder builder.
    """

    ENTITY_CLASS = RunVllmservepollingRun
    ENTITY_SPEC_CLASS = RunSpecVllmservepollingRun
    ENTITY_SPEC_VALIDATOR = RunValidatorVllmservepollingRun
    ENTITY_STATUS_CLASS = RunStatusVllmservepollingRun
    ENTITY_KIND = EntityKinds.RUN_VLLMSERVEPOLLING_SERVE.value
