from typing import Literal

type Role = Literal[
    "user",
    "model",
    "system"
]

type MimeType = Literal[
    # Image types
    "image/png", "image/jpeg", "image/webp",

    # Video types
    "video/x-flv", "video/quicktime", "video/mpeg", "video/mpegps",
    "video/mpg", "video/mp4", "video/webm", "video/wmv", "video/3gpp",

    # Audio types
    "audio/aac", "audio/flac", "audio/mp3", "audio/m4a", "audio/mpeg",
    "audio/mpga", "audio/mp4", "audio/opus", "audio/pcm", "audio/wav",
    "audio/webm",

    # Document types
    "application/pdf", "text/plain",
]

type MediaResolutions = Literal[
    'MEDIA_RESOLUTION_UNSPECIFIED',
    'MEDIA_RESOLUTION_LOW',
    'MEDIA_RESOLUTION_MEDIUM',
    'MEDIA_RESOLUTION_HIGH',
    'MEDIA_RESOLUTION_ULTRA_HIGH',
]

type ThinkingLevel = Literal[
    "THINKING_LEVEL_UNSPECIFIED", 
    "MINIMAL", 
    "LOW", 
    "MEDIUM", 
    "HIGH", 
]
