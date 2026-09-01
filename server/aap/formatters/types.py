from superdesk.core.types import BaseModel


class RSSParams(BaseModel):
    days: int | None = 2
