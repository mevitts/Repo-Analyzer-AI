from pydantic import BaseModel

class RepoInput(BaseModel):
    owner: str
    repo: str

class AnalysisResponse(BaseModel):
    report: str
    session_id: str 