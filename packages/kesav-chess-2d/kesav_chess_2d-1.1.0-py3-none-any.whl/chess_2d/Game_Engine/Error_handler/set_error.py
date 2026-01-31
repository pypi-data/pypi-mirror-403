class Error:
    flag=False
    message=""
    type=None

    def __init__(self,flag=False,type=" ", message=" "):
        self.flag=flag
        self.type=type
        self.message=message