# ★ 新增（枚举 / 状态码 / 固定值）


from enum import IntEnum


class ResponseCode(IntEnum):
    # ===== 通用 =====
    SUCCESS = 200
    UNKNOWN_ERROR = 10000
    PARAM_ERROR = 10001

    # ===== 认证 / 鉴权 =====
    AUTH_FAILED = 20001
    TOKEN_EXPIRED = 20002
    NO_PERMISSION = 20003

    # ===== 用户 =====
    USER_ALREADY_EXISTS = 30001
    USER_NOT_FOUND = 30002
    PASSWORD_ERROR = 30003

    # ===== 角色 / 聊天 =====
    CHARACTER_NOT_FOUND = 40001
    CHAT_FORBIDDEN = 40002
    NOT_FOUND = 40004
    SERVICE_ERROR = 40005
    LIKE_FAILED = 40006
    UNLIKE_FAILED = 40007
    INTERNAL_ERROR = 40008
    # ===== AI / 系统 =====
    MODEL_ERROR = 50001
    RATE_LIMIT = 50002

