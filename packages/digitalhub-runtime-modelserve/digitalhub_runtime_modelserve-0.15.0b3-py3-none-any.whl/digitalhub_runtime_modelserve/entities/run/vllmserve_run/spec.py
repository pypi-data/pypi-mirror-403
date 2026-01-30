# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub_runtime_modelserve.entities.run.modelserve_run.spec import (
    RunSpecModelserveRun,
    RunValidatorModelserveRun,
)


class RunSpecVllmserveRun(RunSpecModelserveRun):
    """RunSpecVllmserveRun specifications."""

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
        url: str | None = None,
        adapters: list[dict] | None = None,
        args: list[str] | None = None,
        enable_telemetry: bool | None = None,
        use_cpu_image: bool | None = None,
        storage_space: str | None = None,
        **kwargs,
    ) -> None:
        super().__init__(
            task,
            local_execution,
            path,
            model_name,
            function,
            workflow,
            volumes,
            resources,
            envs,
            secrets,
            profile,
            image,
            service_type,
            service_name,
            replicas,
            **kwargs,
        )
        self.url = url
        self.adapters = adapters
        self.args = args
        self.enable_telemetry = enable_telemetry
        self.use_cpu_image = use_cpu_image
        self.storage_space = storage_space


class RunValidatorVllmserveRun(RunValidatorModelserveRun):
    """RunValidatorVllmserveRun validator."""

    model_name: str | None = None
    image: str | None = None
    adapters: list[dict] | None = None

    # Run spec
    url: str | None = None
    """URL of the VLLMServe service."""

    args: list[str] | None = None
    """List of arguments to pass to the VLLMServe run."""

    enable_telemetry: bool | None = None
    """Flag to enable or disable telemetry for the VLLMServe run."""

    use_cpu_image: bool | None = None
    """Flag to indicate whether to use a CPU image for the VLLMServe run."""

    storage_space: str | None = None
    """Storage space to be used for the VLLMServe run."""
