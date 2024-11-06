import logging
import signal
import sys
import time
from typing import Any, Optional

from elasticsearch import Elasticsearch
from pymongo import MongoClient

from config import config  # type: ignore

# Logging setup
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO
)


class Service:
    def __init__(self) -> None:
        self.mongo_client: Optional[MongoClient[Any]] = None
        self.es_client: Optional[Elasticsearch] = None

        self.is_running = True

        self.connect_clients()

        signal.signal(signal.SIGTERM, self.graceful_shutdown)
        signal.signal(signal.SIGINT, self.graceful_shutdown)

    def connect_clients(self, retries: str = config.MAX_RETRIES) -> None:
        """Establishes connections to MongoDB and Elasticsearch with retry on failure."""
        if not all(
            [config.MONGODB_URI, config.ELASTIC_USERNAME, config.ELASTIC_PASSWORD]
        ):
            logging.error("Missing environment variables for database connections.")
            return None
        for attempt in range(int(retries)):
            try:
                self.mongo_client = MongoClient(config.MONGODB_URI)
                self.es_client = Elasticsearch(
                    config.ELASTICSEARCH_URI,
                    basic_auth=(config.ELASTIC_USERNAME, config.ELASTIC_PASSWORD),
                )
                if self.es_client.ping():
                    logging.info("Connected to Elasticsearch and MongoDB")
                    return None
            except Exception as e:
                logging.error(f"Attempt {attempt + 1}: Failed to connect - {e}")
                time.sleep(int(config.RETRY_INTERVAL_SEC) * (2**attempt))

        raise ConnectionError(
            "Failed to establish MongoDB/Elasticsearch connection after retries"
        )

    def start_change_stream(self) -> None:
        """Start monitoring MongoDB change stream and handle changes."""
        if self.mongo_client:
            db = self.mongo_client["skillanthropy"]
        resume_token = None
        try:
            change_stream = db.watch(
                [
                    {
                        "$match": {
                            "operationType": {"$in": ["update", "delete", "insert"]}
                        }
                    }
                ],
                resume_after=resume_token,
            )
            logging.info("Watching MongoDB change stream...")
            for change_event in change_stream:
                self.handle_change(change_event)
                resume_token = change_event[
                    "_id"
                ]  # save the token after handling each change event

        except Exception as e:
            logging.error(f"Change stream error: {e}")
            time.sleep(int(config.RETRY_INTERVAL_SEC))
            if self.is_running:
                self.start_change_stream()

    def handle_change(self, change_event: dict[str, Any]) -> None:
        """Process a MongoDB change event."""
        try:
            operation_type = change_event["operationType"]
            document_id = change_event["documentKey"]["_id"]
            collection = self.get_collection_name(change_event["ns"]["coll"])
            document_change = change_event.get("fullDocument") or change_event[
                "updateDescription"
            ].get("updatedFields")

            logging.info(
                f"Change detected - Type: {operation_type}, Collection: {collection}, Document ID: {document_id}"
            )
            if operation_type == "update":
                self.update_document_in_es(collection, document_id, document_change)
            elif operation_type == "insert":
                self.insert_document_in_es(collection, document_id, document_change)
            elif operation_type == "delete":
                self.delete_document_in_es(collection, document_id)
        except KeyError as e:
            logging.error(f"Error processing change event: Missing expected field {e}")
        except KeyError as e:
            logging.error(f"Error processing change event: Missing expected field {e}")

    def get_collection_name(self, mongo_collection: str) -> str:
        """Maps MongoDB collections to Elasticsearch indices."""
        collection_mapping = {
            "tasks": "skillanthropy-tasks",
            "users": "skillanthropy_users",
            "charities": "skillanthropy-charities",
        }
        return collection_mapping.get(mongo_collection, mongo_collection)

    def update_document_in_es(
        self, collection_name: str, document_id: Any, updated_fields: dict[str, Any]
    ) -> None:
        """Update a document in Elasticsearch."""
        try:
            if self.es_client:
                self.es_client.update(
                    index=collection_name, id=document_id, doc=updated_fields
                )
                logging.info(
                    f"Updated document {document_id} in collection {collection_name}"
                )
        except Exception as e:
            logging.error(f"Failed to update document in Elasticsearch: {e}")

    def insert_document_in_es(
        self, collection_name: str, document_id: Any, document: dict[str, Any]
    ) -> None:
        """Update a document in Elasticsearch."""
        try:
            if self.es_client:
                self.es_client.index(
                    index=collection_name, id=document_id, document=document
                )
                logging.info(
                    f"Updated document {document_id} in collection {collection_name}"
                )
        except Exception as e:
            logging.error(f"Failed to update document in Elasticsearch: {e}")

    def delete_document_in_es(self, index: str, document_id: Any) -> None:
        """Delete a document from Elasticsearch."""
        try:
            if self.es_client:
                self.es_client.delete(index=index, id=document_id)
                logging.info(f"Deleted document {document_id} from index {index}")
        except Exception as e:
            logging.error(f"Failed to delete document in Elasticsearch: {e}")

    def graceful_shutdown(self, signum: int, frame: Any) -> None:
        """Handle SIGTERM and SIGINT signals to shut down the service gracefully."""
        logging.info("Received shutdown signal. Initiating graceful shutdown...")
        self.is_running = False
        self.shutdown()
        sys.exit(0)

    def shutdown(self) -> None:
        if self.mongo_client:
            self.mongo_client.close()
            logging.info("MongoDB connection closed.")
        if self.es_client:
            self.es_client.transport.close()
            logging.info("Elasticsearch connection closed.")
