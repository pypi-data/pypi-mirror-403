"""
Content summarizer for knowledge ingestion.

Uses Bedrock Titan for generating summaries of crawled content.
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass

import boto3
from botocore.config import Config

from aicippy.config import get_settings
from aicippy.knowledge.crawler import FeedItem
from aicippy.utils.logging import get_logger
from aicippy.utils.retry import async_retry

logger = get_logger(__name__)


@dataclass
class SummarizedContent:
    """Summarized content ready for indexing."""

    original_item: FeedItem
    summary: str
    key_points: list[str]
    categories: list[str]
    embedding_text: str


class ContentSummarizer:
    """
    Summarizer for feed content using Bedrock.

    Uses Amazon Titan for text generation and embeddings.
    """

    def __init__(
        self,
        model_id: str = "amazon.titan-text-express-v1",
        max_concurrent: int = 5,
    ) -> None:
        """
        Initialize the summarizer.

        Args:
            model_id: Bedrock model ID for summarization.
            max_concurrent: Maximum concurrent API calls.
        """
        self._settings = get_settings()
        self._model_id = model_id
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._client = None

    def _get_client(self):
        """Get or create Bedrock client."""
        if self._client is None:
            config = Config(
                retries={"max_attempts": 3, "mode": "adaptive"},
                read_timeout=60,
            )
            self._client = boto3.client(
                "bedrock-runtime",
                region_name=self._settings.aws_region,
                config=config,
            )
        return self._client

    async def summarize_all(self, items: list[FeedItem]) -> list[SummarizedContent]:
        """
        Summarize all feed items.

        Args:
            items: List of feed items to summarize.

        Returns:
            List of summarized content.
        """
        logger.info("summarization_started", item_count=len(items))

        tasks = [self._summarize_item(item) for item in items]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        summarized: list[SummarizedContent] = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.warning(
                    "summarization_failed",
                    item=items[i].title[:50],
                    error=str(result),
                )
            elif result:
                summarized.append(result)

        logger.info("summarization_completed", success_count=len(summarized))
        return summarized

    @async_retry(max_attempts=3, min_wait=1.0)
    async def _summarize_item(self, item: FeedItem) -> SummarizedContent:
        """
        Summarize a single feed item.

        Args:
            item: Feed item to summarize.

        Returns:
            Summarized content.
        """
        async with self._semaphore:
            # Build prompt
            prompt = f"""Summarize the following content and extract key information.

Title: {item.title}
Source: {item.source}
Content:
{item.content[:4000]}

Provide:
1. A concise 2-3 sentence summary
2. Key points (3-5 bullet points)
3. Categories (e.g., aws, gcp, security, release, feature)

Format your response as JSON:
{{
    "summary": "...",
    "key_points": ["...", "..."],
    "categories": ["...", "..."]
}}
"""

            # Call Bedrock
            client = self._get_client()

            body = {
                "inputText": prompt,
                "textGenerationConfig": {
                    "maxTokenCount": 1024,
                    "temperature": 0.3,
                    "topP": 0.9,
                },
            }

            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: client.invoke_model(
                    modelId=self._model_id,
                    body=json.dumps(body),
                    contentType="application/json",
                    accept="application/json",
                ),
            )

            result = json.loads(response["body"].read())
            output_text = result.get("results", [{}])[0].get("outputText", "")

            # Parse JSON response
            try:
                # Extract JSON from response
                json_start = output_text.find("{")
                json_end = output_text.rfind("}") + 1
                if json_start >= 0 and json_end > json_start:
                    parsed = json.loads(output_text[json_start:json_end])
                else:
                    parsed = {
                        "summary": output_text[:500],
                        "key_points": [],
                        "categories": [],
                    }
            except json.JSONDecodeError:
                parsed = {
                    "summary": output_text[:500],
                    "key_points": [],
                    "categories": [],
                }

            # Build embedding text (combination of title, summary, key points)
            embedding_text = f"{item.title}\n{parsed.get('summary', '')}\n"
            embedding_text += " ".join(parsed.get("key_points", []))

            return SummarizedContent(
                original_item=item,
                summary=parsed.get("summary", ""),
                key_points=parsed.get("key_points", []),
                categories=parsed.get("categories", []),
                embedding_text=embedding_text,
            )

    @async_retry(max_attempts=3, min_wait=1.0)
    async def generate_embedding(
        self,
        text: str,
        model_id: str = "amazon.titan-embed-text-v1",
    ) -> list[float]:
        """
        Generate embedding vector for text.

        Args:
            text: Text to embed.
            model_id: Embedding model ID.

        Returns:
            Embedding vector.
        """
        client = self._get_client()

        body = {"inputText": text[:8000]}  # Limit input length

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: client.invoke_model(
                modelId=model_id,
                body=json.dumps(body),
                contentType="application/json",
                accept="application/json",
            ),
        )

        result = json.loads(response["body"].read())
        return result.get("embedding", [])
