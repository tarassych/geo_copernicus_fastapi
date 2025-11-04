from pydantic_settings import BaseSettings
from functools import lru_cache
import os
from io import StringIO
from dotenv import load_dotenv


def load_environment_variables():
    """
    Load environment variables from appropriate source:
    - GCP Cloud Run: Load from AppSecretsFromDotEnv environment variable (Secret Manager)
    - Local Development: Load from .env file
    """
    # Check if running in GCP Cloud Run with Secret Manager mounted as env var
    secret_content = os.getenv("AppSecretsFromDotEnv")
    
    if secret_content:
        # Running in Cloud Run - parse the secret content as dotenv format
        print("Loading environment variables from GCP Secret Manager (AppSecretsFromDotEnv)")
        load_dotenv(stream=StringIO(secret_content), override=True)
    else:
        # Running locally - load from .env file
        env_file = ".env"
        if os.path.exists(env_file):
            print(f"Loading environment variables from {env_file}")
            load_dotenv(env_file, override=True)
        else:
            print("No .env file found, using default environment variables")


# Load environment variables on module import
load_environment_variables()


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    Variables are loaded from:
    - GCP Cloud Run: AppSecretsFromDotEnv secret (mounted as environment variable)
    - Local Development: .env file in project root
    """
    target_dir: str = "tilescache"
    log_dir: str = "logs"
    topo_api_key: str = ""
    
    class Config:
        # Pydantic will read from os.environ after dotenv loads
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance
    """
    return Settings()

