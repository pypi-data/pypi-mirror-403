from fluidattacks_batch_client.api import ApiClient
from ._send import send_pipeline, send_single_job
from ._core import BatchJobSender


def new_sender(client: ApiClient) -> BatchJobSender:
    return BatchJobSender(
        lambda j, d: send_single_job(client, j, d),
        lambda p: send_pipeline(client, p),
    )


__all__ = [
    "BatchJobSender",
]
