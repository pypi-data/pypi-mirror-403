import sys

class Logger:
    def __init__(self, logfile="relax_log.txt"):
        self.terminal = sys.stdout
        self.log = open(logfile, "w", buffering=1)

    def write(self, msg):
        self.terminal.write(msg)
        self.log.write(msg)

    def flush(self):
        self.terminal.flush()
        self.log.flush()

    def close(self):
        try:
            self.log.flush()
        finally:
            self.log.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
