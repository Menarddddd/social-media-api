class CredentialsException(Exception):
    def __init__(self, error):
        self.error = error


class FieldNotFoundException(Exception):
    def __init__(self, field, value):
        self.field = field
        self.value = value

    def __str__(self):
        return f"{self.field} not found"


class DuplicateEntryException(Exception):
    def __init__(self, field, value):
        self.field = field
        self.value = value

    def __str__(self):
        return f"{self.field} already exists"
