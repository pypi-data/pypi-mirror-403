# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub_runtime_modelserve.entities.run.vllmserve_run.entity import RunVllmserveRun

if typing.TYPE_CHECKING:
    from digitalhub.entities._base.entity.metadata import Metadata

    from digitalhub_runtime_modelserve.entities.run.vllmservetext_run.spec import RunSpecVllmservetextRun
    from digitalhub_runtime_modelserve.entities.run.vllmservetext_run.status import RunStatusVllmservetextRun


class RunVllmservetextRun(RunVllmserveRun):
    """
    RunVllmservetextRun class.
    """

    def __init__(
        self,
        project: str,
        uuid: str,
        kind: str,
        metadata: Metadata,
        spec: RunSpecVllmservetextRun,
        status: RunStatusVllmservetextRun,
        user: str | None = None,
    ) -> None:
        super().__init__(project, uuid, kind, metadata, spec, status, user)

        self.spec: RunSpecVllmservetextRun
        self.status: RunStatusVllmservetextRun
