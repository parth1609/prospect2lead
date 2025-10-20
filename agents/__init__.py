from .base import Agent
from .prospect_search import ProspectSearchAgent
from .pre_enrichment import LLMPreEnrichmentAgent
from .enrichment import DataEnrichmentAgent
from .third_party_enrichment import ThirdPartyEnrichmentAgent
from .intent_signals import AnonymizedIntentSignalAgent
from .scoring import ScoringAgent
from .email_verification import EmailVerificationAgent
from .outreach_content import OutreachContentAgent
from .outreach_executor import OutreachExecutorAgent
from .response_tracker import ResponseTrackerAgent
from .feedback_trainer import FeedbackTrainerAgent
from .feedback_apply import FeedbackApplyAgent

AGENTS = {
    "ProspectSearchAgent": ProspectSearchAgent,
    "LLMPreEnrichmentAgent": LLMPreEnrichmentAgent,
    "DataEnrichmentAgent": DataEnrichmentAgent,
    "ThirdPartyEnrichmentAgent": ThirdPartyEnrichmentAgent,
    "AnonymizedIntentSignalAgent": AnonymizedIntentSignalAgent,
    "ScoringAgent": ScoringAgent,
    "EmailVerificationAgent": EmailVerificationAgent,
    "OutreachContentAgent": OutreachContentAgent,
    "OutreachExecutorAgent": OutreachExecutorAgent,
    "ResponseTrackerAgent": ResponseTrackerAgent,
    "FeedbackTrainerAgent": FeedbackTrainerAgent,
    "FeedbackApplyAgent": FeedbackApplyAgent,
}
