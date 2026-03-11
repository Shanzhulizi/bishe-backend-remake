backend/ ├── app/ │ ├── __init__.py │ ├── main.py # FastAPI应用入口 │ ├── core/ │ │ ├── __init__.py │ │ ├── config.py # 配置文件
│ │ └── security.py # 安全相关 │ ├── models/ │ │ ├── __init__.py │ │ ├── user.py # 用户模型 │ │ └── character.py # 角色模型 │ ├──
schemas/ │ │ ├── __init__.py │ │ ├── user.py # 用户Pydantic模型 │ │ └── chat.py # 聊天相关模型 │ ├── api/ │ │ ├── __init__.py │ │
├── endpoints/ │ │ │ ├── __init__.py │ │ │ ├── auth.py # 认证接口 │ │ │ ├── users.py # 用户接口 │ │ │ ├── characters.py # 角色接口 │
│ │ └── chat.py # 聊天接口 │ │ └── deps.py # 依赖注入 │ ├── services/ │ │ ├── __init__.py │ │ ├── auth.py # 认证服务 │ │ ├──
chat_service.py # 聊天核心服务 │ │ └── llm_client.py # LLM客户端 │ └── database/ │ ├── __init__.py │ └── session.py # 数据库会话 ├──
requirements.txt ├── Dockerfile └── README.md