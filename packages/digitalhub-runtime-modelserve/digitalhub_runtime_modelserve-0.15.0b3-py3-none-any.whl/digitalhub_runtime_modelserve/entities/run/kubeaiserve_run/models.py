# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from pydantic import BaseModel

from digitalhub_runtime_modelserve.entities.run.kubeaiserve_run.enums import LoadBalancingStrategy


class KubeaiPrefixHash(BaseModel):
    mean_load_factor: int | None = 125
    replication: int | None = 256
    prefix_char_length: int | None = 100


class LoadBalancing(BaseModel):
    strategy: LoadBalancingStrategy | None = LoadBalancingStrategy.LEAST_LOAD.value
    prefix_hash: KubeaiPrefixHash | None = KubeaiPrefixHash()


class Scaling(BaseModel):
    replicas: int | None = 1
    min_replicas: int | None = 1
    max_replicas: int | None = None
    autoscaling_disabled: bool = False
    target_request: int | None = 100
    scale_down_delay_seconds: int | None = 30
    load_balancing: LoadBalancing | None = None


class KubeaiFile(BaseModel):
    path: str | None = None
    content: str | None = None
