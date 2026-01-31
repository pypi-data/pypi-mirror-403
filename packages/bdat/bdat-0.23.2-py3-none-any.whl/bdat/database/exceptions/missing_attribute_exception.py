class MissingAttributeException(Exception):
    def __init__(self, res_id, res_typename, attr_name):
        self.res_id = res_id
        self.res_typename = res_typename
        self.attr_name = attr_name
        super().__init__(
            f"Missing attribute {self.attr_name} in {self.res_id.to_str()} ({self.res_typename})"
        )
