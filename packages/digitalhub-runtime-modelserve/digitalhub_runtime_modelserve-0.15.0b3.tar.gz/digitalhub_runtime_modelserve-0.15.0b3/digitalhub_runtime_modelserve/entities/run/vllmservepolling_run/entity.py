# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub_runtime_modelserve.entities.run.vllmserve_run.entity import RunVllmserveRun

if typing.TYPE_CHECKING:
    from digitalhub.entities._base.entity.metadata import Metadata

    from digitalhub_runtime_modelserve.entities.run.vllmservepolling_run.spec import RunSpecVllmservepollingRun
    from digitalhub_runtime_modelserve.entities.run.vllmservepolling_run.status import RunStatusVllmservepollingRun


class RunVllmservepollingRun(RunVllmserveRun):
    """
    RunVllmservepollingRun class.
    """

    def __init__(
        self,
        project: str,
        uuid: str,
        kind: str,
        metadata: Metadata,
        spec: RunSpecVllmservepollingRun,
        status: RunStatusVllmservepollingRun,
        user: str | None = None,
    ) -> None:
        super().__init__(project, uuid, kind, metadata, spec, status, user)

        self.spec: RunSpecVllmservepollingRun
        self.status: RunStatusVllmservepollingRun
