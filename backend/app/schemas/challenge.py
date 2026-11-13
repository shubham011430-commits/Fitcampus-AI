from pydantic import BaseModel


class ChallengeProgressUpdate(BaseModel):
    progress: int
