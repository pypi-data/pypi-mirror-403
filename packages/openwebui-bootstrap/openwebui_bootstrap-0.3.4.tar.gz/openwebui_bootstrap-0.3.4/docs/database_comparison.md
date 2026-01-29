# Database Structure Comparison: openwebui-bootstrap vs open-webui

## Overview

This document compares the database structures between the `openwebui-bootstrap` package and the main `open-webui` repository to understand how they handle model capabilities.

## openwebui-bootstrap (src/openwebui_bootstrap/models.py)

### ModelEntity Class

The `ModelEntity` class in openwebui-bootstrap represents a model configuration:

```python
class ModelEntity(BaseModel):
    id: str
    name: str
    description: str | None = None
    capabilities: dict[str, bool]  # NEW: Dictionary of capability names to boolean values
    default_capabilities: dict[str, bool]  # NEW: Default capabilities
    meta: dict[str, Any] | None = None
    params: dict[str, Any] | None = None
```

**Key Features:**
- Uses `capabilities` as a dictionary mapping capability names to boolean values
- Uses `default_capabilities` as a dictionary for default capabilities
- Both are separate fields in the model
- Capabilities are stored directly in the model structure

### Capability Names

The `openwebui-bootstrap` package defines these capabilities:

```python
CAPABILITIES = {
    "chat": "Chat with the model",
    "image_generation": "Generate images",
    "image_to_image": "Generate images from images",
    "image_variation": "Generate image variations",
    "image_masked_generation": "Generate images with masked areas",
    "image_description": "Describe images",
    "image_analysis": "Analyze images",
    "image_crop": "Crop images",
    "image_upscale": "Upscale images",
    "image_outpainting": "Extend images",
    "image_inpainting": "Modify images",
    "image_to_video": "Generate videos from images",
    "video_generation": "Generate videos",
    "video_to_video": "Generate videos from videos",
    "video_to_image": "Extract images from videos",
    "video_analysis": "Analyze videos",
    "audio_generation": "Generate audio",
    "audio_to_audio": "Modify audio",
    "audio_to_text": "Transcribe audio to text",
    "text_to_audio": "Convert text to speech",
    "text_to_speech": "Convert text to speech",
    "text_to_image": "Generate images from text",
    "text_to_video": "Generate videos from text",
    "text_analysis": "Analyze text",
    "text_to_text": "Process text",
    "text_to_code": "Generate code",
    "code_to_text": "Explain code",
    "code_analysis": "Analyze code",
    "code_to_code": "Modify code",
    "embedding": "Generate embeddings",
    "rerank": "Rerank search results",
    "automatic_speech_recognition": "Recognize speech",
    "speech_to_text": "Convert speech to text",
    "text_to_speech": "Convert text to speech",
    "text_to_audio": "Convert text to audio",
    "audio_to_text": "Convert audio to text",
    "audio_to_audio": "Process audio",
    "audio_generation": "Generate audio",
    "video_generation": "Generate videos",
    "video_to_video": "Process videos",
    "video_to_image": "Extract frames from videos",
    "video_analysis": "Analyze videos",
    "image_generation": "Generate images",
    "image_to_image": "Process images",
    "image_to_video": "Convert images to videos",
    "image_analysis": "Analyze images",
    "image_description": "Describe images",
    "image_crop": "Crop images",
    "image_upscale": "Upscale images",
    "image_outpainting": "Extend images",
    "image_inpainting": "Modify images",
    "image_masked_generation": "Generate images with masks",
    "chat": "Chat with the model",
    "text_to_text": "Process text",
    "text_to_code": "Generate code",
    "code_to_text": "Explain code",
    "code_analysis": "Analyze code",
    "code_to_code": "Modify code",
    "embedding": "Generate embeddings",
    "rerank": "Rerank search results",
}
```

## open-webui (backend/open_webui/models/models.py)

### ModelMeta Class

The `ModelMeta` class in open-webui represents metadata for models:

```python
class ModelMeta(BaseModel):
    profile_image_url: Optional[str] = "/static/favicon.png"
    description: Optional[str] = None
    """User-facing description of the model."""
    capabilities: Optional[dict] = None
    model_config = ConfigDict(extra="allow")
    pass
```

### Model Table Structure

The `Model` table in open-webui has:

```python
class Model(Base):
    __tablename__ = "model"

    id = Column(Text, primary_key=True, unique=True)
    user_id = Column(Text)
    base_model_id = Column(Text, nullable=True)
    name = Column(Text)
    params = Column(JSONField)  # Holds ModelParams
    meta = Column(JSONField)    # Holds ModelMeta (including capabilities)
    access_control = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True)
    updated_at = Column(BigInteger)
    created_at = Column(BigInteger)
```

**Key Features:**
- Capabilities are stored within the `meta` JSON field as part of `ModelMeta`
- The `meta` field is a JSON blob that can contain any additional metadata
- Capabilities are optional (can be None)
- Uses SQLAlchemy's JSONField for flexible storage

## Comparison Summary

| Feature | openwebui-bootstrap | open-webui |
|---------|---------------------|------------|
| **Capability Storage** | Separate `capabilities` field | Inside `meta` JSON field |
| **Capability Format** | Dictionary: `{name: bool}` | Dictionary: `{name: bool}` |
| **Default Capabilities** | Separate `default_capabilities` field | Not explicitly defined |
| **Field Type** | Direct model field | JSON field within `meta` |
| **Flexibility** | Less flexible, fixed structure | More flexible, can store any metadata |
| **Database Schema** | SQLAlchemy model fields | SQLAlchemy JSONField |
| **Backward Compatibility** | New structure | Existing structure |

## Migration Strategy

Since `openwebui-bootstrap` is a new package and `open-webui` is the established project, the recommended approach is:

1. **For openwebui-bootstrap**: Store capabilities in the `meta` field to align with open-webui's structure
2. **Keep backward compatibility**: Support both the new `capabilities` field and the `meta.capabilities` approach
3. **Migration path**: When syncing with open-webui, transform capabilities to the `meta` format

## Implementation Recommendation

The `openwebui-bootstrap` package should:

1. Store capabilities in both places initially for backward compatibility:
   ```python
   capabilities: dict[str, bool]  # Direct field
   meta: dict[str, Any] = Field(default_factory=dict)  # Also includes capabilities
   ```

2. When saving to database, ensure capabilities are in the `meta` field:
   ```python
   meta = {
       "description": description,
       "capabilities": capabilities,
       # other metadata
   }
   ```

3. When loading from database, merge capabilities from both sources:
   ```python
   capabilities = meta.get("capabilities", {}) or self.capabilities
   ```

This approach ensures compatibility with both the new `openwebui-bootstrap` structure and the existing `open-webui` database schema.
