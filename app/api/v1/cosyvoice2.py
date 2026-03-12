
# from fastapi import APIRouter
#
# from app.core.logging import get_logger

# router = APIRouter()
# logger = get_logger(__name__)


#
#
# router.get("/voices/{voice_id}", summary="获取声音详情")
# async def get_voice(voice_id: str):
#     """获取单个声音的详细信息"""
#     voice = VoiceDB.get_voice(voice_id)
#     if not voice:
#         raise HTTPException(status_code=404, detail="声音不存在")
#
#     # 获取这个声音生成的所有音频
#     generated = GeneratedAudioDB.list_by_voice(voice_id)
#
#     return {
#         "voice": voice.to_dict(),
#         "generated_count": len(generated),
#         "recent_generations": [g.to_dict() for g in generated[:5]]
#     }
#
#
# router.delete("/voices/{voice_id}", summary="删除声音")
# async def delete_voice(voice_id: str):
#     """删除声音（同时删除音频文件）"""
#     success = VoiceDB.delete_voice(voice_id)
#     if not success:
#         raise HTTPException(status_code=404, detail="声音不存在")
#
#     return {"success": True, "message": "声音已删除"}
