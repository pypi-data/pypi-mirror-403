# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub_runtime_modelserve.entities.function.vllmserve.entity import FunctionVllmserve

if typing.TYPE_CHECKING:
    from digitalhub.entities._base.entity.metadata import Metadata

    from digitalhub_runtime_modelserve.entities.function.vllmservetext.spec import FunctionSpecVllmservetext
    from digitalhub_runtime_modelserve.entities.function.vllmservetext.status import FunctionStatusVllmservetext


class FunctionVllmservetext(FunctionVllmserve):
    """
    FunctionVllmservetext class.
    """

    def __init__(
        self,
        project: str,
        name: str,
        uuid: str,
        kind: str,
        metadata: Metadata,
        spec: FunctionSpecVllmservetext,
        status: FunctionStatusVllmservetext,
        user: str | None = None,
    ) -> None:
        super().__init__(project, name, uuid, kind, metadata, spec, status, user)

        self.spec: FunctionSpecVllmservetext
        self.status: FunctionStatusVllmservetext
