from enum import Enum
from typing import Literal, Union

from pydantic import BaseModel, Field


class FileExtension(str, Enum):
    """Enumeration of supported file extensions for local export settings."""

    PARQUET = "parquet"
    CSV = "csv"
    PICKLE = "pkl"


class LocalSettings(BaseModel):
    """
    Configuration settings for exporting data to a local file system.

    Attributes:
        artifacts_dir (str): Base directory for storing all exported artifacts.
        extension (FileExtension): File format to use when saving outputs.
    """

    class Config:
        use_enum_values = True

    artifacts_dir: str = Field(..., description="Base directory for all artifacts and outputs")
    extension: FileExtension = Field(default=FileExtension.PARQUET, description="File format extension")


class SnowflakeSettings(BaseModel):
    """
    Configuration settings for exporting data to a Snowflake database.

    Attributes:
        database_name (str): Name of the target Snowflake database.
        schema_name (str): Name of the schema within the Snowflake database.
    """

    database_name: str = Field(..., description="Snowflake database name")
    schema_name: str = Field(..., description="Snowflake schema name")


class OutputConfig(BaseModel):
    """Configuration for prediction output destination."""

    type: Literal["local", "snowflake"]
    settings: Union[LocalSettings, SnowflakeSettings]

    @classmethod
    def local(cls, artifacts_dir: str, extension: FileExtension = FileExtension.PARQUET) -> "OutputConfig":
        """Create a configuration for local file system output."""
        return cls(type="local", settings=LocalSettings(artifacts_dir=artifacts_dir, extension=extension))

    @classmethod
    def snowflake(cls, database_name: str, schema_name: str) -> "OutputConfig":
        """Create a configuration for Snowflake database output."""
        return cls(type="snowflake", settings=SnowflakeSettings(database_name=database_name, schema_name=schema_name))
