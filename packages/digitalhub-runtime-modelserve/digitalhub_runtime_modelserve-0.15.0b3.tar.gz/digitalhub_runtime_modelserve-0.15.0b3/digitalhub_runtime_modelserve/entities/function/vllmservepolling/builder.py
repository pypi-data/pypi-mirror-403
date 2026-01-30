# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.entities.function._base.builder import FunctionBuilder

from digitalhub_runtime_modelserve.entities._base.runtime_entity.builder import RuntimeEntityBuilderVllmservePolling
from digitalhub_runtime_modelserve.entities._commons.enums import EntityKinds
from digitalhub_runtime_modelserve.entities.function.vllmservepolling.entity import FunctionVllmservepolling
from digitalhub_runtime_modelserve.entities.function.vllmservepolling.spec import (
    FunctionSpecVllmservepolling,
    FunctionValidatorVllmservepolling,
)
from digitalhub_runtime_modelserve.entities.function.vllmservepolling.status import FunctionStatusVllmservepolling


class FunctionVllmservepollingBuilder(FunctionBuilder, RuntimeEntityBuilderVllmservePolling):
    """
    FunctionVllmservepolling builder.
    """

    ENTITY_CLASS = FunctionVllmservepolling
    ENTITY_SPEC_CLASS = FunctionSpecVllmservepolling
    ENTITY_SPEC_VALIDATOR = FunctionValidatorVllmservepolling
    ENTITY_STATUS_CLASS = FunctionStatusVllmservepolling
    ENTITY_KIND = EntityKinds.FUNCTION_VLLMSERVEPOLLING.value
