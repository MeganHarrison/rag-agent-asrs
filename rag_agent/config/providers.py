"""Model providers for Semantic Search Agent with retry logic."""

from typing import Optional
import time
import logging
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.models.openai import OpenAIModel
from .settings import load_settings

logger = logging.getLogger(__name__)


def get_llm_model(model_choice: Optional[str] = None, max_retries: int = 3) -> OpenAIModel:
    """
    Get LLM model configuration with retry logic.
    Supports any OpenAI-compatible API provider.
    
    Args:
        model_choice: Optional override for model choice
        max_retries: Maximum number of connection attempts
    
    Returns:
        Configured OpenAI-compatible model
    """
    settings = load_settings()
    
    llm_choice = model_choice or settings.llm_model
    base_url = settings.llm_base_url
    api_key = settings.llm_api_key
    
    # Retry logic with exponential backoff
    for attempt in range(max_retries):
        try:
            # Create provider based on configuration
            provider = OpenAIProvider(base_url=base_url, api_key=api_key)
            model = OpenAIModel(llm_choice, provider=provider)
            
            if attempt > 0:
                logger.info(f"Successfully connected to LLM provider after {attempt + 1} attempts")
            
            return model
            
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                logger.warning(f"Failed to connect to LLM provider (attempt {attempt + 1}/{max_retries}): {e}")
                logger.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                logger.error(f"Failed to connect to LLM provider after {max_retries} attempts: {e}")
                raise


def get_embedding_model() -> OpenAIModel:
    """
    Get embedding model configuration.
    Uses OpenAI embeddings API (or compatible provider).
    
    Returns:
        Configured embedding model
    """
    settings = load_settings()
    
    # For embeddings, use the same provider configuration
    provider = OpenAIProvider(
        base_url=settings.llm_base_url, 
        api_key=settings.llm_api_key
    )
    
    return OpenAIModel(settings.embedding_model, provider=provider)


def get_model_info() -> dict:
    """
    Get information about current model configuration.
    
    Returns:
        Dictionary with model configuration info
    """
    settings = load_settings()
    
    return {
        "llm_provider": settings.llm_provider,
        "llm_model": settings.llm_model,
        "llm_base_url": settings.llm_base_url,
        "embedding_model": settings.embedding_model,
    }


def validate_llm_configuration() -> bool:
    """
    Validate that LLM configuration is properly set.
    Uses lazy validation to avoid blocking startup.
    
    Returns:
        True if configuration is valid
    """
    try:
        settings = load_settings()
        # Just check if required settings exist, don't actually connect
        has_config = bool(settings.llm_api_key and settings.llm_model)
        if has_config:
            logger.info("LLM configuration appears valid (not tested)")
        else:
            logger.warning("LLM configuration incomplete")
        return has_config
    except Exception as e:
        logger.error(f"LLM configuration validation failed: {e}")
        return False