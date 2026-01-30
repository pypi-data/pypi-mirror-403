# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub_runtime_modelserve.entities.function.vllmserve.entity import FunctionVllmserve

if typing.TYPE_CHECKING:
    from digitalhub.entities._base.entity.metadata import Metadata

    from digitalhub_runtime_modelserve.entities.function.vllmservepolling.spec import FunctionSpecVllmservepolling
    from digitalhub_runtime_modelserve.entities.function.vllmservepolling.status import FunctionStatusVllmservepolling


class FunctionVllmservepolling(FunctionVllmserve):
    """
    FunctionVllmservepolling class.
    """

    def __init__(
        self,
        project: str,
        name: str,
        uuid: str,
        kind: str,
        metadata: Metadata,
        spec: FunctionSpecVllmservepolling,
        status: FunctionStatusVllmservepolling,
        user: str | None = None,
    ) -> None:
        super().__init__(project, name, uuid, kind, metadata, spec, status, user)

        self.spec: FunctionSpecVllmservepolling
        self.status: FunctionStatusVllmservepolling
