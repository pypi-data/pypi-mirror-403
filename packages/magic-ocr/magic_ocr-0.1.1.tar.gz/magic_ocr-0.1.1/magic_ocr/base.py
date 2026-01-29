"""Base OCR client interface."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Optional, List, Tuple
from .config import Config
from .prompts import PromptTemplate


class OCRClientError(Exception):
    """Base exception for OCR client errors."""
    pass


logger = logging.getLogger(__name__)


class BaseOCRClient(ABC):
    """Abstract base class for OCR client implementations."""

    def __init__(self, config: Config):
        """Initialize OCR client with configuration.

        Args:
            config: Configuration instance
        """
        self.config = config
        self.user_prompt = self._build_user_prompt()
        self.system_prompt = self._build_system_prompt()

    def _build_user_prompt(self) -> str:
        """Build user prompt based on configuration."""
        if self.config.user_prompt:
            return self.config.user_prompt
        return PromptTemplate.get_user_prompt(self.config.prompt_mode)

    def _build_system_prompt(self) -> Optional[str]:
        """Build system prompt based on configuration."""
        if self.config.system_prompt:
            return self.config.system_prompt
        return PromptTemplate.get_system_prompt(self.config.prompt_mode)

    async def extract_text(self, image_bytes: bytes, mime_type: str) -> str:
        """Extract text from image using template method pattern.

        Args:
            image_bytes: Image data as bytes
            mime_type: MIME type (e.g., 'image/png')

        Returns:
            Extracted text

        Raises:
            OCRClientError: If OCR fails
        """
        logger.debug(f"Processing {mime_type}: {len(image_bytes)} bytes")

        try:
            response = await self._call_api(image_bytes, mime_type)
            text = self._extract_response_text(response)

            logger.info(f"OCR completed: {len(text)} characters extracted")
            return text.strip()

        except OCRClientError:
            raise
        except Exception as e:
            logger.error(f"OCR failed: {e}")
            raise

    async def extract_text_multi(self, images: list[tuple[bytes, str]]) -> str:
        """Extract text from multiple images in a single API call.

        Args:
            images: List of (image_bytes, mime_type) tuples

        Returns:
            Extracted text from all images combined

        Raises:
            OCRClientError: If OCR fails
        """
        if len(images) == 1:
            return await self.extract_text(images[0][0], images[0][1])

        logger.debug(f"Processing {len(images)} images in single context")

        try:
            response = await self._call_api_multi(images)
            text = self._extract_response_text(response)

            logger.info(f"Multi-image OCR completed: {len(text)} characters extracted")
            return text.strip()

        except OCRClientError:
            raise
        except Exception as e:
            logger.error(f"Multi-image OCR failed: {e}")
            raise

    @abstractmethod
    async def _call_api(self, image_bytes: bytes, mime_type: str):
        """Call provider-specific API. Implemented by subclasses."""
        pass

    async def _call_api_multi(self, images: list[tuple[bytes, str]]):
        """Call provider-specific API with multiple images. Override in subclasses."""
        raise NotImplementedError(f"{self.provider_name} does not support multi-image OCR")

    @abstractmethod
    def _extract_response_text(self, response) -> str:
        """Extract text from API response. Implemented by subclasses."""
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the name of the OCR provider."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return the model name being used."""
        pass
