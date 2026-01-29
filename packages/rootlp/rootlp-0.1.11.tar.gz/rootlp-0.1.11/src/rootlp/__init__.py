#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Date          : 2026-01-10
# Author        : Lancelot PINCET
# GitHub        : https://github.com/LancelotPincet
# Library       : rootLP

"""
A library that gathers root functions for custom script execution.
"""



# %% Source import
sources = {
'Section': 'rootlp.modules.Section_LP.Section',
'main': 'rootlp.modules.main_LP.main',
'menu': 'rootlp.modules.menu_LP.menu',
'mo': 'rootlp.modules.mo_LP.mo',
'print': 'rootlp.modules.print_LP.print',
'project_server': 'rootlp.modules.project_server_LP.project_server',
'user_inputs': 'rootlp.modules.user_inputs_LP.user_inputs'
}

from importlib import resources
from contextlib import contextmanager

@contextmanager
def resources_dir():
    with resources.as_file(resources.files("rootlp.resources")) as path:
        yield path

# %% Hidden imports
if False :
    import rootlp.modules.Section_LP.Section
    import rootlp.modules.main_LP.main
    import rootlp.modules.menu_LP.menu
    import rootlp.modules.mo_LP.mo
    import rootlp.modules.print_LP.print
    import rootlp.modules.project_server_LP.project_server
    import rootlp.modules.user_inputs_LP.user_inputs



# %% Lazy imports
from corelp import getmodule
__getattr__, __all__ = getmodule(sources)