import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    MONGODB_URI = os.getenv("MONGODB_URI", "http://localhost:27017")
    DATABASE_NAME = os.getenv("DATABASE_NAME", "skillanthropy")
    COLLECTION_NAME = os.getenv("COLLECTION_NAME", "tasks")
    ELASTICSEARCH_URI = os.getenv("ELASTICSEARCH_URI", "http://localhost:27017")
    ELASTIC_USERNAME = os.getenv("ELASTICSEARCH_USERNAME")
    ELASTIC_PASSWORD = os.getenv("ELASTICSEARCH_PASSWORD")
    RETRY_INTERVAL_SEC = os.getenv("RETRY_INTERVAL_SECOND", 5)
    MAX_RETRIES = os.getenv("MAX_RETRIES", 5)


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


# Select configuration based on environment
config = DevelopmentConfig if os.getenv("ENV") == "development" else ProductionConfig
