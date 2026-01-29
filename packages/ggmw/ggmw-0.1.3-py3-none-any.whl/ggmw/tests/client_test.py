import pytest
from pytest_mock import MockerFixture
from pydantic import BaseModel
import pydantic

from ..core import Client, Message, exceptions
from .genai_mock_client import MockModels, MockGenAIClient, string_split

"""
Text response methods ---------------------------------------------------------
These tests verify that text-based responses work correctly for both successful
responses and error conditions, and that the underlying API methods are called
with the correct parameters.
"""

def test_text_run_success():
    """Test that text_run returns the expected text response."""
    response_text: str | None = "The model should response this text"

    genai_client = MockGenAIClient(
        MockModels(response_text)
    )
    client = Client(genai_client, "not-a-real-model") # pyright: ignore[reportArgumentType]

    res: str = client.text_run([])
    assert res == response_text, f"Expected: {response_text}. Got: {res}"

def test_text_run_model_failed_to_response():
    """Test that text_run raises GeminiAPIError when model returns None."""
    response_text = None

    genai_client = MockGenAIClient(
        MockModels(response_text)
    )
    client = Client(genai_client, "not-a-real-model") # pyright: ignore[reportArgumentType]

    with pytest.raises(exceptions.GeminiAPIError):
        _ = client.text_run([])

def test_text_run_generate_content_call(mocker: MockerFixture):
    """Test that text_run calls generate_content with correct parameters."""
    # Payloads to call the .text_run
    system_messages = [Message("system", "System message")]
    normal_messages = [Message("user", "User message"), Message("model", "Model message")]
    model: str = "not-a-real-model"

    genai_client = MockGenAIClient(MockModels(""))
    client = Client(genai_client, model) # pyright: ignore[reportArgumentType]

    mock_generate_content = mocker.patch('ggmw.tests.genai_mock_client.MockModels.generate_content')

    # Arguments for the .text_run method
    run_arg_messages = system_messages + normal_messages
    run_arg_thinking_level = "LOW"

    # Arguments that will be passed to the .generate_content method
    check_arg_model = model
    check_arg_contents = [msg.to_gemini_part() for msg in normal_messages]
    check_arg_config = client._construct_config(system_messages, run_arg_thinking_level) # pyright: ignore[reportPrivateUsage]

    _ = client.text_run(run_arg_messages, run_arg_thinking_level)

    mock_generate_content.assert_called_once_with(
        model=check_arg_model,
        contents=check_arg_contents,
        config=check_arg_config
    )

def test_text_stream_success():
    """Test that text_stream yields the correct response chunks."""
    response_text: str = "The model should response this text"

    genai_client = MockGenAIClient(
        MockModels(response_text)
    )
    client = Client(genai_client, "not-a-real-model") # pyright: ignore[reportArgumentType]

    chunks = string_split(response_text)
    iterator = client.text_stream([])
    for response_chunk, check_chunk in zip(iterator, chunks):
        assert response_chunk == check_chunk, f"Expected chunk: {check_chunk}. Got: {response_chunk}"

def test_text_stream_model_failed_to_response():
    """Test that text_stream raises GeminiAPIError when model returns None."""
    response_text = None

    genai_client = MockGenAIClient(
        MockModels(response_text)
    )
    client = Client(genai_client, "not-a-real-model") # pyright: ignore[reportArgumentType]

    with pytest.raises(exceptions.GeminiAPIError):
        iterator = client.text_stream([])
        _ = next(iterator)

def test_text_stream_generate_content_stream_call(mocker: MockerFixture):
    """Test that text_stream calls generate_content_stream with correct parameters."""
    # Payloads to call the .text_stream
    system_messages = [Message("system", "System message")]
    normal_messages = [Message("user", "User message"), Message("model", "Model message")]
    model: str = "not-a-real-model"

    genai_client = MockGenAIClient(MockModels(""))
    client = Client(genai_client, model) # pyright: ignore[reportArgumentType]

    mock_generate_content = mocker.patch('ggmw.tests.genai_mock_client.MockModels.generate_content_stream')

    # Arguments for the .text_stream method
    run_arg_messages = system_messages + normal_messages
    run_arg_thinking_level = "LOW"

    # Arguments that will be passed to the .generate_content_stream method
    check_arg_model = model
    check_arg_contents = [msg.to_gemini_part() for msg in normal_messages]
    check_arg_config = client._construct_config(system_messages, run_arg_thinking_level) # pyright: ignore[reportPrivateUsage]

    iterator = client.text_stream(run_arg_messages, run_arg_thinking_level)

    for _ in iterator:
        pass

    mock_generate_content.assert_called_once_with(
        model=check_arg_model,
        contents=check_arg_contents,
        config=check_arg_config
    )

"""
Structured response methods ---------------------------------------------------
These tests verify that structured (JSON) responses are correctly parsed into
Pydantic models for both successful responses and error conditions.
"""

def test_structured_run_success():
    """Test that structured_run correctly parses JSON response into Pydantic model."""
    class ResponseSchema(BaseModel):
        a: int
        b: str
        c: bool

    response_text: str | None = '{"a": 42, "b": "hello world", "c": true}'

    genai_client = MockGenAIClient(
        MockModels(response_text)
    )
    client = Client(genai_client, "not-a-real-model") # pyright: ignore[reportArgumentType]

    res = client.structured_run([], ResponseSchema)

    parsed_response = ResponseSchema.model_validate_json(response_text)

    assert res == parsed_response, f"Expected: {parsed_response}. Got: {res}"

def test_structured_run_model_failed_to_response():
    """Test that structured_run raises GeminiAPIError when model returns None."""
    class ResponseSchema(BaseModel):
        a: int
        b: str
        c: bool

    response_text = None

    genai_client = MockGenAIClient(
        MockModels(response_text)
    )
    client = Client(genai_client, "not-a-real-model") # pyright: ignore[reportArgumentType]

    with pytest.raises(exceptions.GeminiAPIError):
        _ = client.structured_run([], ResponseSchema)

def test_structured_run_model_produces_malformed_json():
    """Test that structured_run raises MalformedJSON for invalid JSON."""
    class ResponseSchema(BaseModel):
        a: int
        b: str
        c: bool

    response_text = "this is not valid json string"

    genai_client = MockGenAIClient(
        MockModels(response_text)
    )
    client = Client(genai_client, "not-a-real-model") # pyright: ignore[reportArgumentType]

    with pytest.raises(exceptions.MalformedJSON):
        _ = client.structured_run([], ResponseSchema)

def test_structured_run_model_produces_incorrect_schema():
    """Test that structured_run raises ValidationError for JSON that doesn't match schema."""
    class ResponseSchema(BaseModel):
        a: int
        b: str
        c: bool

    response_text = '{"wrong": "schema"}'

    genai_client = MockGenAIClient(
        MockModels(response_text)
    )
    client = Client(genai_client, "not-a-real-model") # pyright: ignore[reportArgumentType]

    with pytest.raises(pydantic.ValidationError):
        _ = client.structured_run([], ResponseSchema)

def test_structured_run_generate_content_call(mocker: MockerFixture):
    """Test that structured_run calls generate_content with correct parameters."""
    class ResponseSchema(BaseModel):
        a: str
        b: int

    # Payloads to call the .structured_run
    system_messages = [Message("system", "System message")]
    normal_messages = [Message("user", "User message"), Message("model", "Model message")]
    model: str = "not-a-real-model"

    genai_client = MockGenAIClient(MockModels(""))
    client = Client(genai_client, model) # pyright: ignore[reportArgumentType]

    mock_generate_content = mocker.patch('ggmw.tests.genai_mock_client.MockModels.generate_content')
    mock_generate_content.return_value.text = '{"a": "something", "b": 36}'

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

    _ = client.structured_run(run_arg_messages, ResponseSchema, run_arg_thinking_level)

    mock_generate_content.assert_called_once_with(
        model=check_arg_model,
        contents=check_arg_contents,
        config=check_arg_config
    )

"""
Structured stream methods -----------------------------------------------------
These tests verify that structured streaming responses work properly and handle
streaming edge cases correctly.
"""

def test_structured_stream_success():
    """Test that structured_stream correctly processes streaming JSON responses."""
    class ResponseSchema(BaseModel):
        a: int
        b: str
        c: bool

    response_text: str | None = '{"a": 42, "b": "hello world", "c": true}'

    genai_client = MockGenAIClient(
        MockModels(response_text)
    )
    client = Client(genai_client, "not-a-real-model") # pyright: ignore[reportArgumentType]

    chunks = string_split(response_text)
    aggregate_chunks = ""
    iterator = client.structured_stream([], ResponseSchema)
    for response_partial, check_chunk in zip(iterator, chunks):
        aggregate_chunks += check_chunk
        import partial_json_parser as pjp
        fixed_check_chunk = pjp.loads(aggregate_chunks)
        from ..core.partial import partial_model
        check_partial = partial_model(ResponseSchema).model_validate(fixed_check_chunk)

        assert response_partial == check_partial, f"Expected: {repr(check_partial)}. Got: {repr(response_partial)}"

def test_structured_stream_model_failed_to_response():
    """Test that structured_stream raises GeminiAPIError when model returns None."""
    class ResponseSchema(BaseModel):
        a: int
        b: str
        c: bool

    response_text = None

    genai_client = MockGenAIClient(
        MockModels(response_text)
    )
    client = Client(genai_client, "not-a-real-model") # pyright: ignore[reportArgumentType]

    with pytest.raises(exceptions.GeminiAPIError):
        for _ in client.structured_stream([], ResponseSchema):
            pass

def test_structured_stream_model_produces_malformed_json():
    """Test that structured_stream raises MalformedJSON for invalid JSON during streaming."""
    class ResponseSchema(BaseModel):
        a: int
        b: str
        c: bool

    response_text = "this is not valid json string"

    genai_client = MockGenAIClient(
        MockModels(response_text)
    )
    client = Client(genai_client, "not-a-real-model") # pyright: ignore[reportArgumentType]

    with pytest.raises(exceptions.MalformedJSON):
        for _ in client.structured_stream([], ResponseSchema):
            pass

def test_structured_stream_generate_content_call(mocker: MockerFixture):
    """Test that structured_stream calls generate_content_stream with correct parameters."""
    class ResponseSchema(BaseModel):
        a: str
        b: int

    # Payloads to call the .structured_stream
    system_messages = [Message("system", "System message")]
    normal_messages = [Message("user", "User message"), Message("model", "Model message")]
    model: str = "not-a-real-model"

    genai_client = MockGenAIClient(MockModels('{"a": "test", "b": 42}'))
    client = Client(genai_client, model) # pyright: ignore[reportArgumentType]

    # Create proper mock for streaming response
    mock_response1 = mocker.Mock()
    mock_response1.text = '{"a": "te'
    mock_response2 = mocker.Mock()
    mock_response2.text = 'st", "b": 42}'
    mock_iterator = iter([mock_response1, mock_response2])
    
    mock_generate_content = mocker.patch('ggmw.tests.genai_mock_client.MockModels.generate_content_stream')
    mock_generate_content.return_value = mock_iterator

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

    for _ in client.structured_stream(run_arg_messages, ResponseSchema, run_arg_thinking_level):
        pass

    mock_generate_content.assert_called_once_with(
        model=check_arg_model,
        contents=check_arg_contents,
        config=check_arg_config
    )