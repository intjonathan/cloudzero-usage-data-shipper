class ConvertedCzJsonFile:
    def __init__(self, stream_name=None, file_name=None):
        self.stream_name = stream_name
        self.file_name = file_name

    def __str__(self):
        return f"stream_name: {self.stream_name}, file_name: {self.file_name}"