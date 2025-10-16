import pytest


class FakeLLM:
    def invoke(self, messages):
        class R:
            # Simulate an LLM that references a valid doc id (I10) but also an external
            # unsupported reference [EXTERNAL] which should be stripped/replaced.
            content = "MOCK ICD ANSWER: Evidence suggests hypertension. I10 and [EXTERNAL]."

        return R()


class FakeSearch:
    def __init__(self, index, query, top=5, vector_field=None, **kwargs):
        self.index = index
        self.query = query
        self.top = top
        self.vector_field = vector_field

    def run(self):
        return [
            {
                "score": 0.95,
                "document": {
                    "id": "I10",
                    "title": "Essential (primary) hypertension",
                    "content": "Elevated blood pressure... (ICD-10 I10)",
                },
            }
        ]


def test_icd_agent_process(monkeypatch):
    # Patch the ICD agent LLM factory to use a fake LLM
    monkeypatch.setattr("modules.agents.icd_agent.IcdAgent._create_llm", lambda self: FakeLLM())

    # Patch the Search helper used by the ICD agent
    import modules.search_tool as search_tool_mod

    monkeypatch.setattr(search_tool_mod, "Search", FakeSearch)

    # Import and run the agent
    from modules.agents.icd_agent import IcdAgent

    agent = IcdAgent(index="pcornet-icd-index")
    resp = agent.process("What is ICD code I10?")

    assert isinstance(resp, dict)
    assert "processed_response" in resp
    assert "MOCK ICD ANSWER" in resp["processed_response"]
    # Post-processing should normalize I10 to [I10] and replace [EXTERNAL] with [UNSUPPORTED_CITATION]
    assert "[I10]" in resp["processed_response"]
    assert "[UNSUPPORTED_CITATION]" in resp["processed_response"]


def test_icd_agent_with_history(monkeypatch):
    # Patch LLM and Search again
    monkeypatch.setattr("modules.agents.icd_agent.IcdAgent._create_llm", lambda self: FakeLLM())
    import modules.search_tool as search_tool_mod
    monkeypatch.setattr(search_tool_mod, "Search", FakeSearch)

    # Create a minimal fake conversation history with required API
    class FakeHistory:
        def get_langchain_messages(self):
            return []

    from modules.agents.icd_agent import IcdAgent

    agent = IcdAgent(index="pcornet-icd-index")
    resp = agent.process_with_history("Please explain I10.", FakeHistory())

    assert isinstance(resp, str)
    # Post-processing should normalize I10 to [I10] and replace [EXTERNAL] with [UNSUPPORTED_CITATION]
    assert "MOCK ICD ANSWER" in resp
    assert "[I10]" in resp
    assert "[UNSUPPORTED_CITATION]" in resp


def test_heart_disease_concept_set(monkeypatch):
    # Patch LLM to ensure it's not called when concept set is served locally
    class SilentLLM:
        def invoke(self, messages):
            class R:
                content = "SHOULD_NOT_BE_CALLED"
            return R()

    monkeypatch.setattr("modules.agents.icd_agent.IcdAgent._create_llm", lambda self: SilentLLM())

    from modules.agents.icd_agent import IcdAgent
    agent = IcdAgent()

    resp = agent.process("Provide the Heart Disease Concept Set")

    # Ensure the response is a dictionary with the expected structure
    assert isinstance(resp, dict)
    assert "processed_response" in resp
    assert "data" in resp
    
    # Check the processed response contains expected codes and citations
    processed_response = resp["processed_response"]
    assert "[I20]" in processed_response  # Citations should be bracketed
    assert "[I21]" in processed_response
    assert "[I50]" in processed_response
    assert "PCORnet" in processed_response or "PCORnet Documentation" in processed_response

    # last_retrieved_documents should be populated with the concept set entries
    assert isinstance(agent.last_retrieved_documents, list)
    assert any((d.get("document", {}).get("id") == "I20") for d in agent.last_retrieved_documents)
