# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.entities.task._base.builder import TaskBuilder

from digitalhub_runtime_modelserve.entities._base.runtime_entity.builder import RuntimeEntityBuilderVllmserveSpeech
from digitalhub_runtime_modelserve.entities._commons.enums import EntityKinds
from digitalhub_runtime_modelserve.entities.task.vllmservespeech_serve.entity import TaskVllmservespeechServe
from digitalhub_runtime_modelserve.entities.task.vllmservespeech_serve.spec import (
    TaskSpecVllmservespeechServe,
    TaskValidatorVllmservespeechServe,
)
from digitalhub_runtime_modelserve.entities.task.vllmservespeech_serve.status import TaskStatusVllmservespeechServe


class TaskVllmservespeechServeBuilder(TaskBuilder, RuntimeEntityBuilderVllmserveSpeech):
    """
    TaskVllmservespeechServe builder.
    """

    ENTITY_CLASS = TaskVllmservespeechServe
    ENTITY_SPEC_CLASS = TaskSpecVllmservespeechServe
    ENTITY_SPEC_VALIDATOR = TaskValidatorVllmservespeechServe
    ENTITY_STATUS_CLASS = TaskStatusVllmservespeechServe
    ENTITY_KIND = EntityKinds.TASK_VLLMSERVESPEECH_SERVE.value
