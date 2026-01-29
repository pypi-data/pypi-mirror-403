import pytest
from pytest_mock import MockerFixture
from pydantic import BaseModel
import pydantic

from ..core import AsyncClient, Message, exceptions
from .genai_mock_client import MockAsyncModels, MockGenAIAsyncClient, string_split

"""
Async text response methods ---------------------------------------------------
These tests verify that async text-based responses work correctly for both successful
responses and error conditions, and that the underlying API methods are called
with the correct parameters.
"""

async def test_text_run_success():
    """Test that async text_run returns the expected text response."""
    response_text: str | None = "The model should response this text"

    genai_client = MockGenAIAsyncClient(
        MockAsyncModels(response_text)
    )
    client = AsyncClient(genai_client, "not-a-real-model") # pyright: ignore[reportArgumentType]

    res: str = await client.text_run([])
    assert res == response_text, f"Expected: {response_text}. Got: {res}"

async def test_text_run_model_failed_to_response():
    """Test that async text_run raises GeminiAPIError when model returns None."""
    response_text = None

    genai_client = MockGenAIAsyncClient(
        MockAsyncModels(response_text)
    )
    client = AsyncClient(genai_client, "not-a-real-model") # pyright: ignore[reportArgumentType]

    with pytest.raises(exceptions.GeminiAPIError):
        _ = await client.text_run([])

async def test_text_run_generate_content_call(mocker: MockerFixture):
    """Test that async text_run calls generate_content with correct parameters."""
    # Payloads to call the .text_run
    system_messages = [Message("system", "System message")]
    normal_messages = [Message("user", "User message"), Message("model", "Model message")]
    model: str = "not-a-real-model"

    genai_client = MockGenAIAsyncClient(MockAsyncModels(""))
    client = AsyncClient(genai_client, model) # pyright: ignore[reportArgumentType]

    mock_response = mocker.Mock()
    mock_response.text = "some response text"
    mock_generate_content = mocker.patch(
        'ggmw.tests.genai_mock_client.MockAsyncModels.generate_content', 
        return_value=mock_response
    )

    # Arguments for the .text_run method
    run_arg_messages = system_messages + normal_messages
    run_arg_thinking_level = "LOW"

    # Arguments that will be passed to the .generate_content method
    check_arg_model = model
    check_arg_contents = [msg.to_gemini_part() for msg in normal_messages]
    check_arg_config = client._construct_config(system_messages, run_arg_thinking_level) # pyright: ignore[reportPrivateUsage]

    _ = await client.text_run(run_arg_messages, run_arg_thinking_level)

    mock_generate_content.assert_called_once_with(
        model=check_arg_model,
        contents=check_arg_contents,
        config=check_arg_config
    )

async def test_text_stream_success():
    """Test that async text_stream yields the correct response chunks."""
    response_text: str = "The model should response this text"

    genai_client = MockGenAIAsyncClient(
        MockAsyncModels(response_text)
    )
    client = AsyncClient(genai_client, "not-a-real-model") # pyright: ignore[reportArgumentType]

    chunks = string_split(response_text)
    iterator = client.text_stream([])
    response_chunks: list[str] = []
    async for chunk in iterator:
        response_chunks.append(chunk)
    
    # Compare the result chunks with expected chunks
    assert response_chunks == list(chunks)

async def test_text_stream_model_failed_to_response():
    """Test that async text_stream raises GeminiAPIError when model returns None."""
    response_text = None

    genai_client = MockGenAIAsyncClient(
        MockAsyncModels(response_text)
    )
    client = AsyncClient(genai_client, "not-a-real-model") # pyright: ignore[reportArgumentType]

    with pytest.raises(exceptions.GeminiAPIError):
        iterator = client.text_stream([])
        async for _ in iterator:
            pass  # This will trigger the error when trying to get the first chunk

async def test_text_stream_generate_content_stream_call(mocker: MockerFixture):
    """Test that async text_stream calls generate_content_stream with correct parameters."""
    # Payloads to call the .text_stream
    system_messages = [Message("system", "System message")]
    normal_messages = [Message("user", "User message"), Message("model", "Model message")]
    model: str = "not-a-real-model"

    genai_client = MockGenAIAsyncClient(MockAsyncModels(""))
    client = AsyncClient(genai_client, model) # pyright: ignore[reportArgumentType]

    # Create a mock async generator
    mock_response1 = mocker.Mock()
    mock_response1.text = "chunk1"
    mock_response2 = mocker.Mock()
    mock_response2.text = "chunk2"
    mock_response3 = mocker.Mock()
    mock_response3.text = "chunk3"
    
    async def async_generator():
        yield mock_response1
        yield mock_response2
        yield mock_response3
    
    mock_generate_content_stream = mocker.patch('ggmw.tests.genai_mock_client.MockAsyncModels.generate_content_stream')
    mock_generate_content_stream.return_value = async_generator()

    # Arguments for the .text_stream method
    run_arg_messages = system_messages + normal_messages
    run_arg_thinking_level = "LOW"

    # Arguments that will be passed to the .generate_content_stream method
    check_arg_model = model
    check_arg_contents = [msg.to_gemini_part() for msg in normal_messages]
    check_arg_config = client._construct_config(system_messages, run_arg_thinking_level) # pyright: ignore[reportPrivateUsage]

    iterator = client.text_stream(run_arg_messages, run_arg_thinking_level)
    async for _ in iterator:
        pass

    mock_generate_content_stream.assert_called_once_with(
        model=check_arg_model,
        contents=check_arg_contents,
        config=check_arg_config
    )

"""
Async structured response methods ---------------------------------------------
These tests verify that async structured (JSON) responses are correctly parsed into
Pydantic models for both successful responses and error conditions.
"""

async def test_structured_run_success():
    """Test that async structured_run correctly parses JSON response into Pydantic model."""
    class ResponseSchema(BaseModel):
        a: int
        b: str
        c: bool

    response_text: str | None = '{"a": 42, "b": "hello world", "c": true}'

    genai_client = MockGenAIAsyncClient(
        MockAsyncModels(response_text)
    )
    client = AsyncClient(genai_client, "not-a-real-model") # pyright: ignore[reportArgumentType]

    res = await client.structured_run([], ResponseSchema)

    parsed_response = ResponseSchema.model_validate_json(response_text)

    assert res == parsed_response, f"Expected: {parsed_response}. Got: {res}"

async def test_structured_run_model_failed_to_response():
    """Test that async structured_run raises GeminiAPIError when model returns None."""
    class ResponseSchema(BaseModel):
        a: int
        b: str
        c: bool

    response_text = None

    genai_client = MockGenAIAsyncClient(
        MockAsyncModels(response_text)
    )
    client = AsyncClient(genai_client, "not-a-real-model") # pyright: ignore[reportArgumentType]

    with pytest.raises(exceptions.GeminiAPIError):
        _ = await client.structured_run([], ResponseSchema)

async def test_structured_run_model_produces_malformed_json():
    """Test that async structured_run raises MalformedJSON for invalid JSON."""
    class ResponseSchema(BaseModel):
        a: int
        b: str
        c: bool

    response_text = "this is not valid json string"

    genai_client = MockGenAIAsyncClient(
        MockAsyncModels(response_text)
    )
    client = AsyncClient(genai_client, "not-a-real-model") # pyright: ignore[reportArgumentType]

    with pytest.raises(exceptions.MalformedJSON):
        _ = await client.structured_run([], ResponseSchema)

async def test_structured_run_model_produces_incorrect_schema():
    """Test that async structured_run raises ValidationError for JSON that doesn't match schema."""
    class ResponseSchema(BaseModel):
        a: int
        b: str
        c: bool

    response_text = '{"wrong": "schema"}'

    genai_client = MockGenAIAsyncClient(
        MockAsyncModels(response_text)
    )
    client = AsyncClient(genai_client, "not-a-real-model") # pyright: ignore[reportArgumentType]

    with pytest.raises(pydantic.ValidationError):
        _ = await client.structured_run([], ResponseSchema)

async def test_structured_run_generate_content_call(mocker: MockerFixture):
    """Test that async structured_run calls generate_content with correct parameters."""
    class ResponseSchema(BaseModel):
        a: str
        b: int

    # Payloads to call the .structured_run
    system_messages = [Message("system", "System message")]
    normal_messages = [Message("user", "User message"), Message("model", "Model message")]
    model: str = "not-a-real-model"

    genai_client = MockGenAIAsyncClient(MockAsyncModels(""))
    client = AsyncClient(genai_client, model) # pyright: ignore[reportArgumentType]

    mock_response = mocker.Mock()
    mock_response.text = '{"a": "something", "b": 36}'
    mock_generate_content = mocker.patch('ggmw.tests.genai_mock_client.MockAsyncModels.generate_content',
                                        return_value=mock_response)

    # Arguments for the .structured_run method
    run_arg_messages = system_messages + normal_messages
    run_arg_thinking_level = "LOW"

    # Arguments that will be passed to the .generate_content method
    check_arg_model = model
    check_arg_contents = [msg.to_gemini_part() for msg in normal_messages]
    check_arg_config = client._construct_config( # pyright: ignore[reportPrivateUsage]
        system_messages,
        run_arg_thinking_level,
        ResponseSchema
    )

    _ = await client.structured_run(run_arg_messages, ResponseSchema, run_arg_thinking_level)

    mock_generate_content.assert_called_once_with(
        model=check_arg_model,
        contents=check_arg_contents,
        config=check_arg_config
    )

"""
Async structured stream methods -------------------------------------------------
These tests verify that async structured streaming responses work properly and handle
streaming edge cases correctly.
"""

async def test_structured_stream_success():
    """Test that async structured_stream correctly processes streaming JSON responses."""
    class ResponseSchema(BaseModel):
        a: int
        b: str
        c: bool

    response_text: str | None = '{"a": 42, "b": "hello world", "c": true}'

    genai_client = MockGenAIAsyncClient(
        MockAsyncModels(response_text)
    )
    client = AsyncClient(genai_client, "not-a-real-model") # pyright: ignore[reportArgumentType]

    chunks = string_split(response_text)
    aggregate_chunks = ""
    iterator = client.structured_stream([], ResponseSchema)
    idx = 0
    async for response_partial in iterator:
        if idx < len(chunks):
            check_chunk = chunks[idx]
            aggregate_chunks += check_chunk
            import partial_json_parser as pjp
            fixed_check_chunk = pjp.loads(aggregate_chunks)
            from ..core.partial import partial_model
            check_partial = partial_model(ResponseSchema).model_validate(fixed_check_chunk)

            assert response_partial == check_partial, f"Expected: {repr(check_partial)}. Got: {repr(response_partial)}"
            idx += 1

async def test_structured_stream_model_failed_to_response():
    """Test that async structured_stream raises GeminiAPIError when model returns None."""
    class ResponseSchema(BaseModel):
        a: int
        b: str
        c: bool

    response_text = None

    genai_client = MockGenAIAsyncClient(
        MockAsyncModels(response_text)
    )
    client = AsyncClient(genai_client, "not-a-real-model") # pyright: ignore[reportArgumentType]

    with pytest.raises(exceptions.GeminiAPIError):
        async for _ in client.structured_stream([], ResponseSchema):
            pass

async def test_structured_stream_model_produces_malformed_json():
    """Test that async structured_stream raises MalformedJSON for invalid JSON during streaming."""
    class ResponseSchema(BaseModel):
        a: int
        b: str
        c: bool

    response_text = "this is not valid json string"

    genai_client = MockGenAIAsyncClient(
        MockAsyncModels(response_text)
    )
    client = AsyncClient(genai_client, "not-a-real-model") # pyright: ignore[reportArgumentType]

    with pytest.raises(exceptions.MalformedJSON):
        async for _ in client.structured_stream([], ResponseSchema):
            pass

async def test_structured_stream_generate_content_call(mocker: MockerFixture):
    """Test that async structured_stream calls generate_content_stream with correct parameters."""
    class ResponseSchema(BaseModel):
        a: str
        b: int

    # Payloads to call the .structured_stream
    system_messages = [Message("system", "System message")]
    normal_messages = [Message("user", "User message"), Message("model", "Model message")]
    model: str = "not-a-real-model"

    genai_client = MockGenAIAsyncClient(MockAsyncModels('{"a": "test", "b": 42}'))
    client = AsyncClient(genai_client, model) # pyright: ignore[reportArgumentType]

    # Create mock responses for streaming
    mock_response1 = mocker.Mock()
    mock_response1.text = '{"a": "te'
    mock_response2 = mocker.Mock()
    mock_response2.text = 'st", "b": 42}'
    
    async def async_generator():
        yield mock_response1
        yield mock_response2
    
    mock_generate_content = mocker.patch('ggmw.tests.genai_mock_client.MockAsyncModels.generate_content_stream')
    mock_generate_content.return_value = async_generator()

    # Arguments for the .structured_stream method
    run_arg_messages = system_messages + normal_messages
    run_arg_thinking_level = "LOW"

    # Arguments that will be passed to the .generate_content_stream method
    check_arg_model = model
    check_arg_contents = [msg.to_gemini_part() for msg in normal_messages]
    check_arg_config = client._construct_config( # pyright: ignore[reportPrivateUsage]
        system_messages,
        run_arg_thinking_level,
        ResponseSchema
    )

    async for _ in client.structured_stream(run_arg_messages, ResponseSchema, run_arg_thinking_level):
        pass

    mock_generate_content.assert_called_once_with(
        model=check_arg_model,
        contents=check_arg_contents,
        config=check_arg_config
    )
