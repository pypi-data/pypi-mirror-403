# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub_runtime_modelserve.entities.task.huggingfaceserve_serve.models import Backend, Dtype, HuggingfaceTask
from digitalhub_runtime_modelserve.entities.task.modelserve_serve.spec import (
    TaskSpecModelserveServe,
    TaskValidatorModelserveServe,
)


class TaskSpecHuggingfaceserveServe(TaskSpecModelserveServe):
    """
    TaskSpecHuggingfaceserveServe specifications.
    """

    def __init__(
        self,
        function: str,
        volumes: list[dict] | None = None,
        resources: dict | None = None,
        envs: list[dict] | None = None,
        secrets: list[str] | None = None,
        profile: str | None = None,
        huggingface_task: str | None = None,
        backend: str | None = None,
        tokenizer_revision: str | None = None,
        max_length: int | None = None,
        disable_lower_case: bool | None = None,
        disable_special_tokens: bool | None = None,
        dtype: str | None = None,
        trust_remote_code: bool | None = None,
        tensor_input_names: list[str] | None = None,
        return_token_type_ids: bool | None = None,
        return_probabilities: bool | None = None,
        **kwargs,
    ) -> None:
        super().__init__(
            function,
            volumes,
            resources,
            envs,
            secrets,
            profile,
            **kwargs,
        )
        self.huggingface_task = huggingface_task
        self.backend = backend
        self.tokenizer_revision = tokenizer_revision
        self.max_length = max_length
        self.disable_lower_case = disable_lower_case
        self.disable_special_tokens = disable_special_tokens
        self.dtype = dtype
        self.trust_remote_code = trust_remote_code
        self.tensor_input_names = tensor_input_names
        self.return_token_type_ids = return_token_type_ids
        self.return_probabilities = return_probabilities


class TaskValidatorHuggingfaceserveServe(TaskValidatorModelserveServe):
    """
    TaskValidatorHuggingfaceserveServe validator.
    """

    huggingface_task: HuggingfaceTask | None = None
    """
    Huggingface task name.
    """

    backend: Backend | None = None
    """
    Backend type.
    """

    tokenizer_revision: str | None = None
    """
    Tokenizer revision.
    """

    max_length: int | None = None
    """
    Huggingface max sequence length for the tokenizer.
    """

    disable_lower_case: bool | None = None
    """
    Do not use lower case for the tokenizer.
    """

    disable_special_tokens: bool | None = None
    """
    The sequences will not be encoded with the special tokens relative to their model
    """

    dtype: Dtype | None = None
    """
    Data type to load the weights in.
    """

    trust_remote_code: bool | None = None
    """
    Allow loading of models and tokenizers with custom code.
    """

    tensor_input_names: list[str] | None = None
    """
    The tensor input names passed to the model
    """

    return_token_type_ids: bool | None = None
    """
    Return token type ids
    """

    return_probabilities: bool | None = None
    """
    Return all probabilities
    """

    disable_log_requests: bool | None = None
    """
    Disable log requests
    """

    max_log_len: int | None = None
    """
    Max number of prompt characters or prompt
    """
