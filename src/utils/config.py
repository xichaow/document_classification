"""
Configuration management for the document classification system.

This module handles environment variables and application settings using
pydantic for validation and type safety.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    """
    Application settings with environment variable support.

    Uses pydantic BaseSettings to automatically load and validate
    environment variables with type hints and default values.
    """

    # AWS Configuration - Optional for fallback mode
    AWS_ACCESS_KEY_ID: str = Field(default="", description="AWS access key ID")
    AWS_SECRET_ACCESS_KEY: str = Field(default="", description="AWS secret access key")
    AWS_REGION: str = Field(default="us-east-1", description="AWS region")

    # Bedrock Configuration
    BEDROCK_MODEL_ID: str = Field(
        default="anthropic.claude-v2", description="Bedrock model ID for classification"
    )
    BEDROCK_REGION: str = Field(default="us-east-1", description="Bedrock region")

    # Application Configuration
    ENVIRONMENT: str = Field(default="development", description="Environment (development/production)")
    MAX_FILE_SIZE: int = Field(
        default=20971520, description="Maximum file size in bytes"  # 20MB
    )
    UPLOAD_DIR: str = Field(default="uploads", description="Upload directory")
    RESULTS_DIR: str = Field(default="results", description="Results directory")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")

    # Web Interface
    HOST: str = Field(default="0.0.0.0", description="Server host")
    PORT: int = Field(default=8000, description="Server port")

    # Classification Settings
    CONFIDENCE_THRESHOLD: float = Field(
        default=0.8, description="Minimum confidence threshold for classification"
    )
    TEXTRACT_CONFIDENCE_THRESHOLD: float = Field(
        default=0.95, description="Minimum confidence threshold for Textract extraction"
    )

    class Config:
        """Pydantic configuration."""

        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """
    Get application settings.

    Returns:
        Settings: Application settings instance.
    """
    return settings


def validate_aws_credentials() -> bool:
    """
    Validate AWS credentials are present.

    Returns:
        bool: True if credentials are present, False otherwise.
    """
    try:
        return bool(settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY)
    except Exception:
        return False
