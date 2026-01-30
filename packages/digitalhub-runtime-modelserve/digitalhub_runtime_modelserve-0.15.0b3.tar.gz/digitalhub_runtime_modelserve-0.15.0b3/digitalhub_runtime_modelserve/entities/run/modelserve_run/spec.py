# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.entities.run._base.spec import RunSpec, RunValidator


class RunSpecModelserveRun(RunSpec):
    """RunSpecModelserveRun specifications."""

    def __init__(
        self,
        task: str,
        local_execution: bool = False,
        path: str | None = None,
        model_name: str | None = None,
        function: str | None = None,
        workflow: str | None = None,
        volumes: list[dict] | None = None,
        resources: dict | None = None,
        envs: list[dict] | None = None,
        secrets: list[str] | None = None,
        profile: str | None = None,
        image: str | None = None,
        service_type: str | None = None,
        service_name: str | None = None,
        replicas: int | None = None,
        **kwargs,
    ) -> None:
        super().__init__(
            task,
            local_execution,
            function,
            workflow,
            volumes,
            resources,
            envs,
            secrets,
            profile,
            **kwargs,
        )
        self.path = path
        self.model_name = model_name
        self.image = image
        self.service_type = service_type
        self.service_name = service_name
        self.replicas = replicas


class RunValidatorModelserveRun(RunValidator):
    """RunValidatorModelserveRun Validator."""

    # Function parameters
    image: str | None = None

    # Task serve
    service_type: str | None = None
    service_name: str | None = None
    replicas: int | None = None

    # Run parameters
    path: str | None = None
    "Path to the model files"

    model_name: str | None = None
    "Name of the model"
