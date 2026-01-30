# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

import requests

from digitalhub_runtime_modelserve.entities.run.modelserve_run.entity import RunModelserveRun

if typing.TYPE_CHECKING:
    from digitalhub.entities._base.entity.metadata import Metadata

    from digitalhub_runtime_modelserve.entities.run.vllmserve_run.spec import RunSpecVllmserveRun
    from digitalhub_runtime_modelserve.entities.run.vllmserve_run.status import RunStatusVllmserveRun


class RunVllmserveRun(RunModelserveRun):
    """
    RunVllmserveRun class.
    """

    def __init__(
        self,
        project: str,
        uuid: str,
        kind: str,
        metadata: Metadata,
        spec: RunSpecVllmserveRun,
        status: RunStatusVllmserveRun,
        user: str | None = None,
    ) -> None:
        super().__init__(project, uuid, kind, metadata, spec, status, user)

        self.spec: RunSpecVllmserveRun
        self.status: RunStatusVllmserveRun

    def invoke(
        self,
        method: str = "POST",
        url: str | None = None,
        **kwargs,
    ) -> requests.Response:
        """
        Invoke served model.
        The method defaults to "POST" if data or json is provided in kwargs,
        otherwise it defaults to "GET". The function returns a requests.Response
        object.

        Parameters
        ----------
        method : str
            Method of the request (e.g., "GET", "POST").
        url : str
            URL to invoke. If specified, it must start with the service URL
            (http:// or https:// prefixes are required and stripped before comparison).
        **kwargs : dict
            Keyword arguments to pass to the request.

        Returns
        -------
        requests.Response
            Response from the request.
        """
        base_url: str = self._get_base_url()

        if url is None:
            url = self.status.service.get("urls")[0]
        else:
            self._eval_url(url, base_url)

        if "data" not in kwargs and "json" not in kwargs:
            method = "GET"

        return requests.request(method=method, url=url, **kwargs)
