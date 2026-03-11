# app/ai/base.py
from abc import ABC, abstractmethod


class BaseLLM(ABC):
    @abstractmethod
    async def generate(self, prompt: str):
        pass

    @abstractmethod
    async def stream(self, prompt: str):
        pass
