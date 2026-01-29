from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class DigestifySettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    openai_api_key: SecretStr = Field(default=...)
    openai_model: str = Field(default="gpt-5.2")
    webquest_mcp_access_token: SecretStr = Field(default=...)
    webquest_mcp_url: str = Field(default=...)
    max_tool_calls: int = Field(default=5)
    max_output_tokens: int = Field(default=100000)
