"""
Typed Image Generation Models

Provides type-safe image model configurations for agent image generation.
"""

from enum import Enum
from pydantic import BaseModel, Field, ConfigDict


class ImageProvider(str, Enum):
    """Image generation providers"""
    GOOGLE = "Google"
    OPENAI = "OpenAI"


class ImageModelConfig(BaseModel):
    """Configuration for image generation model"""

    model: str = Field(..., description="Image model name")
    credential_id: str = Field(..., description="Credential ID")
    provider: ImageProvider = Field(..., description="Provider")

    model_config = ConfigDict(frozen=True)


# ============================================================================
# Google Gemini Image Models
# ============================================================================

class Gemini:
    """Google Gemini image generation models"""

    PRO = ImageModelConfig(
        model="gemini/gemini-3-pro-image-preview",
        credential_id="lyzr_google",
        provider=ImageProvider.GOOGLE
    )

    FLASH = ImageModelConfig(
        model="gemini/gemini-2.5-flash-image",
        credential_id="lyzr_google",
        provider=ImageProvider.GOOGLE
    )


# ============================================================================
# OpenAI DALL-E Image Models
# ============================================================================

class DallE:
    """OpenAI DALL-E and GPT image generation models"""

    DALL_E_3 = ImageModelConfig(
        model="dall-e-3",
        credential_id="lyzr_openai",
        provider=ImageProvider.OPENAI
    )

    DALL_E_2 = ImageModelConfig(
        model="dall-e-2",
        credential_id="lyzr_openai",
        provider=ImageProvider.OPENAI
    )

    GPT_IMAGE_1 = ImageModelConfig(
        model="gpt-image-1",
        credential_id="lyzr_openai",
        provider=ImageProvider.OPENAI
    )

    GPT_IMAGE_1_5 = ImageModelConfig(
        model="gpt-image-1.5",
        credential_id="lyzr_openai",
        provider=ImageProvider.OPENAI
    )
