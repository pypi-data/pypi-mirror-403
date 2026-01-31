"""Base event class."""

import uuid
import pydantic


class Event(pydantic.BaseModel):
    """Base event class."""

    event_id: uuid.UUID = pydantic.Field(default_factory=uuid.uuid4)
