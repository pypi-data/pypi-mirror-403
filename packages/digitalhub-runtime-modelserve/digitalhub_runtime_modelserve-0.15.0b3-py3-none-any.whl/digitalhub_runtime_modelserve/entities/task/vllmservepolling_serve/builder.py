# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.entities.task._base.builder import TaskBuilder

from digitalhub_runtime_modelserve.entities._base.runtime_entity.builder import RuntimeEntityBuilderVllmservePolling
from digitalhub_runtime_modelserve.entities._commons.enums import EntityKinds
from digitalhub_runtime_modelserve.entities.task.vllmservepolling_serve.entity import TaskVllmservepollingServe
from digitalhub_runtime_modelserve.entities.task.vllmservepolling_serve.spec import (
    TaskSpecVllmservepollingServe,
    TaskValidatorVllmservepollingServe,
)
from digitalhub_runtime_modelserve.entities.task.vllmservepolling_serve.status import TaskStatusVllmservepollingServe


class TaskVllmservepollingServeBuilder(TaskBuilder, RuntimeEntityBuilderVllmservePolling):
    """
    TaskVllmservepollingServe builder.
    """

    ENTITY_CLASS = TaskVllmservepollingServe
    ENTITY_SPEC_CLASS = TaskSpecVllmservepollingServe
    ENTITY_SPEC_VALIDATOR = TaskValidatorVllmservepollingServe
    ENTITY_STATUS_CLASS = TaskStatusVllmservepollingServe
    ENTITY_KIND = EntityKinds.TASK_VLLMSERVEPOLLING_SERVE.value
