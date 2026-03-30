import asyncio

from fastapi import APIRouter, Depends, Form, File, UploadFile
from fastapi.responses import StreamingResponse

from app.api.deps import get_current_user
from app.api.deps import get_db
from app.core.logging import get_logger
from app.db.session import SessionLocal
from app.schemas.chat import ChatRequest
from app.services.ars_service import ASRService
from app.services.character_service import CharacterService
from app.services.chat_service import ChatService
from app.services.gpt_covits_service import GptCovitsService
from app.services.voice_service import VoiceService

router = APIRouter()

logger = get_logger(__name__)


# @router.post("/send", response_model=ChatResponse)
# async def send_chat(
#         req: ChatRequest,
#         db=Depends(get_db),
#         user=Depends(get_current_user)
# ):
#     service = ChatService(db)
#     logger.info(f"用户 {user.id} 发送文字消息给角色 {req.character_id}")
#     reply = await service.send_message(
#         db=db,
#         user_id=user.id,
#         character_id=req.character_id,
#         content=req.message,
#     )
#     logger.info(f"角色 {req.character_id} 回复用户 {user.id} 消息")
#     return {"reply": reply
#             }


@router.post("/stream")
async def send_chat_stream(
        req: ChatRequest,
        db=Depends(get_db),
        user=Depends(get_current_user)
):
    async def generator():
        service = ChatService(db)
        error_occurred = False
        error_message = ""
        try:
            # service = ChatService(db)
            async for token in service.send_message_stream(
                    db=db,
                    user_id=user.id,
                    character_id=req.character_id,
                    content=req.message
            ):
                # logger.info(f"发送chunk: {token[:20]}...")

                yield token
                # 🔥 强制让出事件循环，确保数据被发送
                await asyncio.sleep(0.0001)
            logger.info("流式请求成功完成")
        except Exception as e:
            logger.info(f"流式请求发生错误: {e}")
            yield f"\n\n[连接中断: {str(e)}]"

    return StreamingResponse(
        generator(),
        media_type="text/plain; charset=utf-8",
        headers={
            "Cache-Control": "no-cache, no-transform",  # 🔥 禁止转换
            "Connection": "keep-alive",
            "Content-Type": "text/plain; charset=utf-8",
            "X-Accel-Buffering": "no",  # 🔥 禁用 Nginx 缓冲
            "Transfer-Encoding": "chunked",
        }
    )


"""
    播放文本的语音
"""


# @router.post("/tts")
# async def tts(
#     req: TTSRequest
# ):
#
#     audio_url = await TTSService.text_to_speech(
#         text=req.text,
#         character_id=req.character_id,
#         # voice_style=req.voice_style
#         voice_code=req.voice_code
#     )
#
#     return {
#         "audio_url": audio_url
#     }
#



@router.post("/voice_chat")
async def voice_chat(
        character_id: int = Form(...),
        audio: UploadFile = File(...),
        user=Depends(get_current_user),
        db=Depends(get_db)
):
    # 1. ASR
    audio_bytes = await audio.read()
    logger.info(f"用户 {user.id} 发送语音消息给角色 {character_id}")
    logger.info(f"语音文件大小: {len(audio_bytes)} 字节")
    logger.info(f"语音文件: {audio_bytes[:20]}...")
    try:
        user_text, _ = await ASRService.speech_to_text(audio_bytes)
    except Exception as e:
        print("ASR 失败", e)
        return {
            "user_text": "",
            "reply_text": "抱歉，我的语音识别暂时无法使用，请稍后再试",
            "audio_url": None
        }
    logger.info(f"ASR 识别结果: {user_text}")
    # 2. 聊天（你现有逻辑）
    chat_service = ChatService(db)
    # 收集所有回复片段
    reply_buffer = ""
    try:
        async for token in chat_service.send_message_stream(
                db=db,
                user_id=user.id,
                character_id=character_id,
                content=user_text
        ):
            reply_buffer += token
            # 可以在这里做流式处理（如果 WebSocket 的话）

        reply_text = reply_buffer
        logger.info(f"角色 {character_id} 回复用户 {user.id}: {reply_text[:100]}...")

    except Exception as e:
        logger.error(f"聊天服务失败: {e}")
        reply_text = "抱歉，AI 服务暂时不可用，请稍后再试"


    logger.info(f"角色 {character_id} 回复用户 {user.id} 消息: {reply_text}")
    # 3. TTS
    try:
        character_service = CharacterService(db)
        character = character_service.get_character(character_id)
        voice_id = character.voice_id if character else None
        gpt_covits_service = GptCovitsService(db)
        logger.info(f"使用角色 {character_id} 的 voice_id {voice_id} 进行 TTS")
        audio_url = gpt_covits_service.generate_voice(
            text=reply_text,
            voice_id=voice_id
        )
    except Exception as e:
        logger.error(f"TTS 失败: {e}")
        audio_url = None

    logger.info(f"TTS 生成语音 URL: {audio_url}")
    return {
        "user_text": user_text,
        "reply_text": reply_text,
        "audio_url": audio_url
    }
