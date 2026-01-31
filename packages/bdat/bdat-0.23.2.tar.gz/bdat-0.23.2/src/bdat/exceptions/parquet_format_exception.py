class ParquetFormatException(Exception):
    def __init__(self, cause):
        super().__init__(cause)
