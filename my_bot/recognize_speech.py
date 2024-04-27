import logging
from typing import Any

import torch
import whisper
from dotenv import load_dotenv

from utils.logger import get_logger

load_dotenv()

logger = get_logger("main")


VOICE_OUTPUT_FILE = "output.wav"
VOICE_INPUT_FILE = "input.ogg"



class AssistantAI:
    def __init__(self) -> None:
        # Инициализация модели распознавания голоса
        self._voice_recognition_model = whisper.load_model("small")
        # Инициализация модели текст в речь
        self._text_to_speech_model = self._init_tts_model_ru_model()
        # Словарь для отслеживания истории разговора для каждого пользователя
        self._current_talk_per_user = {}
        # Хранение предыдущей истории для каждого пользователя отключено по соображениям конфиденциальности
        self._use_previous_history_per_user = None

    @staticmethod
    def _init_tts_model_ru_model() -> torch.nn.Module:
        """Вспомогательная функция для инициализации модели TTS для русского языка"""
        language = "ru"
        model_id = "v3_1_ru"
        device = torch.device("cpu")

        model, example_text = torch.hub.load(
            repo_or_dir="snakers4/silero-models",
            model="silero_tts",
            language=language,
            speaker=model_id,
        )
        model.to(device)
        return model

    def create_response_from_voice(self, user_id: int) -> Any:
        # генерация текста из голоса пользователя с помощью модели Whisper Open AI
        text_from_user_voice = self._voice_recognition_model.transcribe(
            f"{str(user_id)}_{VOICE_INPUT_FILE}"
        )["text"]

        return text_from_user_voice

