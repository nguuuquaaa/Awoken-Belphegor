
class FlowControl(Exception):
    message: str

    def __init__(self, message: str = ""):
        self.message = message

class CustomError(Exception):
    message: str

    def __init__(self, message: str = ""):
        self.message = message

class QueryFailed(CustomError):
    pass

class InvalidInput(CustomError):
    pass