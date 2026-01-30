# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.entities.run._base.builder import RunBuilder

from digitalhub_runtime_modelserve.entities._base.runtime_entity.builder import RuntimeEntityBuilderVllmserveText
from digitalhub_runtime_modelserve.entities._commons.enums import EntityKinds
from digitalhub_runtime_modelserve.entities.run.vllmservetext_run.entity import RunVllmservetextRun
from digitalhub_runtime_modelserve.entities.run.vllmservetext_run.spec import (
    RunSpecVllmservetextRun,
    RunValidatorVllmservetextRun,
)
from digitalhub_runtime_modelserve.entities.run.vllmservetext_run.status import RunStatusVllmservetextRun


class RunVllmservetextRunBuilder(RunBuilder, RuntimeEntityBuilderVllmserveText):
    """
    RunVllmservetextRunBuilder builder.
    """

    ENTITY_CLASS = RunVllmservetextRun
    ENTITY_SPEC_CLASS = RunSpecVllmservetextRun
    ENTITY_SPEC_VALIDATOR = RunValidatorVllmservetextRun
    ENTITY_STATUS_CLASS = RunStatusVllmservetextRun
    ENTITY_KIND = EntityKinds.RUN_VLLMSERVETEXT_SERVE.value
