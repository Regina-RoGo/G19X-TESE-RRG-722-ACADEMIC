from sqlmodel import Session

from app.repositories import ai_summary_repository, customer_repository, interaction_repository


def get_dashboard_data(session: Session) -> dict:
    return {
        "total_customers": customer_repository.count(session),
        "total_interactions": interaction_repository.count(session),
        "total_summaries": ai_summary_repository.count(session),
        "recent_interactions": interaction_repository.get_recent(session, limit=5),
        "recent_customers": customer_repository.get_recent(session, limit=5),
    }
