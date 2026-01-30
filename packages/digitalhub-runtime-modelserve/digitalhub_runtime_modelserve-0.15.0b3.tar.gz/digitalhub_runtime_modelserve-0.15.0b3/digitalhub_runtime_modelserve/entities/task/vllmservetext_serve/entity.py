# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub_runtime_modelserve.entities.task.vllmserve_serve.entity import TaskVllmserveServe

if typing.TYPE_CHECKING:
    from digitalhub.entities._base.entity.metadata import Metadata

    from digitalhub_runtime_modelserve.entities.task.vllmservetext_serve.spec import TaskSpecVllmservetextServe
    from digitalhub_runtime_modelserve.entities.task.vllmservetext_serve.status import TaskStatusVllmservetextServe


class TaskVllmservetextServe(TaskVllmserveServe):
    """
    TaskVllmservetextServe class.
    """

    def __init__(
        self,
        project: str,
        uuid: str,
        kind: str,
        metadata: Metadata,
        spec: TaskSpecVllmservetextServe,
        status: TaskStatusVllmservetextServe,
        user: str | None = None,
    ) -> None:
        super().__init__(project, uuid, kind, metadata, spec, status, user)

        self.spec: TaskSpecVllmservetextServe
        self.status: TaskStatusVllmservetextServe
