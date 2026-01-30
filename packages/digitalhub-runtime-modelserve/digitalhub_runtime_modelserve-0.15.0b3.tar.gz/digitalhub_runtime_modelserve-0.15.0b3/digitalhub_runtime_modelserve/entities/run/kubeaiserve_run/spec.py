# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.entities.run._base.spec import RunSpec, RunValidator
from pydantic import Field

from digitalhub_runtime_modelserve.entities.run.kubeaiserve_run.models import KubeaiFile, Scaling

regexp = (
    r"^(store://([^/]+)/model/huggingface/.*)"
    + r"|"
    + r"^pvc?://.*$"
    + r"|"
    + r"^s3?://.*$"
    + r"|"
    + r"^ollama?://.*$"
    + r"|"
    + r"^hf?://.*$"
)


class RunSpecKubeaiserveRun(RunSpec):
    """RunSpecKubeaiserveRun specifications."""

    def __init__(
        self,
        task: str,
        local_execution: bool = False,
        function: str | None = None,
        workflow: str | None = None,
        volumes: list[dict] | None = None,
        resources: dict | None = None,
        envs: list[dict] | None = None,
        secrets: list[str] | None = None,
        profile: str | None = None,
        model_name: str | None = None,
        url: str | None = None,
        image: str | None = None,
        adapters: list[dict] | None = None,
        processors: int | None = None,
        env: dict | None = None,
        args: list[str] | None = None,
        cache_profile: str | None = None,
        scaling: dict | None = None,
        files: list[dict] | None = None,
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
        self.model_name = model_name
        self.url = url
        self.image = image
        self.adapters = adapters
        self.processors = processors
        self.env = env
        self.args = args
        self.cache_profile = cache_profile
        self.scaling = scaling
        self.files = files


class RunValidatorKubeaiserveRun(RunValidator):
    """RunValidatorKubeaiserveRun validator."""

    # Function parameters
    image: str | None = None
    adapters: list[dict] | None = None

    # Run parameters
    url: str | None = Field(pattern=regexp, default=None)
    "Model URL."

    model_name: str | None = None
    "Model name."

    processors: int | None = Field(default=None, ge=1)
    "Number of processors."

    env: dict | None = None
    """Environment variables."""

    args: list[str] | None = None
    """Arguments."""

    cache_profile: str | None = None
    """Cache profile."""

    files: list[KubeaiFile] | None = None
    """Files."""

    scaling: Scaling | None = None
    """Scaling parameters."""
