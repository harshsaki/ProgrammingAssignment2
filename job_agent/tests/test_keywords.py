from job_agent.generator.keywords import extract_keywords

JD = """
We are hiring a Head of AI to lead our Generative AI and Agentic AI
strategy. You'll own our LLM roadmap, work with LangChain and Azure
OpenAI, and drive MLOps best practices across the org.
"""


def test_extract_keywords_prefers_known_vocab():
    vocab = ["Generative AI", "Agentic AI", "LangChain", "Azure OpenAI", "MLOps", "Kubernetes"]
    keywords = extract_keywords(JD, known_vocab=vocab, top_n=10)
    assert "Generative AI" in keywords
    assert "LangChain" in keywords
    assert "Kubernetes" not in keywords  # not present in the JD text


def test_extract_keywords_never_crashes_on_empty_input():
    assert extract_keywords("", known_vocab=[]) == []
