# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.entities.function._base.builder import FunctionBuilder

from digitalhub_runtime_modelserve.entities._base.runtime_entity.builder import RuntimeEntityBuilderVllmserveSpeech
from digitalhub_runtime_modelserve.entities._commons.enums import EntityKinds
from digitalhub_runtime_modelserve.entities.function.vllmservespeech.entity import FunctionVllmservespeech
from digitalhub_runtime_modelserve.entities.function.vllmservespeech.spec import (
    FunctionSpecVllmservespeech,
    FunctionValidatorVllmservespeech,
)
from digitalhub_runtime_modelserve.entities.function.vllmservespeech.status import FunctionStatusVllmservespeech


class FunctionVllmservespeechBuilder(FunctionBuilder, RuntimeEntityBuilderVllmserveSpeech):
    """
    FunctionVllmservespeech builder.
    """

    ENTITY_CLASS = FunctionVllmservespeech
    ENTITY_SPEC_CLASS = FunctionSpecVllmservespeech
    ENTITY_SPEC_VALIDATOR = FunctionValidatorVllmservespeech
    ENTITY_STATUS_CLASS = FunctionStatusVllmservespeech
    ENTITY_KIND = EntityKinds.FUNCTION_VLLMSERVESPEECH.value
