# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.entities.function._base.builder import FunctionBuilder

from digitalhub_runtime_modelserve.entities._base.runtime_entity.builder import RuntimeEntityBuilderVllmserveText
from digitalhub_runtime_modelserve.entities._commons.enums import EntityKinds
from digitalhub_runtime_modelserve.entities.function.vllmservetext.entity import FunctionVllmservetext
from digitalhub_runtime_modelserve.entities.function.vllmservetext.spec import (
    FunctionSpecVllmservetext,
    FunctionValidatorVllmservetext,
)
from digitalhub_runtime_modelserve.entities.function.vllmservetext.status import FunctionStatusVllmservetext


class FunctionVllmservetextBuilder(FunctionBuilder, RuntimeEntityBuilderVllmserveText):
    """
    FunctionVllmservetext builder.
    """

    ENTITY_CLASS = FunctionVllmservetext
    ENTITY_SPEC_CLASS = FunctionSpecVllmservetext
    ENTITY_SPEC_VALIDATOR = FunctionValidatorVllmservetext
    ENTITY_STATUS_CLASS = FunctionStatusVllmservetext
    ENTITY_KIND = EntityKinds.FUNCTION_VLLMSERVETEXT.value
