# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.entities.function._base.builder import FunctionBuilder

from digitalhub_runtime_modelserve.entities._base.runtime_entity.builder import RuntimeEntityBuilderVllmserve
from digitalhub_runtime_modelserve.entities._commons.enums import EntityKinds
from digitalhub_runtime_modelserve.entities.function.vllmserve.entity import FunctionVllmserve
from digitalhub_runtime_modelserve.entities.function.vllmserve.spec import (
    FunctionSpecVllmserve,
    FunctionValidatorVllmserve,
)
from digitalhub_runtime_modelserve.entities.function.vllmserve.status import FunctionStatusVllmserve


class FunctionVllmserveBuilder(FunctionBuilder, RuntimeEntityBuilderVllmserve):
    """
    FunctionVllmserve builder.
    """

    ENTITY_CLASS = FunctionVllmserve
    ENTITY_SPEC_CLASS = FunctionSpecVllmserve
    ENTITY_SPEC_VALIDATOR = FunctionValidatorVllmserve
    ENTITY_STATUS_CLASS = FunctionStatusVllmserve
    ENTITY_KIND = EntityKinds.FUNCTION_VLLMSERVE.value
