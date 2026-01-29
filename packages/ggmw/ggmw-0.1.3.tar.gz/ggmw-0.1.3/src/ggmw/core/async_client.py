from collections.abc import Iterable, AsyncIterator 

from google.genai import client, types
from pydantic import BaseModel 

from .message import Message, split_messages
from .exceptions import GeminiAPIError
from .types import ThinkingLevel
from .parse_fragment import parse_fragment 
from .partial import partial_model 

class AsyncClient:
    """Client for interact with Gemini API asynchronously

    Methods:
        `.text_run(...)`         : Generates whole text response   
        `.text_stream(...)`      : Streams text response chunk-by-chunk 
        `.structured_run(...)`   : Generates whole structured response 
        `.structured_stream(...)`: Streams structured response aggregately
    """
    def __init__(self, genai_client: client.Client, model: str):
        """Initializes the client.

        Args:
            `genai_client` (`google.genai.client.Client`): The Google Gemini client.
            `model` (`str`) : Model to use.
        """
        self._genai_client: client.Client = genai_client 
        self._model: str = model

    def _construct_config(
        self,
        system_messages: list[Message],
        thinking_level: ThinkingLevel | None = None,
        output_schema: type[BaseModel] | None = None,
        /
    ) -> types.GenerateContentConfig:
        """Constructs a `types.GenerateContentConfig` instance using the provided configuration.

        Args:
            `system_messages` (`list[Message]`): List of system instruction messages.
            `thinking_level` (`Literal[str] | None`, optional): The level of reasoning effort to apply.
            `output_schema` (`type[BaseModel] | None`, optional): The Pydantic model for structured response generation.

        Returns:
            `types.GenerateContentConfig`: The constructed configuration object.
        """

        config = types.GenerateContentConfig(
            system_instruction=[
                msg.to_gemini_part()
                for msg in system_messages
            ],
        )

        if thinking_level is not None:
            config.thinking_config = types.ThinkingConfig(
                thinking_level=types.ThinkingLevel(thinking_level)
            )

        if output_schema is not None:
            config.response_mime_type = "application/json"
            config.response_json_schema = output_schema.model_json_schema()

        return config

    async def text_run(
        self,
        msgs: Iterable[Message],
        thinking_level: ThinkingLevel | None = None,  
    ) -> str:
        """Generates the complete text response. 

        Sends the provided messages to the Gemini API in order.
        Then retrieves the response, and extracts the resulting text content.

        Args:
            `msgs` (`Iterable[Message]`): The messages to send to the model.
            `thinking_level` (`Literal[str] | None`, optional): The level of reasoning effort the model 
                should apply. Defaults to `None` for models that do not support thinking.
        Returns:
            `str`: The complete text response.
        Raises:
            `GeminiAPIError`: If the Gemini API fails to generate a response.
        """       
        system_messages, normal_messages = split_messages(msgs)
        
        config = self._construct_config(system_messages, thinking_level)    

        response = await self._genai_client.aio.models.generate_content(  # pyright: ignore[reportUnknownMemberType]
            model=self._model,
            contents=[
                msg.to_gemini_part()
                for msg in normal_messages
            ],
            config=config
        )
        
        response_text = response.text
        if response_text is None:
            raise GeminiAPIError(f"No response were produced by the model")
        
        return response_text
    
    async def text_stream(
        self,
        msgs: Iterable[Message],
        thinking_level: ThinkingLevel | None = None,  
    ) -> AsyncIterator[str]:
        """Streams the text response chunk-by-chunk. 

        Sends the provided messages to the Gemini API in order and yields the resulting text chunks
        as they arrive.

        Args:
            `msgs` (`Iterable[Message]`): The messages to send to the model.
            `thinking_level` (`Literal[str] | None`, optional): The level of reasoning effort the model 
                should apply. Defaults to `None` for models that do not support thinking.
        Returns:
            `AsyncIterator[str]`: An iterator over the streaming text chunks.
        Raises:
            `GeminiAPIError`: If the Gemini API fails to generate a response.
        """       
        system_messages, normal_messages = split_messages(msgs)
        
        config = self._construct_config(system_messages, thinking_level)    
        iterator = await self._genai_client.aio.models.generate_content_stream(  # pyright: ignore[reportUnknownMemberType]
            model=self._model,
            contents=[
                msg.to_gemini_part()
                for msg in normal_messages
            ],
            config=config
        )
        async for chunk in iterator: 
            if chunk.text is None:
                raise GeminiAPIError(f"No response were produced by the model")

            yield chunk.text 
    
    async def structured_run(
        self, 
        msgs: Iterable[Message],
        output_schema: type[BaseModel], 
        thinking_level: ThinkingLevel | None = None,
    ) -> BaseModel:
        """Generates the complete structured response. 

        Sends the provided messages to the Gemini API in order, with the `output_schema` 
        configure as the generation schema in the Gemini API config. 
        Then retrieves the structured text response (JSON string), and loads it to the `output_schema`.

        Args:
            `msgs` (`Iterable[Message]`): The messages to send to the model.
            `output_schema` (`type[BaseModel]`): The pydantic model for structured response 
            `thinking_level` (`Literal[str] | None`, optional): The level of reasoning effort the model 
                should apply. Defaults to `None` for models that do not support thinking.

        Returns:
            `BaseModel`: The structured output. 

        Raises:
            `GeminiAPIError`: If the Gemini API fails to generate a response.
            `MalformedJSON`: If the model produces invalid JSON string.
            `pydantic.ValidationError`: If produced JSON does not conform to the provided schema.
        """
        system_messages, normal_messages = split_messages(msgs)
        
        config = self._construct_config(system_messages, thinking_level, output_schema) 
    
        response = await self._genai_client.aio.models.generate_content(  # pyright: ignore[reportUnknownMemberType]
            model=self._model,
            contents=[
                msg.to_gemini_part()
                for msg in normal_messages
            ],
            config=config
        )
        
        if response.text is None:
            raise GeminiAPIError(f"No response were produced by the model")

        return parse_fragment(response.text, output_schema) 

    async def structured_stream(
        self, 
        msgs: Iterable[Message],
        output_schema: type[BaseModel], 
        thinking_level: ThinkingLevel | None = None,
    ) -> AsyncIterator[BaseModel]:
        """Streams the structured response in an aggregated manner.

        Sends the provided messages to the Gemini API in order and configures `output_schema`
        as the generation schema in the Gemini API configuration. 
        It then concatenates the streaming text-chunk responses, attempts to fix the JSON, 
        loads the fixed JSON into a partial version of `output_schema`, and yields the result.

        The partial version of `output_schema` is another Pydantic model identical to `output_schema`,
        but all fields are optional, allowing it to load incomplete JSON fragments.

        Notice: Since it uses a partial version of `output_schema` to handle incomplete JSON fragments,
        it is the caller's responsibility to validate the final output against `output_schema`.

        Args:
            `msgs` (`Iterable[Message]`): The messages to send to the model.
            `output_schema` (`type[BaseModel]`): The Pydantic model for the structured response.
            `thinking_level` (`Literal[str] | None`, optional): The level of reasoning effort the model
                should apply. Defaults to `None` for models that do not support thinking.

        Returns:
            `AsyncIterator[BaseModel]`: An iterator over the partially loaded data.

        Raises:
            `GeminiAPIError`: If the Gemini API fails to generate a response.
            `MalformedJSON`: If the model produces invalid JSON strings.
            `pydantic.ValidationError`: If the produced JSON does not conform to the provided schema.
        """

        system_messages, normal_messages = split_messages(msgs)
        
        config = self._construct_config(system_messages, thinking_level, output_schema) 
    
        iterator = await self._genai_client.aio.models.generate_content_stream(  # pyright: ignore[reportUnknownMemberType]
            model=self._model,
            contents=[
                msg.to_gemini_part()
                for msg in normal_messages
            ],
            config=config
        )
        aggregate_text = ""
        PartialOutputSchema = partial_model(output_schema)
        async for chunk in iterator: 
            if chunk.text is None:
                raise GeminiAPIError(f"No response were produced by the model")

            aggregate_text += chunk.text

            parsed_json_fragment = parse_fragment(aggregate_text, PartialOutputSchema)
            
            yield parsed_json_fragment 
