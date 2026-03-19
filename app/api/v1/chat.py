import asyncio

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.deps import get_current_user
from app.api.deps import get_db
from app.core.logging import get_logger
from app.schemas.chat import ChatRequest
from app.services.chat_service import ChatService

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


# TODO 需要添加伦理审查，在审查发现有问题时，能在前端把生成的内容变为”不好意思，无法生成“
# TODO 还需要添加情感分析，在生成回复之前就做，把情感加入提示词中，提升回复的质量
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

# TODO 这是将来可能做的语音通话，别给删了
#
# @router.post("/voice")
# async def voice_chat(
#     character_id: int= Form(...),
#     audio: UploadFile = File(...),
#     user=Depends(get_current_user),
#     db=Depends(get_db)
# ):
#     # 1. ASR
#     audio_bytes = await audio.read()
#     logger.info(f"用户 {user.id} 发送语音消息给角色 {character_id}")
#     logger.info(f"语音文件大小: {len(audio_bytes)} 字节")
#     logger.info(f"语音文件: {audio_bytes[:20]}...")
#     try:
#         user_text, _ = await ASRService.speech_to_text(audio_bytes)
#     except Exception as e:
#         print("ASR 失败", e)
#         return {
#             "user_text": "",
#             "reply_text": "抱歉，我的语音识别暂时无法使用，请稍后再试",
#             "audio_url": None
#         }
#     logger.info(f"ASR 识别结果: {user_text}")
#     # 2. 聊天（你现有逻辑）
#     reply_text = await ChatService.send_message(
#         db=db,  # 这里接你真实 db
#         user_id=user.id,
#         #     user_id=1,  # 临时用一个固定用户 ID
#         character_id=character_id,
#         content=user_text
#     )
#     logger.info(f"角色 {character_id} 回复用户 {user.id} 消息: {reply_text}")
#     # 3. TTS
#     # audio_url = await TTSService.text_to_speech(
#     #     text=reply_text,
#     #     character_id=character_id
#     # )
#
#     try:
#         audio_url = await TTSService.text_to_speech(
#             text=reply_text,
#             character_id=character_id
#         )
#     except Exception as e:
#         logger.error(f"TTS 失败: {e}")
#         audio_url = None
#
#     logger.info(f"TTS 生成语音 URL: {audio_url}")
#     return {
#         "user_text": user_text,
#         "reply_text": reply_text,
#         "audio_url": audio_url
#     }
