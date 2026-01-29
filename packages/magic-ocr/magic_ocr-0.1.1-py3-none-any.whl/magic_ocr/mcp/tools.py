"""MCP OCR tools."""

from __future__ import annotations

import copy
import logging
from typing import Optional, Union, List, Tuple

from ..utils import read_image_file, decode_base64_image, detect_image_input_type
from ..config import get_config
from ..prompts import PromptMode
from .. import get_ocr_client

logger = logging.getLogger(__name__)


async def _load_image(image: str) -> Tuple[bytes, str]:
    """Load image from file path or base64 and return (bytes, mime_type)."""
    input_type = detect_image_input_type(image)
    logger.info(f"Loading image, detected type: {input_type}")

    if input_type == "url":
        # For URLs in multi-image mode, download first
        import httpx
        from ..utils import get_mime_type
        async with httpx.AsyncClient(follow_redirects=True, timeout=15.0) as http_client:
            response = await http_client.get(image)
            response.raise_for_status()
        image_bytes = response.content
        mime_type = response.headers.get("content-type", "").split(";", 1)[0].strip()
        if not mime_type.startswith("image/"):
            mime_type = get_mime_type(image_bytes)
        return image_bytes, mime_type
    elif input_type == "file_path":
        return read_image_file(image)
    else:  # base64
        return decode_base64_image(image)


async def ocr_image(
    image: Union[str, List[str]],
    provider: Optional[str] = None,
    model: Optional[str] = None,
    mode: Optional[str] = None,
    system_prompt: Optional[str] = None,
    user_prompt: Optional[str] = None,
) -> str:
    """Extract text from image (file/URL/base64).

    Args:
        image: Absolute file path (e.g., /Users/name/image.png), URL (https://...),
            or base64 string. Prefer absolute path or URL over base64.
            Do NOT use relative paths.
            Can also be a list of images to process in a single context.
        provider: OCR provider ('gemini', 'openai', 'gcp')
        model: Model name (e.g., 'gemini-3-flash-preview', 'gpt-4o')
        mode: Output mode ('plain' or 'markdown')
        system_prompt: Custom system prompt
        user_prompt: Custom user prompt

    Returns:
        Extracted text from all images combined.

    Note:
        All optional parameters have optimized defaults.
        Only override when user explicitly requests a specific value.
    """
    logger.info("OCR request")

    try:
        # Normalize to list and validate
        images = [image] if isinstance(image, str) else list(image)
        if not images:
            raise ValueError("At least one image is required")

        # Load config and create a copy to avoid modifying global state
        config = copy.copy(get_config())

        # mode: map to PromptMode, default 'plain'
        if mode is not None:
            m = mode.strip().lower()
            if m in ("plain", "plaintext"):
                config.prompt_mode = PromptMode.PLAINTEXT
            elif m == "markdown":
                config.prompt_mode = PromptMode.MARKDOWN
            else:
                logger.warning(f"Invalid mode: {mode}, using default 'plain'")
                config.prompt_mode = PromptMode.PLAINTEXT

        # optional prompt overrides
        if system_prompt is not None:
            config.system_prompt = system_prompt
        if user_prompt is not None:
            config.user_prompt = user_prompt

        client = get_ocr_client(provider=provider, config=config, model=model)
        logger.info(f"Using {client.provider_name} OCR with model: {client.model_name}")

        if len(images) == 1:
            # Single image: use native URL support when available
            img = images[0]
            input_type = detect_image_input_type(img)

            if input_type == "url":
                text = await client.extract_text_from_url(img)
            elif input_type == "file_path":
                image_bytes, mime_type = read_image_file(img)
                text = await client.extract_text(image_bytes, mime_type)
            else:  # base64
                image_bytes, mime_type = decode_base64_image(img)
                text = await client.extract_text(image_bytes, mime_type)
        else:
            # Multiple images: load all and send in single context
            logger.info(f"Loading {len(images)} images for multi-image OCR")
            loaded_images = []
            for img in images:
                image_bytes, mime_type = await _load_image(img)
                loaded_images.append((image_bytes, mime_type))
            text = await client.extract_text_multi(loaded_images)

        logger.info(f"OCR completed: {len(text)} characters extracted")
        return text

    except Exception as e:
        logger.error(f"OCR failed: {str(e)}")
        raise
