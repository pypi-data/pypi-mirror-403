import asyncio
from typing import Optional, List, Dict
from cozeloop.decorator import observe
from coze_coding_utils.runtime_ctx.context import Context

from ..core.client import BaseClient
from ..core.config import Config
from ..core.exceptions import APIError, ValidationError
from .models import (
    EmbeddingConfig,
    EmbeddingInputItem,
    EmbeddingInputImageURL,
    EmbeddingInputVideoURL,
    EmbeddingRequest,
    EmbeddingResponse,
    EmbeddingData,
    EmbeddingUsage,
    MultiEmbeddingConfig,
    SparseEmbeddingConfig,
    SparseEmbeddingItem,
)


class EmbeddingClient(BaseClient):
    def __init__(
        self,
        config: Optional[Config] = None,
        ctx: Optional[Context] = None,
        custom_headers: Optional[Dict[str, str]] = None,
        verbose: bool = False,
    ):
        super().__init__(config, ctx, custom_headers, verbose)
        self.base_url = self.config.base_url
        self.model = EmbeddingConfig.DEFAULT_MODEL

    def _validate_inputs(
        self,
        texts: Optional[List[str]],
        image_urls: Optional[List[str]],
        video_urls: Optional[List[str]] = None
    ) -> None:
        has_texts = texts is not None and len(texts) > 0
        has_images = image_urls is not None and len(image_urls) > 0
        has_videos = video_urls is not None and len(video_urls) > 0

        if not has_texts and not has_images and not has_videos:
            raise ValidationError(
                "At least one of texts, image_urls, or video_urls must be provided",
                field="input"
            )

        total_inputs = 0
        if texts:
            total_inputs += len(texts)
        if image_urls:
            total_inputs += len(image_urls)
        if video_urls:
            total_inputs += len(video_urls)

        if total_inputs > EmbeddingConfig.MAX_BATCH_SIZE:
            raise ValidationError(
                f"Total inputs exceed maximum batch size of {EmbeddingConfig.MAX_BATCH_SIZE}",
                field="input",
                value=total_inputs
            )

    def _build_input_items(
        self,
        texts: Optional[List[str]],
        image_urls: Optional[List[str]],
        video_urls: Optional[List[str]] = None
    ) -> List[EmbeddingInputItem]:
        items = []
        if texts:
            for text in texts:
                if text and text.strip():
                    items.append(EmbeddingInputItem(type="text", text=text))
        if image_urls:
            for url in image_urls:
                if url and url.strip():
                    items.append(EmbeddingInputItem(
                        type="image_url",
                        image_url=EmbeddingInputImageURL(url=url)
                    ))
        if video_urls:
            for url in video_urls:
                if url and url.strip():
                    items.append(EmbeddingInputItem(
                        type="video_url",
                        video_url=EmbeddingInputVideoURL(url=url)
                    ))
        return items

    @observe
    def embed(
        self,
        texts: Optional[List[str]] = None,
        image_urls: Optional[List[str]] = None,
        video_urls: Optional[List[str]] = None,
        model: Optional[str] = None,
        dimensions: Optional[int] = None,
        encoding_format: Optional[str] = None,
        instructions: Optional[str] = None,
        multi_embedding: bool = False,
        sparse_embedding: bool = False
    ) -> EmbeddingResponse:
        self._validate_inputs(texts, image_urls, video_urls)

        input_items = self._build_input_items(texts, image_urls, video_urls)
        if not input_items:
            raise ValidationError("No valid input provided", field="input")

        request = EmbeddingRequest(
            model=model or self.model,
            input=input_items,
            dimensions=dimensions,
            encoding_format=encoding_format,
            instructions=instructions,
            multi_embedding=MultiEmbeddingConfig(type="enabled") if multi_embedding else None,
            sparse_embedding=SparseEmbeddingConfig(type="enabled") if sparse_embedding else None
        )

        data = self._request(
            method="POST",
            url=f"{self.base_url}/api/v3/embeddings/multimodal",
            json=request.to_api_request()
        )

        if "error" in data and data["error"]:
            raise APIError(
                f"API returned error: {data['error'].get('message', 'Unknown error')}",
                code=data['error'].get('code')
            )

        return EmbeddingResponse(**data)

    @observe
    def embed_text(
        self,
        text: str,
        model: Optional[str] = None,
        dimensions: Optional[int] = None,
        instructions: Optional[str] = None
    ) -> List[float]:
        response = self.embed(
            texts=[text],
            model=model,
            dimensions=dimensions,
            instructions=instructions
        )
        if response.embedding:
            return response.embedding
        raise APIError("No embedding returned")

    @observe
    def embed_texts(
        self,
        texts: List[str],
        model: Optional[str] = None,
        dimensions: Optional[int] = None,
        instructions: Optional[str] = None
    ) -> List[float]:
        response = self.embed(
            texts=texts,
            model=model,
            dimensions=dimensions,
            instructions=instructions
        )
        if response.embedding:
            return response.embedding
        raise APIError("No embedding returned")

    @observe
    def embed_image(
        self,
        image_url: str,
        model: Optional[str] = None,
        dimensions: Optional[int] = None
    ) -> List[float]:
        response = self.embed(
            image_urls=[image_url],
            model=model,
            dimensions=dimensions
        )
        if response.embedding:
            return response.embedding
        raise APIError("No embedding returned")

    @observe
    def embed_images(
        self,
        image_urls: List[str],
        model: Optional[str] = None,
        dimensions: Optional[int] = None
    ) -> List[float]:
        response = self.embed(
            image_urls=image_urls,
            model=model,
            dimensions=dimensions
        )
        if response.embedding:
            return response.embedding
        raise APIError("No embedding returned")

    @observe
    def embed_video(
        self,
        video_url: str,
        model: Optional[str] = None,
        dimensions: Optional[int] = None
    ) -> List[float]:
        response = self.embed(
            video_urls=[video_url],
            model=model,
            dimensions=dimensions
        )
        if response.embedding:
            return response.embedding
        raise APIError("No embedding returned")

    @observe
    def embed_videos(
        self,
        video_urls: List[str],
        model: Optional[str] = None,
        dimensions: Optional[int] = None
    ) -> List[float]:
        response = self.embed(
            video_urls=video_urls,
            model=model,
            dimensions=dimensions
        )
        if response.embedding:
            return response.embedding
        raise APIError("No embedding returned")

    @observe
    def embed_multimodal(
        self,
        texts: Optional[List[str]] = None,
        image_urls: Optional[List[str]] = None,
        video_urls: Optional[List[str]] = None,
        model: Optional[str] = None,
        dimensions: Optional[int] = None,
        instructions: Optional[str] = None,
        multi_embedding: bool = False,
        sparse_embedding: bool = False
    ) -> EmbeddingResponse:
        return self.embed(
            texts=texts,
            image_urls=image_urls,
            video_urls=video_urls,
            model=model,
            dimensions=dimensions,
            instructions=instructions,
            multi_embedding=multi_embedding,
            sparse_embedding=sparse_embedding
        )

    @observe
    def embed_with_multi_vectors(
        self,
        texts: Optional[List[str]] = None,
        image_urls: Optional[List[str]] = None,
        video_urls: Optional[List[str]] = None,
        model: Optional[str] = None,
        dimensions: Optional[int] = None,
        instructions: Optional[str] = None
    ) -> Optional[List[List[float]]]:
        response = self.embed(
            texts=texts,
            image_urls=image_urls,
            video_urls=video_urls,
            model=model,
            dimensions=dimensions,
            instructions=instructions,
            multi_embedding=True
        )
        return response.multi_embeddings

    @observe
    def embed_with_sparse(
        self,
        texts: Optional[List[str]] = None,
        image_urls: Optional[List[str]] = None,
        video_urls: Optional[List[str]] = None,
        model: Optional[str] = None,
        dimensions: Optional[int] = None,
        instructions: Optional[str] = None
    ) -> Optional[List[SparseEmbeddingItem]]:
        response = self.embed(
            texts=texts,
            image_urls=image_urls,
            video_urls=video_urls,
            model=model,
            dimensions=dimensions,
            instructions=instructions,
            sparse_embedding=True
        )
        return response.sparse_embeddings

    async def embed_async(
        self,
        texts: Optional[List[str]] = None,
        image_urls: Optional[List[str]] = None,
        video_urls: Optional[List[str]] = None,
        model: Optional[str] = None,
        dimensions: Optional[int] = None,
        encoding_format: Optional[str] = None,
        instructions: Optional[str] = None,
        multi_embedding: bool = False,
        sparse_embedding: bool = False
    ) -> EmbeddingResponse:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.embed(
                texts=texts,
                image_urls=image_urls,
                video_urls=video_urls,
                model=model,
                dimensions=dimensions,
                encoding_format=encoding_format,
                instructions=instructions,
                multi_embedding=multi_embedding,
                sparse_embedding=sparse_embedding
            )
        )

    async def batch_embed(
        self,
        text_batches: List[List[str]],
        model: Optional[str] = None,
        dimensions: Optional[int] = None,
        instructions: Optional[str] = None,
        max_concurrent: int = 5
    ) -> List[EmbeddingResponse]:
        semaphore = asyncio.Semaphore(max_concurrent)

        async def _embed_with_semaphore(texts: List[str]) -> EmbeddingResponse:
            async with semaphore:
                return await self.embed_async(
                    texts=texts,
                    model=model,
                    dimensions=dimensions,
                    instructions=instructions
                )

        tasks = [_embed_with_semaphore(batch) for batch in text_batches]
        return await asyncio.gather(*tasks, return_exceptions=False)
