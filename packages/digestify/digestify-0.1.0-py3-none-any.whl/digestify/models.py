from pydantic import BaseModel


class Topic(BaseModel):
    name: str
    description: str


class Story(BaseModel):
    title: str
    content: str
    published_at: str
    reference_urls: list[str]


class Digest(BaseModel):
    stories: list[Story]
