"""
Knowledge Base indexer for AiCippy.

Manages S3 storage and Bedrock Knowledge Base indexing.
"""

from __future__ import annotations

import asyncio
import json
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import boto3
from botocore.config import Config

from aicippy.config import get_settings
from aicippy.knowledge.summarizer import SummarizedContent
from aicippy.utils.logging import get_logger
from aicippy.utils.retry import async_retry

logger = get_logger(__name__)


@dataclass
class IndexedDocument:
    """A document indexed in the Knowledge Base."""

    document_id: str
    source: str
    title: str
    s3_key: str
    indexed_at: datetime
    metadata: dict[str, Any]


class KnowledgeIndexer:
    """
    Indexer for managing Knowledge Base content.

    Handles:
    - S3 storage of documents
    - Knowledge Base data source syncing
    - Document metadata management
    """

    def __init__(self) -> None:
        """Initialize the indexer."""
        self._settings = get_settings()
        self._s3_client = None
        self._bedrock_agent_client = None
        self._dynamodb = None

    def _get_s3_client(self):
        """Get or create S3 client."""
        if self._s3_client is None:
            config = Config(retries={"max_attempts": 3, "mode": "adaptive"})
            self._s3_client = boto3.client(
                "s3",
                region_name=self._settings.aws_region,
                config=config,
            )
        return self._s3_client

    def _get_bedrock_agent_client(self):
        """Get or create Bedrock Agent client."""
        if self._bedrock_agent_client is None:
            config = Config(retries={"max_attempts": 3, "mode": "adaptive"})
            self._bedrock_agent_client = boto3.client(
                "bedrock-agent",
                region_name=self._settings.aws_region,
                config=config,
            )
        return self._bedrock_agent_client

    def _get_dynamodb(self):
        """Get or create DynamoDB resource."""
        if self._dynamodb is None:
            self._dynamodb = boto3.resource(
                "dynamodb",
                region_name=self._settings.aws_region,
            )
        return self._dynamodb

    async def index_documents(
        self,
        documents: list[SummarizedContent],
    ) -> list[IndexedDocument]:
        """
        Index summarized documents into the Knowledge Base.

        Args:
            documents: List of summarized content to index.

        Returns:
            List of indexed documents.
        """
        logger.info("indexing_started", document_count=len(documents))

        indexed: list[IndexedDocument] = []

        for doc in documents:
            try:
                indexed_doc = await self._index_single_document(doc)
                indexed.append(indexed_doc)
            except Exception as e:
                logger.warning(
                    "document_indexing_failed",
                    title=doc.original_item.title[:50],
                    error=str(e),
                )

        # Trigger Knowledge Base sync
        await self._trigger_kb_sync()

        logger.info("indexing_completed", indexed_count=len(indexed))
        return indexed

    @async_retry(max_attempts=3, min_wait=1.0)
    async def _index_single_document(
        self,
        doc: SummarizedContent,
    ) -> IndexedDocument:
        """
        Index a single document.

        Args:
            doc: Summarized content to index.

        Returns:
            Indexed document record.
        """
        document_id = str(uuid.uuid4())
        timestamp = datetime.utcnow()

        # Build document content for S3
        document_content = {
            "title": doc.original_item.title,
            "source": doc.original_item.source,
            "link": doc.original_item.link,
            "published": doc.original_item.published.isoformat()
            if doc.original_item.published
            else None,
            "summary": doc.summary,
            "key_points": doc.key_points,
            "categories": doc.categories,
            "original_content": doc.original_item.content[:10000],
            "indexed_at": timestamp.isoformat(),
        }

        # Upload to S3
        s3_key = f"documents/{timestamp.strftime('%Y/%m/%d')}/{document_id}.json"

        s3_client = self._get_s3_client()
        loop = asyncio.get_event_loop()

        await loop.run_in_executor(
            None,
            lambda: s3_client.put_object(
                Bucket=self._settings.s3_knowledge_bucket,
                Key=s3_key,
                Body=json.dumps(document_content, indent=2),
                ContentType="application/json",
                Metadata={
                    "source": doc.original_item.source,
                    "document_id": document_id,
                },
            ),
        )

        # Store metadata in DynamoDB
        dynamodb = self._get_dynamodb()
        table = dynamodb.Table(self._settings.dynamodb_knowledge_metadata_table)

        await loop.run_in_executor(
            None,
            lambda: table.put_item(
                Item={
                    "source_id": f"{doc.original_item.source}#{doc.original_item.link}",
                    "version": timestamp.isoformat(),
                    "document_id": document_id,
                    "title": doc.original_item.title,
                    "s3_key": s3_key,
                    "categories": doc.categories,
                    "indexed_at": timestamp.isoformat(),
                }
            ),
        )

        return IndexedDocument(
            document_id=document_id,
            source=doc.original_item.source,
            title=doc.original_item.title,
            s3_key=s3_key,
            indexed_at=timestamp,
            metadata={
                "categories": doc.categories,
                "key_points": doc.key_points,
            },
        )

    async def _trigger_kb_sync(self) -> None:
        """Trigger Knowledge Base data source sync."""
        # Note: This requires the Knowledge Base ID and data source ID
        # which would be retrieved from configuration or SSM Parameter Store
        logger.info("kb_sync_triggered")

        # Example of how to trigger sync (commented as it requires actual KB IDs)
        # bedrock = self._get_bedrock_agent_client()
        # loop = asyncio.get_event_loop()
        # await loop.run_in_executor(
        #     None,
        #     lambda: bedrock.start_ingestion_job(
        #         knowledgeBaseId="your-kb-id",
        #         dataSourceId="your-data-source-id",
        #     ),
        # )

    async def search(
        self,
        query: str,
        max_results: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Search the Knowledge Base.

        Args:
            query: Search query.
            max_results: Maximum results to return.

        Returns:
            List of matching documents.
        """
        # Note: This would use the Bedrock Agent Runtime RetrieveAndGenerate
        # or Retrieve API to search the Knowledge Base

        logger.info("kb_search", query=query[:50], max_results=max_results)

        # Placeholder - actual implementation would query Bedrock KB
        return []

    async def delete_document(self, document_id: str) -> bool:
        """
        Delete a document from the Knowledge Base.

        Args:
            document_id: Document ID to delete.

        Returns:
            True if deleted, False if not found.
        """
        logger.info("deleting_document", document_id=document_id)

        # Implementation would delete from S3 and DynamoDB
        # then trigger KB sync
        return True
