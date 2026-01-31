class UnexpectedValueException(Exception):
    def __init__(self, res_id, attr_value):
        self.res_id = res_id
        self.attr_value = attr_value
        super().__init__(
            f"Unexpected value {self.attr_value} in resource {self.res_id.to_str()}"
        )
