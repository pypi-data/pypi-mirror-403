from azure.storage.queue import QueueClient, QueueMessage
import json

class Queue:

    def __init__(self, client: QueueClient):
        self._client = client

    @property
    def client(self) -> QueueClient:
        return self._client

    @property
    def queue_name(self) -> str:
        return self.client.queue_name
    
    # Serialize content as json using json.dumps(content)
    def send_json_message(self, content: object | None,
                          visibility_timeout: int | None = None,
                          time_to_live: int | None = None,
                          timeout: int | None = None ) -> QueueMessage:
        self.client.send_message(
            content = json.dumps(content),
            visibility_timeout=visibility_timeout,
            time_to_live=time_to_live,
            timeout=timeout)
