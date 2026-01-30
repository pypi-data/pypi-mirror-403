# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: © 2025 Michael Pucher <contact@cluo.sh>
from .client import ManageClient, MessageError
from .common import DEFAULT_LANGUAGES


def cmd_list_actions(**kwargs):
    url = kwargs.get('manage_host')
    assert url
    c = ManageClient(url)
    plugins = c.list_plugins()
    plugins.sort(key=lambda p: p.name)

    actions = [(p.name, a) for p in plugins for a in p.actions]
    for plugin_name, action in actions:
        print(f'{plugin_name}: {action}')


def cmd_list_rules(**kwargs):
    url = kwargs.get('manage_host')
    assert url
    c = ManageClient(url)
    plugins = c.list_plugins()
    plugins.sort(key=lambda p: p.name)

    rules = [(p.name, r) for p in plugins for r in p.rules]
    for plugin_name, rule in rules:
        print(f'{plugin_name}: {rule}')


def cmd_list_languages(**kwargs):
    url = kwargs.get('manage_host')
    assert url
    c = ManageClient(url)
    plugins = c.list_plugins()
    plugins.sort(key=lambda p: p.name)

    for lang in DEFAULT_LANGUAGES:
        print(f'core: {lang}')

    languages = [(p.name, p.language) for p in plugins if p.language]
    for plugin_name, lang in languages:
        print(f'{plugin_name}: {lang}')


def cmd_force_print_language(**kwargs):
    url = kwargs.get('manage_host')
    assert url
    c = ManageClient(url)

    args = kwargs.get('args')
    assert args

    err = c.force_print_language(args.language)
    if err:
        print(f'Could not set output language: {err}')
        return

    if not args.language:
        print('Reset output language to default.')
    else:
        print(f'Set output language to {args.language}.')
    print('Make sure to refresh the decompiler window.')
