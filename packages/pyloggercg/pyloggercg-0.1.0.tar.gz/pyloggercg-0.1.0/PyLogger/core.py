import datetime
from colorprint import cprint

class Logger:
    levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

    def __init__(self, name="Logger", log_file=None):
        self.name = name
        self.log_file = log_file

    def log(self, level, message):
        if level not in self.levels:
            raise ValueError("Log level must be one of {}".format(self.levels))

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"{timestamp} [{level}] {self.name}: {message}"
        styles = {
            "DEBUG": "BLUE",
            "INFO": "CYAN",
            "WARNING": "YELLOW",
            "ERROR": "RED+BOLD",
            "CRITICAL": "MAGENTA+BOLD"
        }

        cprint(log_message, cstyle=styles.get(level, "BLACK"))
        if self.log_file:
            with open(self.log_file, "a") as f:
                f.write(log_message + "\n")

    def debug(self, msg):
        self.log("DEBUG", msg)

    def info(self, msg):
        self.log("INFO", msg)

    def warning(self, msg):
        self.log("WARNING", msg)

    def error(self, msg):
        self.log("ERROR", msg)

    def critical(self, msg):
        self.log("CRITICAL", msg)