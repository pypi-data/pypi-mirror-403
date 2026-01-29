from typing import Any
from collections.abc import Iterator, AsyncIterator

from unittest.mock import Mock
from google.genai.types import (
    GenerateContentResponse,

)

def string_split(string_to_split: str) -> tuple[str, str, str]:
    """Split a string into 3 parts""" 

    n = len(string_to_split)
    split1 = n // 3
    split2 = 2 * n // 3

    # Slice into 3 parts
    part1 = string_to_split[:split1]
    part2 = string_to_split[split1:split2]
    part3 = string_to_split[split2:]

    return part1, part2, part3


class MockModels:
    def __init__(self, response_text: str | None):
        self.response_text: str | None = response_text

    def generate_content(
        self, 
        *args: Any, **kwags: Any # pyright: ignore[reportUnusedParameter]
    ) -> GenerateContentResponse:
        mock_content = Mock(spec=GenerateContentResponse)
        mock_content.text = self.response_text

        return mock_content

    def generate_content_stream(
        self, 
        *args: Any, **kwags: Any # pyright: ignore[reportUnusedParameter]
    ) -> Iterator[GenerateContentResponse]:
        
        if self.response_text is None:
            mock_content = Mock(spec=GenerateContentResponse)
            mock_content.text = None 
            yield mock_content

        else:
            chunks: tuple[str, ...] = string_split(self.response_text)

            for chunk in chunks:
                mock_content = Mock(spec=GenerateContentResponse)
                mock_content.text = chunk 
                
                yield mock_content

class MockAsyncModels:
    def __init__(self, response_text: str | None):
        self.response_text: str | None = response_text

    async def generate_content(
        self, 
        *args: Any, **kwags: Any # pyright: ignore[reportUnusedParameter]
    ) -> GenerateContentResponse:
        mock_content = Mock(spec=GenerateContentResponse)
        mock_content.text = self.response_text

        return mock_content

    async def generate_content_stream(
        self,
        *args: Any, **kwargs: Any, # pyright: ignore[reportUnusedParameter]
    ) -> AsyncIterator[GenerateContentResponse]:

        async def _iterator() -> AsyncIterator[GenerateContentResponse]:
            if self.response_text is None:
                mock = Mock(spec=GenerateContentResponse)
                mock.text = None
                yield mock
            else:
                for chunk in string_split(self.response_text):
                    mock = Mock(spec=GenerateContentResponse)
                    mock.text = chunk
                    yield mock

        return _iterator()

class MockGenAIClient:
    def __init__(
        self, 
        mock_models: MockModels,
    ):
        self.mock_models: MockModels = mock_models 

    @property
    def models(self) -> MockModels:
        return self.mock_models

class MockGenAIAsyncClient:
    def __init__(
        self, 
        mock_async_models: MockAsyncModels
    ):
        self.mock_async_models: MockAsyncModels = mock_async_models
    
    @property
    def aio(self):
        return self

    @property
    def models(self) -> MockAsyncModels:
        return self.mock_async_models

