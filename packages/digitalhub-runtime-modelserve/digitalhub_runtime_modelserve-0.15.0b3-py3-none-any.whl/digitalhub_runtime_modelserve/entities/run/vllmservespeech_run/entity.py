# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub_runtime_modelserve.entities.run.vllmserve_run.entity import RunVllmserveRun

if typing.TYPE_CHECKING:
    from digitalhub.entities._base.entity.metadata import Metadata

    from digitalhub_runtime_modelserve.entities.run.vllmservespeech_run.spec import RunSpecVllmservespeechRun
    from digitalhub_runtime_modelserve.entities.run.vllmservespeech_run.status import RunStatusVllmservespeechRun


class RunVllmservespeechRun(RunVllmserveRun):
    """
    RunVllmservespeechRun class.
    """

    def __init__(
        self,
        project: str,
        uuid: str,
        kind: str,
        metadata: Metadata,
        spec: RunSpecVllmservespeechRun,
        status: RunStatusVllmservespeechRun,
        user: str | None = None,
    ) -> None:
        super().__init__(project, uuid, kind, metadata, spec, status, user)

        self.spec: RunSpecVllmservespeechRun
        self.status: RunStatusVllmservespeechRun
