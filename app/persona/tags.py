
# TODO 还会添加其它类型的标签，不会局限于性格

# # 1. 性格标签（已实现）- 影响人格参数
# PERSONALITY_TAGS = {
#     "勇敢": {"traits.bravery": 0.3, "traits.confidence": 0.2},
#     "温柔": {"traits.kindness": 0.3, "dialogue_style.tolerance": 0.3},
#     "理性": {"traits.logic": 0.4, "traits.emotionality": -0.3},
#     "幽默": {"dialogue_style.verbosity": 0.2, "traits.flexibility": 0.2},
# }
#
# # 2. 身份标签 - 影响 system prompt
# IDENTITY_TAGS = {
#     "老师": "你是一位有耐心的老师，善于用引导的方式回答问题",
#     "医生": "你是一位专业的医生，用温和专业的语气提供建议",
#     "朋友": "你像一位知心朋友，用亲切随和的语气聊天",
#     "前辈": "你是一位经验丰富的前辈，乐于分享经验",
# }
#
# # 3. 风格标签 - 影响对话风格
# STYLE_TAGS = {
#     "古风": "请用文言文或古风语言回答，多使用诗词典故",
#     "二次元": "请用二次元萌娘的语气，加上'喵~'、'的说'等语气词",
#     "学术": "请用严谨的学术语言，多引用专业术语和文献",
#     "童话": "请用童话故事的语气，像在讲述一个美好的故事",
# }
#
# # 4. 知识领域标签 - 影响知识范围
# DOMAIN_TAGS = {
#     "历史": ["历史事件", "人物", "年代"],
#     "科技": ["编程", "AI", "互联网"],
#     "文学": ["小说", "诗歌", "文学理论"],
#     "生活": ["美食", "旅游", "日常"],
# }
#
# # 5. 语气标签 - 影响情感表达
# TONE_TAGS = {
#     "活泼": 0.3,    # emotional_expressiveness +0.3
#     "严肃": -0.2,   # emotional_expressiveness -0.2
#     "热情": 0.4,    # emotional_expressiveness +0.4
#     "冷淡": -0.3,   # emotional_expressiveness -0.3
# }



TAG_EFFECTS = {
    "勇敢": {
        "traits.bravery": +0.3,
        "traits.confidence": +0.2,
        "dialogue_style.directness": +0.1,
    },
    "温柔": {
        "traits.kindness": +0.3,
        "dialogue_style.tolerance": +0.2,
        "dialogue_style.emotional_expressiveness": +0.1,
    },
    "理性": {
        "traits.logic": +0.3,
        "traits.emotionality": -0.2,
        "dialogue_style.emotional_expressiveness": -0.2,
    },
    "健谈": {
        "dialogue_style.verbosity": +0.3,
        "dialogue_style.directness": +0.1,
    },
    "话少精炼": {
        "dialogue_style.verbosity": -0.3,
        "dialogue_style.directness": +0.1,
    },
    "引导型": {
        "dialogue_style.guidance_style": +0.3,
        "dialogue_style.dialog_control": +0.2,
    },
    "陪伴型": {
        "traits.kindness": +0.2,
        "dialogue_style.tolerance": +0.2,
        "dialogue_style.guidance_style": -0.1,
    },
    "记忆力强": {
        "memory_strategy.long_term_memory": +30,
    },
    "健忘": {
        "memory_strategy.long_term_memory": -30,
    },
    "适应性强": {
        "traits.flexibility": +0.3,
    },
}
