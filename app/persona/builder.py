from app.persona.tags import TAG_EFFECTS

BASE_PERSONA = {
    "traits": {
        "bravery": 0.5,
        "kindness": 0.5,
        "logic": 0.5,
        "emotionality": 0.5,
        "curiosity": 0.5,
        "discipline": 0.5,
        "confidence": 0.5,
        "flexibility": 0.5,
    },
    "memory_strategy": {
        "short_term_memory": 5,
        "long_term_memory": 50,
    },
    "dialogue_style": {
        "directness": 0.5,
        "verbosity": 0.5,
        "emotional_expressiveness": 0.5,
        "guidance_style": 0.5,
        "dialog_control": 0.5,
        "tolerance": 0.5,
    }
}


def clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


class PersonaBuilder:

    @staticmethod
    def apply_tags(tags: list[str]) -> dict:
        import copy

        persona = copy.deepcopy(BASE_PERSONA)

        for tag in tags:
            effects = TAG_EFFECTS.get(tag, {})
            for path, delta in effects.items():
                section, key = path.split(".")
                persona[section][key] += delta

        # clamp
        for section in ("traits", "dialogue_style"):
            for k, v in persona[section].items():
                persona[section][k] = round(min(1.0, max(0.0, v)), 2)

        persona["memory_strategy"]["short_term_memory"] = max(
            1, min(20, persona["memory_strategy"]["short_term_memory"])
        )
        persona["memory_strategy"]["long_term_memory"] = max(
            10, min(200, persona["memory_strategy"]["long_term_memory"])
        )

        return persona
