# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.entities.run._base.builder import RunBuilder

from digitalhub_runtime_modelserve.entities._base.runtime_entity.builder import RuntimeEntityBuilderVllmserveSpeech
from digitalhub_runtime_modelserve.entities._commons.enums import EntityKinds
from digitalhub_runtime_modelserve.entities.run.vllmservespeech_run.entity import RunVllmservespeechRun
from digitalhub_runtime_modelserve.entities.run.vllmservespeech_run.spec import (
    RunSpecVllmservespeechRun,
    RunValidatorVllmservespeechRun,
)
from digitalhub_runtime_modelserve.entities.run.vllmservespeech_run.status import RunStatusVllmservespeechRun


class RunVllmservespeechRunBuilder(RunBuilder, RuntimeEntityBuilderVllmserveSpeech):
    """
    RunVllmservespeechRunBuilder builder.
    """

    ENTITY_CLASS = RunVllmservespeechRun
    ENTITY_SPEC_CLASS = RunSpecVllmservespeechRun
    ENTITY_SPEC_VALIDATOR = RunValidatorVllmservespeechRun
    ENTITY_STATUS_CLASS = RunStatusVllmservespeechRun
    ENTITY_KIND = EntityKinds.RUN_VLLMSERVESPEECH_SERVE.value
