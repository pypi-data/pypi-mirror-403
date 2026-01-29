from typing import overload
from collections.abc import Iterable

from google.genai import types
from pydantic import validate_call

from .types import (
    Role,
    MimeType,
    MediaResolutions,
)

class Message:
    """Represents a message in a conversation with the Gemini API.

    A Message contains content along with metadata about its role (user, model, system) and,
    if the content is binary, information about its MIME type and media resolution.

    Args:
        `role` (`Literal[str]`): The role of the message participant (e.g., "user", "model", "system").
        `content` (`str | bytes`): The content of the message. Can be text (str) or binary data (bytes).
        `mime_type` (`Literal[str] | None`, optional): Required when content is bytes, specifies the
            MIME type of the binary content (e.g., "image/jpeg", "video/mp4"). Defaults to None.
        `media_resolution` (`Literal[str] | None`, optional): Specifies the resolution of media
            content if applicable. Defaults to None.

    Raises:
        `ValueError`: If content is bytes but no mime_type is provided.
        `pydantic.ValidationError`: If arguments don't conform to expected types or values.
    Examples:
        >>> message = Message("user", "Hello, how are you?")
        >>>
        >>> image_data = b"\\x89PNG\\r\\n..."
        >>> image_message = Message("user", image_data, mime_type="image/png")
    """
    @overload
    def __init__(
        self,
        role: Role,
        content: str,
        /,   
    ) -> None: ...
    
    @overload
    def __init__(
        self,
        role: Role,
        content: bytes,
        /,
        *,
        mime_type: MimeType,
        media_resolution: MediaResolutions | None = None
    ) -> None: ...
    
    @validate_call
    def __init__(
        self, 
        role: Role,
        content: str | bytes,
        /,
        *,
        mime_type: MimeType | None = None,
        media_resolution: MediaResolutions | None = None 
    ): 
        self._role: Role = role 
        self._content: str | bytes = content 

        if isinstance(content, bytes):
            if mime_type is None: 
                raise ValueError(
                    f"mime_type: Mime type must be specified when content type is bytes"
                )       
    
            self._mime_type: MimeType = mime_type     

        self._media_resolution: MediaResolutions | None = media_resolution 
    
    @validate_call
    def has_role(self, role: Role) -> bool:
        """Check if the message has the specified role.

        Args:
            `role` (`Literal[str]`): The role to check against the message's role.

        Returns:
            `bool`: True if the message's role matches the provided role, False otherwise.

        Raises:
            `pydantic.ValidationError`: If the role doesn't conform to expected types or values.
        """
        return role == self._role 
   
    @property
    def content(self) -> str | bytes:
        """Get the content of the message.

        Returns:
            `str | bytes`: The content of the message, either as text (str) or binary data (bytes).
        """
        return self._content

    def to_gemini_part(self) -> types.Part:
        """Convert the message content to a google-genai Part object.

        This method transforms the message's content into the appropriate format
        expected by the Google Gemini API, handling both text and binary content.

        Returns:
            `types.Part`: A Part object suitable for use with the Google Gemini API.

        Raises:
            `NotImplementedError`: If the content type is neither str nor bytes.
        """
        if isinstance(self._content, str):
            return types.Part.from_text(text=self._content)

        elif isinstance(self._content, bytes): # pyright: ignore[reportUnnecessaryIsInstance]
            return types.Part.from_bytes(
                data=self._content,
                mime_type=self._mime_type,
                media_resolution=self._media_resolution
            )
        else:
            raise NotImplementedError(f"content type {type(self._content)}")


def split_messages(messages: Iterable[Message]) -> tuple[list[Message], list[Message]]:
    """Split messages into system and normal messages based on their roles.

    This function separates messages with the 'system' role from messages with
    'user' or 'model' roles, which is useful when preparing messages for API calls
    that treat system instructions differently from conversation messages.

    Args:
        `messages` (`Iterable[Message]`): The iterable of messages to split

    Returns:
        `tuple[list[Message], list[Message]]`: A tuple containing two lists:
            - First element: List of system messages (role is 'system')
            - Second element: List of normal messages (role is 'user' or 'model')

    Example:
        >>> messages = [
        ...     Message("system", "Be helpful"),
        ...     Message("user", "Hello!"),
        ...     Message("model", "Hi there!")
        ... ]
        >>> system_msgs, normal_msgs = split_messages(messages)
        >>> len(system_msgs)
        1
        >>> len(normal_msgs)
        2
    """

    system_messages: list[Message] = [] 
    normal_messages: list[Message] = []
    for msg in messages:
        if msg.has_role("system"):
            system_messages.append(msg)
        else:
            normal_messages.append(msg)

    return system_messages, normal_messages
