import logging

from backend.config import get_settings
from . import gemini, groq, openrouter


logger = logging.getLogger("liwin-ai.llm")


def clean_answer(answer: str) -> str:
    """
    Clean common Unicode and mojibake characters.
    """

    if not answer:
        return ""

    # --------------------------------------------------------
    # Normal Unicode punctuation
    # --------------------------------------------------------

    replacements = {
        "’": "'",
        "‘": "'",
        "“": '"',
        "”": '"',
        "–": "-",
        "—": "-",
        "…": "...",
    }

    for old, new in replacements.items():
        answer = answer.replace(old, new)

    # --------------------------------------------------------
    # Common mojibake
    # --------------------------------------------------------

    mojibake = {
        "â€™": "'",
        "â€˜": "'",
        "â€œ": '"',
        "â€": '"',
        "â€“": "-",
        "â€”": "-",
        "â€¦": "...",
    }

    for old, new in mojibake.items():
        answer = answer.replace(old, new)

    # --------------------------------------------------------
    # Known broken forms appearing in this application
    # --------------------------------------------------------

    answer = answer.replace("âpowered", "-powered")
    answer = answer.replace("ârecognition", " recognition")
    answer = answer.replace("ârecord", "-record")
    answer = answer.replace("âtime", "-time")
    answer = answer.replace("âstack", "-stack")

    return answer.strip()


def is_valid_answer(answer: str) -> bool:

    if not answer:
        return False

    answer = answer.strip()

    if len(answer) < 10:
        return False

    invalid_responses = {
        "user safety: safe",
        "response safety: safe",
        "user safety: unsafe",
        "response safety: unsafe",
    }

    if answer.lower() in invalid_responses:
        return False

    return True


def generate_answer(prompt: str) -> tuple[str, str]:
    """Try explicitly configured providers in order without exposing their errors."""

    providers = {
        "gemini": gemini.generate,
        "openrouter": openrouter.generate,
        "groq": groq.generate,
    }

    attempted: list[str] = []
    for provider_name in get_settings().llm_providers:
        provider = providers.get(provider_name.lower())
        if provider is None:
            logger.warning("Skipping unknown LLM provider configuration: %s", provider_name)
            continue

        attempted.append(provider_name)
        try:
            answer = clean_answer(provider(prompt))
            if is_valid_answer(answer):
                return answer, provider_name
            logger.warning("Provider %s returned an invalid response.", provider_name)
        except Exception:
            logger.warning("Provider %s was unavailable.", provider_name, exc_info=True)

    if not attempted:
        raise RuntimeError("No supported LLM providers are configured.")
    raise RuntimeError("All configured generation providers are temporarily unavailable.")
