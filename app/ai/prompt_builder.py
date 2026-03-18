from typing import List, Dict

from app.services.emotion_service import emotion_service


async def build_system_prompt(character, content: str, history: List[Dict] = None) -> List[Dict]:
    # 情感分析逻辑

    emotion_result = await emotion_service.analyze_use_api(content)

    system_msg = f"""现在你正在扮演一个角色来服务用户，请完全沉浸在这个角色中。注意要与用户区分你我。

    角色名称：{character.name}，
    角色简介：{character.description}，
    角色设定：{character.worldview}。
    【重要规则】
    1. 记住之前的对话内容，保持连贯性
    2. 用符合角色性格的方式回应用户
    3. 在用户提及名字、喜好等信息时，要记住并在后续对话中使用
    4. 回复要自然流畅，不要重复同样的话
    5. 不要提及你是AI或助手
    6. 用户如果提及违背法律、伦理的内容，请礼貌地拒绝并引导回正常话题
    
    
    
    
    【当前用户状态】
    情绪：{emotion_result['emotion']}（置信度：{emotion_result['score']:.2f}）
    回应建议：{emotion_result['tone']}。
    请根据用户情绪调整回应方式，保持角色性格不变。
    
    """

    messages = [{"role": "system", "content": system_msg}]
    # 添加历史消息（如果有）
    if history:
        messages.extend(history)

    messages.append({"role": "user", "content": f"{content}"})

    return messages
