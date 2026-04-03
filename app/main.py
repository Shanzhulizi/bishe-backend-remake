import asyncio
import platform
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles

from app.api.v1 import auth, characters, chat, conversation, voice, character_like, recommend, category, tag
from app.core.config import settings
from app.core.logging import setup_logging
from app.tasks.update_popularity import start_scheduler, stop_scheduler

if platform.system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


#-------------------------------------------------------------

# 1. 获取当前 Python 环境下的 torch lib 路径
import torch,os
torch_lib_path = os.path.join(os.path.dirname(torch.__file__), 'lib')

# 2. 将该路径添加到系统 PATH 的最前面 (Windows 关键步骤)
os.environ['PATH'] = torch_lib_path + os.pathsep + os.environ.get('PATH', '')


#-------------------------------------------------------------

# 启动日志
setup_logging()


# 定时任务
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时执行

    try:

        from app.services.ars_service import ASRService
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, ASRService._get_model_sync)
        print("✅ ASR 模型预加载完成")
    except Exception as e:
        print(f"⚠️ ASR 模型预加载失败: {e}")

    # print("🚀 应用启动中...")
    start_scheduler()
    yield
    # 关闭时执行
    print("🛑 应用关闭中...")
    stop_scheduler()

    # 清理 ASR 线程池
    try:
        from app.services.ars_service import ASRService
        await ASRService.close()
    except:
        pass

app = FastAPI(
    title="AI角色扮演聊天平台",
    description="基于FastAPI和Vue3的AI角色扮演聊天网站",
    lifespan=lifespan, # 定时任务的开关
    version="1.0.0"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 关键：挂载静态文件服务
# 将 /static 路径映射到项目的 static 目录
static_path = Path(__file__).parent.parent / "static"
app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# 注册路由
app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
# app.include_router(users.router, prefix="/api/users", tags=["用户"])
app.include_router(characters.router, prefix="/api/characters", tags=["角色"])
app.include_router(chat.router, prefix="/api/chat", tags=["聊天"])
app.include_router(conversation.router, prefix="/api/conversation", tags=["对话"])
app.include_router(voice.router, prefix="/api/voice", tags=["语音"])
app.include_router(character_like.router, prefix="/api/character-like", tags=["角色点赞"])
app.include_router(recommend.router, prefix="/api/recommend", tags=["推荐接口"])
app.include_router(category.router, prefix="/api/category", tags=["角色类别"]   )
app.include_router(tag.router, prefix="/api/tag", tags=["角色标签"])

@app.get("/")
async def root():
    return {"message": "AI角色扮演聊天平台API"}


# @app.onmodel()_event("startup")
# async def startup_event():
    # ASRService.get_  # 预加载模型

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        # reload=True,
        loop="asyncio"  # 关键参数
    )
