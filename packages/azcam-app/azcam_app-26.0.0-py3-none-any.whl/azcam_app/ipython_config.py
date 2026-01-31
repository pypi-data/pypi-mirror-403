"""
Configure IPython for azcam-app, do not rely on profile.
"""

import os

from traitlets.config import Config
from IPython.terminal.prompts import Prompts, Token


def ipython_config():
    """
    Configure IPython for azcam-app
    """

    c = Config()

    c.InteractiveShellApp.exec_lines = [
        "from azcam_app.ipython_config import MyPrompts",
        "ip=get_ipython()",
        "ip.prompts=MyPrompts(ip)",
        "del MyPrompts, ip",
    ]
    c.InteractiveShellApp.gui = "tk"
    c.InteractiveShellApp.matplotlib = "tk"
    c.InteractiveShellApp.pylab_import_all = False
    c.InteractiveShell.autocall = 1
    c.InteractiveShell.colors = "nocolor"  # best for Terminal
    c.InteractiveShell.confirm_exit = False
    c.TerminalIPythonApp.display_banner = False
    c.TerminalInteractiveShell.display_completions = "readlinelike"
    c.TerminalInteractiveShell.highlight_matching_brackets = False
    c.TerminalInteractiveShell.term_title = False
    c.StoreMagics.autorestore = True

    return c


class MyPrompts(Prompts):
    def in_prompt_tokens(self):
        # Define the structure and styling of your input prompt
        return [
            (Token, os.getcwd()),
            (Token.Prompt, ">"),
        ]

    def out_prompt_tokens(self):
        # Define the structure and styling of your output prompt
        return [
            (Token, ""),
            (Token.Prompt, "==>"),
        ]
