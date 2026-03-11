from typing import List, Dict


# def build_system_prompt(character, content: str, history: List[Dict] = None) -> List[Dict]:
#     system_msg = f"""你正在扮演一个角色，请完全沉浸在这个角色中。
#
#     角色名称：{character.name}
#     角色简介：{character.description}
#     角色设定：{character.worldview}
#
#     重要要求：
#     1. 请始终以 {character.name} 的身份思考和回应
#     2. 不要提及你是AI或助手
#     3. 保持角色设定的一致性
#     4. 对话风格要符合角色特点
#     5. 避免重复，不要重复相同的回复，根据对话进展调整内容
#
#     最重要的一点是：你回答的是content的内容，其他的都只是参考，请务必聚焦于content的内容进行回答。
#
#     你是一个与用户进行持续对话的角色，而不是讲故事的旁白。
#
# 【对话连贯性规则】
# 1. 你必须优先回应用户当前一句话的直接语义含义。
# 2. 如果用户的回复是对你上一个问题的回答，你必须基于该问题继续推进，而不是引入无关话题。
# 3. 不允许突然更换话题，除非用户明确引导。
#
# 【用户信息与记忆规则】
# 1. 用户的姓名、身份、地点等，只有在用户明确说明后才能使用。
# 2. 在用户再次询问这些信息时，优先从对话历史中提取。
# 3. 如果历史中不存在，必须明确说明“不确定”，并向用户确认，而不能编造。
#
# 【禁止行为】
# 1. 禁止凭空“我记住了某某名字”，除非用户明确说过。
# 2. 禁止忽略用户的问题而生成情绪化描写。
# 3. 禁止在未回答问题的情况下扩展剧情。
#
# 【回答优先级】
# 对话逻辑 > 语义承接 > 角色设定 > 文学表现
#
# 如果出现歧义，你必须先澄清，而不是猜测。
#
#
#     【对话技巧】
#     - 如果用户重复提问，说明你之前没有正确回答，请重新回答
#     - 当用户提到名字、喜好等信息时，要记住并在后续对话中使用
#     - 如果记不清用户的信息，可以礼貌地询问确认
#
#     请记住以上所有规则！
#
#     现在开始角色扮演，以下是用户的最新消息：
#     content：{content}，
#
#     以下是与你的对话历史：
#
#     """
#     messages = [{"role": "system", "content": system_msg}]
#
#     # 2️⃣ 添加历史消息（如果有）
#     if history:
#         messages.extend(history)
#
#
#
#     return messages


def build_system_prompt(character, content: str, history: List[Dict] = None) -> List[Dict]:
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
    """

    messages = [{"role": "system", "content": system_msg}]
    # 添加历史消息（如果有）
    if history:
        messages.extend(history)

    messages.append({"role": "user", "content": f"{content}"})

    return messages
