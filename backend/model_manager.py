from langchain_ollama import ChatOllama
from config import AVAILABLE_MODELS


def get_llm(model_name : str):
    
    if model_name not in AVAILABLE_MODELS:
        raise ValueError(f"Unknown Model : {model_name}")
    
    key = AVAILABLE_MODELS[model_name]
    
    return ChatOllama(
        model=key,
        temperature=0
    )