from pydantic import BaseModel


class WorkerInfo(BaseModel):
    scheduler_url: str
    namespace: str
    tls: bool = False
