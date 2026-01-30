# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: © 2025 Michael Pucher <contact@cluo.sh>
from __future__ import annotations
import ctypes
from multiprocessing import Pool
from pathlib import Path
from typing import Optional, Tuple
from .manage import client
from .config import log 


class _ActionDefinition(ctypes.Structure):
    _fields_ = [
        ('name', ctypes.c_char_p),
        ('cnstr', ctypes.POINTER(ctypes.c_ubyte))
    ]

class _RuleDefinition(ctypes.Structure):
    _fields_ = [
        ('name', ctypes.c_char_p),
        ('cnstr', ctypes.POINTER(ctypes.c_ubyte))
    ]

class _CActionDefinition(ctypes.Structure):
    _fields_ = [
        ('name', ctypes.c_char_p),
        ('cnstr', ctypes.POINTER(ctypes.c_ubyte)),
        ('destroy', ctypes.POINTER(ctypes.c_ubyte)),
        ('apply', ctypes.POINTER(ctypes.c_ubyte))
    ]

class _CRuleDefinition(ctypes.Structure):
    _fields_ = [
        ('name', ctypes.c_char_p),
        ('cnstr', ctypes.POINTER(ctypes.c_ubyte)),
        ('destroy', ctypes.POINTER(ctypes.c_ubyte)),
        ('oplist', ctypes.POINTER(ctypes.c_ubyte)),
        ('apply', ctypes.POINTER(ctypes.c_ubyte))
    ]


class Plugin(client.Plugin):
    actions: dict[str, int]
    rules: dict[str, int]
    language: Optional[str]
    file_path: Path
    name: str

    def __init__(
        self,
        file_path: Path,
        actions: dict[str, int],
        rules: dict[str, int],
        language: Optional[str]
    ):
        self.actions = actions
        self.rules = rules
        self.language = language
        self.name = file_path.stem.strip('lib')
        self.file_path = file_path

    @staticmethod
    def load_all(paths: list[Path]) -> list[Plugin]:
        plugin_paths = [path.resolve() for path in paths]
        for path in plugin_paths:
            log.info(f'Loading {path}')

        # Load plugins in a separate process to not pollute shared
        # libraries of other CPython modules
        with Pool(1) as p:
            load_results = p.map(Plugin.load_shared_lib, plugin_paths)

        plugins = []
        for file, plugin, err in load_results:
            if plugin is None:
                log.error(err)
                log.error(f'Could not load plugin {file}')
            else:
                plugins.append(plugin)

        plugins.sort(key=lambda p: p.name)
        return plugins

    @staticmethod
    def load_shared_lib(path: Path) -> Tuple[Path, Optional[Plugin], str]:
        # Python currently doesn't have a platform independent way to
        # unload CDLLs after loading them... this is gonna be rough
        # if we want to rebuild the plugins dynamically
        lib = ctypes.CDLL(str(path))

        try:
            getattr(lib, 'reoxide_c_abi')
            c_abi = True
        except AttributeError:
            c_abi = False

        try:
            getattr(lib, 'reoxide_rule_defs')
            getattr(lib, 'reoxide_rule_count')
        except AttributeError:
            err = f'Library {path} does not contain rule definitions'
            return path, None, err

        try:
            getattr(lib, 'reoxide_action_defs')
            getattr(lib, 'reoxide_action_count')
        except AttributeError:
            err = f'Library {path} does not contain action definitions'
            return path, None, err

        try:
            getattr(lib, 'reoxide_plugin_new')
            getattr(lib, 'reoxide_plugin_delete')
        except AttributeError:
            err = f'Library {path} does not contain context functions'
            return path, None, err

        action_count = ctypes.c_size_t.in_dll(lib, 'reoxide_action_count').value
        action_def = _CActionDefinition if c_abi else _ActionDefinition
        action_table = (action_def * action_count)
        actions = {
            action.name.decode(): i
            for i, action 
            in enumerate(action_table.in_dll(lib, "reoxide_action_defs"))
        }

        rule_count = ctypes.c_size_t.in_dll(lib, 'reoxide_rule_count').value
        rule_def = _CRuleDefinition if c_abi else _RuleDefinition
        rule_table = (rule_def * rule_count)
        rules = {
            rule.name.decode(): i
            for i, rule
            in enumerate(rule_table.in_dll(lib, "reoxide_rule_defs"))
        }

        try:
            getattr(lib, 'reoxide_language')

            lang = ctypes.c_char_p.in_dll(lib, 'reoxide_language').value
            if lang:
                language = lang.decode()
            else:
                language = None
        except AttributeError:
            language = None

        return path, Plugin(path, actions, rules, language), ''
