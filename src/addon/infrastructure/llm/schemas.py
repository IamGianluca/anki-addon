from typing import List, Optional

from pydantic import BaseModel


class AddonNoteChanges(BaseModel):
    """Pydantic schema for LLM structured output when formatting notes.

    This schema defines the expected JSON structure that the LLM should return
    when formatting or editing notes. It's used for generating JSON schemas
    and validating LLM responses.

    Attributes:
        front: Updated front side content
        back: Updated back side content
        tags: Updated list of tags (optional)
    """

    front: str
    back: str
    tags: Optional[List[str]] = None