# MongoDB to Elasticsearch Sync Service

A Python application that listens to MongoDB change streams and syncs data to Elasticsearch in real-time.

## Features

- **Real-time Sync**: Automatically updates Elasticsearch based on MongoDB changes.
- **Retry Mechanism**: Retries on failure with exponential backoff.
- **Configurable**: Environment variable support for easy configuration.
- **Dockerized**: Simplified deployment using Docker and Docker Compose.

## Requirements

- **Python 3.12**
- **MongoDB** (with change stream support)
- **Elasticsearch**
- **Poetry** for dependency management

## Setup

### 1. Environment Variables

Create a `.env` file in the project root:

```dotenv
# MongoDB Configuration
MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=your_database
MONGODB_COLLECTION=your_collection

# Elasticsearch Configuration
ELASTICSEARCH_URI=http://localhost:9200
ELASTICSEARCH_USERNAME=your_username
ELASTICSEARCH_PASSWORD=your_password

# Application Configuration
LOG_LEVEL=INFO
RETRY_INTERVAL_SECONDS=5
```

###  Install Dependencies
poetry install
### Run the Application
poetry run python main.py
