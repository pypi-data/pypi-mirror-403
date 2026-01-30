# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0
from digitalhub_runtime_modelserve.entities._commons.enums import EntityKinds
from digitalhub_runtime_modelserve.entities.function.huggingfaceserve.builder import FunctionHuggingfaceserveBuilder
from digitalhub_runtime_modelserve.entities.function.kubeaiservespeechtotext.builder import (
    FunctionKubeaiserveSpeechtotextBuilder,
)
from digitalhub_runtime_modelserve.entities.function.kubeaiservetext.builder import FunctionKubeaiserveTextBuilder
from digitalhub_runtime_modelserve.entities.function.mlflowserve.builder import FunctionMlflowserveBuilder
from digitalhub_runtime_modelserve.entities.function.sklearnserve.builder import FunctionSklearnserveBuilder
from digitalhub_runtime_modelserve.entities.function.vllmservepolling.builder import FunctionVllmservepollingBuilder
from digitalhub_runtime_modelserve.entities.function.vllmservespeech.builder import FunctionVllmservespeechBuilder
from digitalhub_runtime_modelserve.entities.function.vllmservetext.builder import FunctionVllmservetextBuilder
from digitalhub_runtime_modelserve.entities.run.huggingfaceserve_run.builder import RunHuggingfaceserveRunBuilder
from digitalhub_runtime_modelserve.entities.run.kubeaiservespeechtotext_run.builder import (
    RunKubeaiserveSpeechtotextRunBuilder,
)
from digitalhub_runtime_modelserve.entities.run.kubeaiservetext_run.builder import RunKubeaiserveTextRunBuilder
from digitalhub_runtime_modelserve.entities.run.mlflowserve_build_run.builder import RunMlflowserveBuildRunBuilder
from digitalhub_runtime_modelserve.entities.run.mlflowserve_serve_run.builder import RunMlflowserveServeRunBuilder
from digitalhub_runtime_modelserve.entities.run.sklearnserve_run.builder import RunSklearnserveRunBuilder
from digitalhub_runtime_modelserve.entities.run.vllmservepolling_run.builder import RunVllmservepollingRunBuilder
from digitalhub_runtime_modelserve.entities.run.vllmservespeech_run.builder import RunVllmservespeechRunBuilder
from digitalhub_runtime_modelserve.entities.run.vllmservetext_run.builder import RunVllmservetextRunBuilder
from digitalhub_runtime_modelserve.entities.task.huggingfaceserve_serve.builder import TaskHuggingfaceserveServeBuilder
from digitalhub_runtime_modelserve.entities.task.kubeaiservespeechtotext_serve.builder import (
    TaskKubeaiserveSpeechtotextServeBuilder,
)
from digitalhub_runtime_modelserve.entities.task.kubeaiservetext_serve.builder import TaskKubeaiserveTextServeBuilder
from digitalhub_runtime_modelserve.entities.task.mlflowserve_build.builder import TaskMlflowserveBuildBuilder
from digitalhub_runtime_modelserve.entities.task.mlflowserve_serve.builder import TaskMlflowserveServeBuilder
from digitalhub_runtime_modelserve.entities.task.sklearnserve_serve.builder import TaskSklearnserveServeBuilder
from digitalhub_runtime_modelserve.entities.task.vllmservepolling_serve.builder import TaskVllmservepollingServeBuilder
from digitalhub_runtime_modelserve.entities.task.vllmservespeech_serve.builder import TaskVllmservespeechServeBuilder
from digitalhub_runtime_modelserve.entities.task.vllmservetext_serve.builder import TaskVllmservetextServeBuilder

entity_builders = (
    (EntityKinds.FUNCTION_HUGGINGFACESERVE.value, FunctionHuggingfaceserveBuilder),
    (EntityKinds.FUNCTION_KUBEAISERVESPEECHTOTEXT.value, FunctionKubeaiserveSpeechtotextBuilder),
    (EntityKinds.FUNCTION_KUBEAISERVETEXT.value, FunctionKubeaiserveTextBuilder),
    (EntityKinds.FUNCTION_MLFLOWSERVE.value, FunctionMlflowserveBuilder),
    (EntityKinds.FUNCTION_SKLEARNSERVE.value, FunctionSklearnserveBuilder),
    (EntityKinds.FUNCTION_VLLMSERVEPOLLING.value, FunctionVllmservepollingBuilder),
    (EntityKinds.FUNCTION_VLLMSERVESPEECH.value, FunctionVllmservespeechBuilder),
    (EntityKinds.FUNCTION_VLLMSERVETEXT.value, FunctionVllmservetextBuilder),
    (EntityKinds.RUN_HUGGINGFACESERVE_SERVE.value, RunHuggingfaceserveRunBuilder),
    (EntityKinds.RUN_KUBEAISERVESPEECHTOTEXT_SERVE.value, RunKubeaiserveSpeechtotextRunBuilder),
    (EntityKinds.RUN_KUBEAISERVETEXT_SERVE.value, RunKubeaiserveTextRunBuilder),
    (EntityKinds.RUN_MLFLOWSERVE_BUILD.value, RunMlflowserveBuildRunBuilder),
    (EntityKinds.RUN_MLFLOWSERVE_SERVE.value, RunMlflowserveServeRunBuilder),
    (EntityKinds.RUN_SKLEARNSERVE_SERVE.value, RunSklearnserveRunBuilder),
    (EntityKinds.RUN_VLLMSERVEPOLLING_SERVE.value, RunVllmservepollingRunBuilder),
    (EntityKinds.RUN_VLLMSERVESPEECH_SERVE.value, RunVllmservespeechRunBuilder),
    (EntityKinds.RUN_VLLMSERVETEXT_SERVE.value, RunVllmservetextRunBuilder),
    (EntityKinds.TASK_HUGGINGFACESERVE_SERVE.value, TaskHuggingfaceserveServeBuilder),
    (EntityKinds.TASK_KUBEAISERVESPEECHTOTEXT_SERVE.value, TaskKubeaiserveSpeechtotextServeBuilder),
    (EntityKinds.TASK_KUBEAISERVETEXT_SERVE.value, TaskKubeaiserveTextServeBuilder),
    (EntityKinds.TASK_MLFLOWSERVE_BUILD.value, TaskMlflowserveBuildBuilder),
    (EntityKinds.TASK_MLFLOWSERVE_SERVE.value, TaskMlflowserveServeBuilder),
    (EntityKinds.TASK_SKLEARNSERVE_SERVE.value, TaskSklearnserveServeBuilder),
    (EntityKinds.TASK_VLLMSERVEPOLLING_SERVE.value, TaskVllmservepollingServeBuilder),
    (EntityKinds.TASK_VLLMSERVESPEECH_SERVE.value, TaskVllmservespeechServeBuilder),
    (EntityKinds.TASK_VLLMSERVETEXT_SERVE.value, TaskVllmservetextServeBuilder),
)

try:
    from digitalhub_runtime_modelserve.runtimes.builder import RuntimeModelserveBuilder

    runtime_builders = ((kind, RuntimeModelserveBuilder) for kind in [e.value for e in EntityKinds])
except ImportError:
    runtime_builders = tuple()
