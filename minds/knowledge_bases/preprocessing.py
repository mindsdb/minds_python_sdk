from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, model_validator


DEFAULT_LLM_MODEL = 'gpt-4o'
DEFAULT_LLM_MODEL_PROVIDER = 'openai'


class TextChunkingConfig(BaseModel):
    '''Configuration for chunking text content before they are inserted into a knowledge base'''
    separators: List[str] = Field(
        default=['\n\n', '\n', ' ', ''],
        description='List of separators to use for splitting text, in order of priority'
    )
    chunk_size: int = Field(
        default=1000,
        description='The target size of each text chunk',
        gt=0
    )
    chunk_overlap: int = Field(
        default=200,
        description='The number of characters to overlap between chunks',
        ge=0
    )


class LLMConfig(BaseModel):
    model_name: str = Field(default=DEFAULT_LLM_MODEL, description='LLM model to use for context generation')
    provider: str = Field(default=DEFAULT_LLM_MODEL_PROVIDER, description='LLM model provider to use for context generation')
    params: Dict[str, Any] = Field(default={}, description='Additional parameters to pass in when initializing the LLM')


class ContextualConfig(BaseModel):
    '''Configuration specific to contextual preprocessing'''
    llm_config: LLMConfig = Field(
        default=LLMConfig(),
        description='LLM configuration to use for context generation'
    )
    context_template: Optional[str] = Field(
        default=None,
        description='Custom template for context generation'
    )
    chunk_size: int = Field(
        default=1000,
        description='The target size of each text chunk',
        gt=0
    )
    chunk_overlap: int = Field(
        default=200,
        description='The number of characters to overlap between chunks',
        ge=0
    )


class PreprocessingConfig(BaseModel):
    '''Complete preprocessing configuration'''
    type: Literal['contextual', 'text_chunking'] = Field(
        default='text_chunking',
        description='Type of preprocessing to apply'
    )
    contextual_config: Optional[ContextualConfig] = Field(
        default=None,
        description='Configuration for contextual preprocessing'
    )
    text_chunking_config: Optional[TextChunkingConfig] = Field(
        default=None,
        description='Configuration for text chunking preprocessing'
    )

    @model_validator(mode='after')
    def validate_config_presence(self) -> 'PreprocessingConfig':
        '''Ensure the appropriate config is present for the chosen type'''
        if self.type == 'contextual' and not self.contextual_config:
            self.contextual_config = ContextualConfig()
        if self.type == 'text_chunking' and not self.text_chunking_config:
            self.text_chunking_config = TextChunkingConfig()
        return self
