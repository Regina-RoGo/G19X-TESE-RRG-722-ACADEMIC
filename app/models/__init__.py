from app.models.user import User, UserRole
from app.models.customer import Customer
from app.models.interaction_type import InteractionType
from app.models.interaction import Interaction
from app.models.ai_summary import AISummary
from app.models.deal import Deal, DealStage
from app.models.sales_suggestion import SalesSuggestion

__all__ = [
    "User",
    "UserRole",
    "Customer",
    "InteractionType",
    "Interaction",
    "AISummary",
    "Deal",
    "DealStage",
    "SalesSuggestion",
]
