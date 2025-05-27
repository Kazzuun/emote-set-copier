from pydantic import BaseModel, Field, field_validator


class EmoteFlags(BaseModel):
    private: bool


class EmoteData(BaseModel):
    id: str
    default_name: str = Field(alias="defaultName")
    flags: EmoteFlags


class EmoteSetEmote(BaseModel):
    id: str
    alias: str
    data: EmoteData = Field(alias="emote")


class Emotes(BaseModel):
    items: list[EmoteSetEmote] = Field(default_factory=list)
    total_count: int = Field(alias="totalCount")


class Owner(BaseModel):
    id: str
    editors: list[str] = Field(default_factory=list)

    @field_validator("editors", mode="before")
    @classmethod
    def validate_flags(cls, editors: list[dict[str, str]]) -> list[str]:
        return [editor["editorId"] for editor in editors]


class EmoteSet(BaseModel):
    id: str
    name: str
    capacity: int
    emotes: Emotes
    owner: Owner
