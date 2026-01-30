# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub_runtime_modelserve.entities.function.modelserve.entity import FunctionModelserve

if typing.TYPE_CHECKING:
    from digitalhub.entities._base.entity.metadata import Metadata

    from digitalhub_runtime_modelserve.entities.function.vllmserve.spec import FunctionSpecVllmserve
    from digitalhub_runtime_modelserve.entities.function.vllmserve.status import FunctionStatusVllmserve


class FunctionVllmserve(FunctionModelserve):
    """
    FunctionVllmserve class.
    """

    def __init__(
        self,
        project: str,
        name: str,
        uuid: str,
        kind: str,
        metadata: Metadata,
        spec: FunctionSpecVllmserve,
        status: FunctionStatusVllmserve,
        user: str | None = None,
    ) -> None:
        super().__init__(project, name, uuid, kind, metadata, spec, status, user)

        self.spec: FunctionSpecVllmserve
        self.status: FunctionStatusVllmserve
