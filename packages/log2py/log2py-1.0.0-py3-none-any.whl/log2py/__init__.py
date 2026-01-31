import datetime
import os

class Logger:
    def __init__(self, log_save_path="log"):
        self.now = datetime.datetime.now()
        self.log = []
        self.log_print = True
        self.save_log = True
        self.save_path = log_save_path

    def custom(self, log_type, text, color="\033[0m"):
        self.now = datetime.datetime.now()
        log_message = f"{self.now.strftime('%Y-%m-%d %H:%M:%S')} {log_type} {text}"
        self.log.append(log_message)

        if self.log_print:
            print(f"{self.now.strftime('%Y-%m-%d %H:%M:%S')} {color}{log_type}\033[0m {text}")

    def debug(self, text):
        self.custom("DEBUG", text, "\033[36m")

    def info(self, text):
        self.custom("INFO", text, "\033[94m")

    def warning(self, text):
        self.custom("WARNING", text, "\033[33m")

    def error(self, text):
        self.custom("ERROR", text, "\033[91m")

    def critical(self, text):
        self.custom("CRITICAL", text, "\033[31m")

    def save(self):
        self.now = datetime.datetime.now()
        os.makedirs(self.save_path, exist_ok=True)
        file_path = os.path.join(self.save_path, f"{self.now.strftime('%Y-%m-%d %H-%M-%S')}.log")
        with open(file_path, "w") as f:
            f.write("\n".join(self.log))

    def __del__(self, name):
        if self.save_log:
            self.save()
