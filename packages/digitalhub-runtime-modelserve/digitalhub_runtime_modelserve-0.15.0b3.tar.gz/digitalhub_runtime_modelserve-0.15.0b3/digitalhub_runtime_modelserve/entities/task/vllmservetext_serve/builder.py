# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.entities.task._base.builder import TaskBuilder

from digitalhub_runtime_modelserve.entities._base.runtime_entity.builder import RuntimeEntityBuilderVllmserveText
from digitalhub_runtime_modelserve.entities._commons.enums import EntityKinds
from digitalhub_runtime_modelserve.entities.task.vllmservetext_serve.entity import TaskVllmservetextServe
from digitalhub_runtime_modelserve.entities.task.vllmservetext_serve.spec import (
    TaskSpecVllmservetextServe,
    TaskValidatorVllmservetextServe,
)
from digitalhub_runtime_modelserve.entities.task.vllmservetext_serve.status import TaskStatusVllmservetextServe


class TaskVllmservetextServeBuilder(TaskBuilder, RuntimeEntityBuilderVllmserveText):
    """
    TaskVllmservetextServe builder.
    """

    ENTITY_CLASS = TaskVllmservetextServe
    ENTITY_SPEC_CLASS = TaskSpecVllmservetextServe
    ENTITY_SPEC_VALIDATOR = TaskValidatorVllmservetextServe
    ENTITY_STATUS_CLASS = TaskStatusVllmservetextServe
    ENTITY_KIND = EntityKinds.TASK_VLLMSERVETEXT_SERVE.value
