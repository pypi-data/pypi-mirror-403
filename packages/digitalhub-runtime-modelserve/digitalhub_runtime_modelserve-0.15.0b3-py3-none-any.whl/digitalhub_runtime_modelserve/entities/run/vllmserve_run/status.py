# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub_runtime_modelserve.entities.run.modelserve_run.status import RunStatusModelserveRun


class RunStatusVllmserveRun(RunStatusModelserveRun):
    """
    RunStatusVllmserveRun status.
    """

    def __init__(
        self,
        state: str,
        message: str | None = None,
        transitions: list[dict] | None = None,
        k8s: dict | None = None,
        metrics: dict | None = None,
        service: dict | None = None,
        openai: dict | None = None,
        **kwargs,
    ):
        super().__init__(
            state,
            message,
            transitions,
            k8s,
            metrics,
            service,
            **kwargs,
        )
        self.openai = openai
