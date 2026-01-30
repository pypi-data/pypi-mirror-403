# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: © 2025 Michael Pucher <contact@cluo.sh>
from enum import Enum


class ManageRequest(Enum):
    Unknown = 0
    ListPlugins = 1
    FetchPipeline = 2
    ApplyPipeline = 3
    ListPipelines = 4
    SavePipeline = 5
    DeletePipeline = 6
    ForcePrintLanguage = 7

    def __bytes__(self):
        return bytes([self.value])


class ManageStatus(Enum):
    Ok = 0
    UnknownRequest = 1
    UnknownStatus = 2
    PipelineMessageError = 3
    PipelineSerializationError = 4
    PipelineFetchError = 5
    UnknownPrintLanguage = 6

    def __bytes__(self):
        return bytes([self.value])


class PipelineNodeType(Enum):
    Action = b'a'
    Rule = b'r'
    Group = b'g'
    Pool = b'p'
    ActionWithArgs = b'ax'


class PipelineNodeExtraArgs(Enum):
    Bool = b'b'


# The default print languages available in Ghidra
DEFAULT_LANGUAGES = [
    'c-language',
    'java-language'
]
