

class CustomError(Exception):
    def __init__(self, message):
        self.message = message

class FlowControl(CustomError):
    pass

class QueryFailed(CustomError):
    pass