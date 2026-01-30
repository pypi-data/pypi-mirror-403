from typing import Optional, List, Literal
from pydantic import BaseModel, Field


class EmbeddingConfig:
    DEFAULT_MODEL = "doubao-embedding-vision-251215"
    DEFAULT_ENCODING_FORMAT = "float"
    MAX_BATCH_SIZE = 100


class EmbeddingInputImageURL(BaseModel):
    url: str = Field(..., description="Image URL")


class EmbeddingInputVideoURL(BaseModel):
    url: str = Field(..., description="Video URL")


class EmbeddingInputItem(BaseModel):
    type: Literal["text", "image_url", "video_url"] = Field(..., description="Input type")
    text: Optional[str] = Field(default=None, description="Text content for embedding")
    image_url: Optional[EmbeddingInputImageURL] = Field(default=None, description="Image URL for embedding")
    video_url: Optional[EmbeddingInputVideoURL] = Field(default=None, description="Video URL for embedding")


class MultiEmbeddingConfig(BaseModel):
    type: Literal["enabled", "disabled"] = Field(default="disabled", description="Multi embedding mode")


class SparseEmbeddingConfig(BaseModel):
    type: Literal["enabled", "disabled"] = Field(default="disabled", description="Sparse embedding mode")


class SparseEmbeddingItem(BaseModel):
    index: int = Field(..., description="Token index")
    value: float = Field(..., description="Token weight value")


class PromptTokensDetails(BaseModel):
    image_tokens: int = Field(default=0, description="Number of image tokens")
    text_tokens: int = Field(default=0, description="Number of text tokens")


class EmbeddingUsage(BaseModel):
    prompt_tokens: int = Field(default=0, description="Number of prompt tokens")
    prompt_tokens_details: Optional[PromptTokensDetails] = Field(default=None, description="Token details breakdown")
    total_tokens: int = Field(default=0, description="Total number of tokens")


class EmbeddingData(BaseModel):
    object: str = Field(default="embedding", description="Object type")
    embedding: Optional[List[float]] = Field(default=None, description="Embedding vector")
    multi_embedding: Optional[List[List[float]]] = Field(default=None, description="Multi embedding vectors")
    sparse_embedding: Optional[List[SparseEmbeddingItem]] = Field(default=None, description="Sparse embedding")
    index: int = Field(default=0, description="Index of the embedding in the batch")


class EmbeddingRequest(BaseModel):
    model: str = Field(default=EmbeddingConfig.DEFAULT_MODEL, description="Model ID for embedding")
    input: List[EmbeddingInputItem] = Field(..., description="List of inputs to embed")
    dimensions: Optional[int] = Field(default=None, description="Output embedding dimensions")
    encoding_format: Optional[Literal["float", "base64"]] = Field(default=None, description="Encoding format")
    instructions: Optional[str] = Field(default=None, description="Instructions for embedding")
    multi_embedding: Optional[MultiEmbeddingConfig] = Field(default=None, description="Multi embedding config")
    sparse_embedding: Optional[SparseEmbeddingConfig] = Field(default=None, description="Sparse embedding config")

    def to_api_request(self) -> dict:
        request_data = {
            "model": self.model,
            "input": []
        }
        for item in self.input:
            item_dict = {"type": item.type}
            if item.text is not None:
                item_dict["text"] = item.text
            if item.image_url is not None:
                item_dict["image_url"] = {"url": item.image_url.url}
            if item.video_url is not None:
                item_dict["video_url"] = {"url": item.video_url.url}
            request_data["input"].append(item_dict)

        if self.dimensions is not None:
            request_data["dimensions"] = self.dimensions
        if self.encoding_format is not None:
            request_data["encoding_format"] = self.encoding_format
        if self.instructions is not None:
            request_data["instructions"] = self.instructions
        if self.multi_embedding is not None:
            request_data["multi_embedding"] = {"type": self.multi_embedding.type}
        if self.sparse_embedding is not None:
            request_data["sparse_embedding"] = {"type": self.sparse_embedding.type}
        return request_data


class EmbeddingResponse(BaseModel):
    object: str = Field(default="list", description="Response object type")
    data: Optional[EmbeddingData] = Field(default=None, description="Embedding result")
    model: str = Field(default="", description="Model used for embedding")
    usage: Optional[EmbeddingUsage] = Field(default=None, description="Token usage information")
    id: Optional[str] = Field(default=None, description="Response ID")
    created: Optional[int] = Field(default=None, description="Creation timestamp")
    error: Optional[dict] = Field(default=None, description="Error information if any")

    @property
    def success(self) -> bool:
        return self.error is None and self.data is not None

    @property
    def embedding(self) -> Optional[List[float]]:
        if self.data and self.data.embedding:
            return self.data.embedding
        return None

    @property
    def multi_embeddings(self) -> Optional[List[List[float]]]:
        if self.data and self.data.multi_embedding:
            return self.data.multi_embedding
        return None

    @property
    def sparse_embeddings(self) -> Optional[List[SparseEmbeddingItem]]:
        if self.data and self.data.sparse_embedding:
            return self.data.sparse_embedding
        return None

    @property
    def error_message(self) -> Optional[str]:
        if self.error:
            return self.error.get("message", "Unknown error")
        return None
