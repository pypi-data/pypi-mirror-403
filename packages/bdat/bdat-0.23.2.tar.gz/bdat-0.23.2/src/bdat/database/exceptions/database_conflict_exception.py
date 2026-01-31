class DatabaseConflictException(Exception):
    conflicting_id: int

    def __init__(self, conflicting_id: int):
        self.conflicting_id = conflicting_id
