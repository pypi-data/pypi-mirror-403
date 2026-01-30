import os
from .llm import LLM
from enum import Enum
from typing import Iterator
import litellm

class Model(Enum):
    GPT_4_1_NANO = "gpt-4.1-nano"
    QWEN_TURBO_LATEST = "qwen-turbo-latest"
    QWEN_PLUS_LATEST = "qwen-plus-latest"
    QWEN_MAX_LATEST = "qwen-max-latest"
    DOUBO_SEED_1_6_250615 = "doubao-seed-1-6-250615"
    DOUBO_SEED_1_6_THINKING_250615 = "doubao-seed-1-6-thinking-250615"
    DOUBO_SEED_1_6_FLASH_250615 = "doubao-seed-1-6-flash-250615"
    DEEPSEEK_V3_250324 = "deepseek-v3-250324"
    AZURE_GPT_4O_MINI = "azure-gpt-4o-mini"
    GEMINI = "gemini-2.5-flash"

    def provider(self) -> str:
        if self.value.startswith("gpt"):
            return "openai"
        elif self.value.startswith("qwen"):
            return "dashscope"
        elif self.value.startswith("doubao"):
            return "doubao"
        elif self.value.startswith("deepseek"):
            return "deepseek"
        elif self.value.startswith("azure"):
            return "azure"
        elif self.value.startswith("gemini"):
            return "gemini"
        raise ValueError(f"Invalid model: {self.value}")

class SfLLM():
    def __init__(self, api_base: str, api_key: str) -> None:
        self.api_base = api_base
        self.api_key = api_key
        self.model_dict = {
            Model.GPT_4_1_NANO: "",
            Model.QWEN_TURBO_LATEST: "",
            Model.QWEN_PLUS_LATEST: "",
            Model.QWEN_MAX_LATEST: "",
            Model.DOUBO_SEED_1_6_250615: "",
            Model.DOUBO_SEED_1_6_THINKING_250615: "",
            Model.DOUBO_SEED_1_6_FLASH_250615: "",
            Model.DEEPSEEK_V3_250324: "openai/ark-deepseek-v3",
            Model.AZURE_GPT_4O_MINI: "",
            Model.GEMINI: "",
        }

    def set_model_dict(self, model_dict: dict[Model, str]) -> None:
        self.model_dict = model_dict

    def set_model(self, model: Model, value: str) -> None:
        self.model_dict[model] = value

    def set_api_base(self, api_base: str) -> None:
        self.api_base = api_base

    def set_api_key(self, api_key: str) -> None:
        self.api_key = api_key

    def __getattr__(self, name):
        fn = getattr(litellm, name)

        def wrapper(
            *,
            input: str | None = None,
            system_prompt: str | None = None,
            model: Model = Model.DEEPSEEK_V3_250324,
            **kwargs
        ):
            if input is not None:
                messages = []
                if system_prompt is not None:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": input})
                return fn(
                    model=self.model_dict[model],
                    messages=messages,
                    api_base=self.api_base,
                    api_key=self.api_key,
                    **kwargs
                )
            else:
                return fn(
                    model=self.model_dict[model],
                    api_base=self.api_base,
                    api_key=self.api_key,
                    **kwargs
                )
        return wrapper

_llm_dicts = {}

def get_model(model: str) -> Model:
    if model in Model.__members__:
        return Model[model]

    model = model.upper().replace("-", "_")
    if model in Model.__members__:
        return Model[model]

    raise ValueError(f"Invalid model: {model}")
            
def get_llm(provider: str) -> LLM:
    if provider not in _llm_dicts:
        if provider == "openai":
            _llm_dicts[provider] = LLM(os.environ.get("OPENAI_API_KEY", ""), os.environ.get("OPENAI_BASE_URL", ""), int(os.environ.get("OPENAI_TIMEOUT", 2000)))
        elif provider == "doubao":
            _llm_dicts[provider] = LLM(os.environ.get("DOUBAO_API_KEY", ""), os.environ.get("DOUBAO_BASE_URL", ""), int(os.environ.get("DOUBAO_TIMEOUT", 2000)))
        elif provider == "dashscope":
            _llm_dicts[provider] = LLM(os.environ.get("DASHSCOPE_API_KEY", ""), os.environ.get("DASHSCOPE_BASE_URL", ""), int(os.environ.get("DASHSCOPE_TIMEOUT", 2000)))
        elif provider == "deepseek":
            _llm_dicts[provider] = LLM(os.environ.get("DEEPSEEK_API_KEY", ""), os.environ.get("DEEPSEEK_BASE_URL", ""), int(os.environ.get("DEEPSEEK_TIMEOUT", 2000)))
        elif provider == "azure":
            _llm_dicts[provider] = LLM(os.environ.get("AZURE_API_KEY", ""), os.environ.get("AZURE_BASE_URL", ""), int(os.environ.get("AZURE_TIMEOUT", 2000)), os.environ.get("AZURE_API_VERSION", ""))
        elif provider == "gemini":
            _llm_dicts[provider] = LLM(os.environ.get("GEMINI_API_KEY", ""), os.environ.get("GEMINI_BASE_URL", ""), int(os.environ.get("GEMINI_TIMEOUT", 2000)))
        else:
            raise ValueError(f"Invalid provider: {provider}")
    return _llm_dicts[provider]

def chat(input: str, system_prompt: str, model: Model, temperature: float) -> str:
    return get_llm(model.provider()).chat(input, system_prompt, model.value, temperature)

def chat_stream(input: str, system_prompt: str, model: Model, temperature: float) -> Iterator[str]:
    return get_llm(model.provider()).chat_stream(input, system_prompt, model.value, temperature)