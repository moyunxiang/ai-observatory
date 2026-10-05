"""LLM client interface.

Each category is sent as its own single-turn request (no shared history), so
answers are independent. No provider is wired up yet: the API, model and
sampling settings must be confirmed before any paid call is made.
"""

# Providers with a working implementation in query_llm(). Empty until configured.
SUPPORTED_PROVIDERS: set[str] = set()

PROMPT_TEMPLATE = (
    "What are the best-known and most representative brands for {category}? "
    "List exactly 10 brands."
)


def build_prompt(category_name: str) -> str:
    return PROMPT_TEMPLATE.format(category=category_name)


def query_llm(prompt: str, provider: str, model: str, temperature: float) -> str:
    """Send one independent single-turn prompt and return the raw text answer."""
    raise NotImplementedError(
        f"Provider '{provider}' is not configured yet. "
        "Implement the API call here once provider/model/key are confirmed."
    )
