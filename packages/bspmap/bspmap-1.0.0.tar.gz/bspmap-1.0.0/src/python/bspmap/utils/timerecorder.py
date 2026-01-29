

class TimeRecorder:
    """A simple time recorder for measuring execution time of code blocks."""

    def __init__(self, name: str = "TimeRecorder"):
        self.name = name
        self.start_time = None

    def __enter__(self):
        import time
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        import time
        end_time = time.time()
        elapsed_time = end_time - self.start_time
        print(f"[{self.name}] Elapsed time: {elapsed_time:.6f} seconds")