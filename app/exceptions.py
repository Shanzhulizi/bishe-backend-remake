from app.core.constants import ResponseCode


# 业务异常（Business Exception）
class BizException(Exception):
    def __init__(
            self,
            code: ResponseCode,
            message: str | None = None
    ):
        self.code = code
        self.message = message or code.name
        super().__init__(self.message)
