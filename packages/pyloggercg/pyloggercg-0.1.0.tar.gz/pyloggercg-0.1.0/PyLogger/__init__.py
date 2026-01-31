from .core import Logger

import os
_welcome_file = os.path.join(os.path.expanduser("~"), ".pylogger_installed")

if not os.path.exists(_welcome_file):
    print("Greetings from the PyLogger Dev! Please visit https://github.com/CoolGuy158-Git/PyLogger for info and example code")
    with open(_welcome_file, "w") as f:
        f.write("installed")
