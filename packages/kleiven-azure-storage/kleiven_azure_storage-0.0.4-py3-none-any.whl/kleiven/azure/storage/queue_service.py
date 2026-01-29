from azure.storage.queue import QueueServiceClient, QueueProperties
from kleiven.azure.storage import Queue

class QueueService:
    def __init__(self, connection_string: str):
        self._client = QueueServiceClient.from_connection_string(
            conn_str=connection_string)

    @property
    def client(self) -> QueueServiceClient:
        return self._client

    def get_queue(self, queue: str | QueueProperties ) -> "Queue":
        queue_client = self.client.get_queue_client(queue)
        return Queue(queue_client)
