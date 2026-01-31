"""
Starts the azcam-app application.
"""

import sys
import os

import IPython

from azcam_app.ipython_config import ipython_config


def main():
    """
    Starts azcam-app.
    Usage examples: azcamapp full_path_to_config_file -- <options>
                    python -m azcam-app full_path_to_config_file -- <options>
    """

    print("Welcome to azcamapp!")

    # configure IPython
    c = ipython_config()

    # check for config file as first argument on command line
    if len(sys.argv) == 1:
        config_file = ""
        print("No configuration file specified")
    else:
        config_file = sys.argv[1]
        print("Configuration file is", config_file)

        # add config_file folder to Python search path
        config_folder = os.path.dirname(config_file)
        config_file = os.path.basename(config_file)
        if config_file.endswith(".py"):
            config_file = config_file[:-3]
        sys.path.append(config_folder)

        # import everything from config_file when IPython starts
        config_command = f"from {config_file} import *"
        c.InteractiveShellApp.exec_lines.append(config_command)

        # optimize for azcam-app
        _cmd = f"from azcam_app.optimize import *"
        c.InteractiveShellApp.exec_lines.append(_cmd)

    # start IPython in interactive mode
    IPython.start_ipython([], config=c)

    print("Exited embedded IPython")


if __name__ == "__main__":
    main()
