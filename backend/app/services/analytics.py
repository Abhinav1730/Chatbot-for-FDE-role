from app.schemas import Analytics, Session
from app.services.llm import generate_analytics as llm_generate_analytics


def generate_analytics(session: Session) -> Analytics:
    return llm_generate_analytics(session)
