"""Run the example through CrewAI with scripted model replies."""

import importlib.util
import json
from pathlib import Path

from crewai.llms.base_llm import BaseLLM
from test_tool import DOC, QUOTE, TEST_KEY, FakeSDK

from faxforagents_crewai import tool as module


def test_example_prepares_and_quotes_without_sending(monkeypatch):
    path = Path(__file__).resolve().parents[1] / "examples/fax_crew.py"
    spec = importlib.util.spec_from_file_location("fax_crew_example", path)
    example = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(example)
    fake = FakeSDK()
    fake.responses = {
        "documents.create": {"id": DOC, "page_count": 1},
        "quotes.create": {"id": QUOTE, "amount_micro": 0, "billable_pages": 1},
    }
    monkeypatch.setattr(module, "Client", fake.factory())
    monkeypatch.setenv("FAXFORAGENTS_API_KEY", TEST_KEY)

    class ScriptedModel(BaseLLM):
        def __init__(self):
            super().__init__(model="offline-script")
            self.replies = iter(
                [
                    "Thought: Prepare the requested document.\nAction: prepare_fax\nAction Input: "
                    + json.dumps(
                        {"text": "Sandbox fax example", "idempotency_key": "test-prepare"}
                    ),
                    "Thought: Quote the document.\nAction: quote_fax\nAction Input: "
                    + json.dumps(
                        {"document_id": DOC, "to": "+15550000001", "idempotency_key": "test-quote"}
                    ),
                    "Thought: Report the quote.\n"
                    f"Final Answer: Quote {QUOTE}, one page, sandbox price zero.",
                ]
            )

        def call(self, messages, **kwargs):
            return next(self.replies)

    crew = example.build_crew(ScriptedModel(), "test")
    assert {t.name for t in crew.agents[0].tools} == {"prepare_fax", "quote_fax"}
    result = crew.kickoff()
    assert QUOTE in result.raw
    assert [path for _, path, _ in fake.calls] == ["documents.create", "quotes.create"]
    assert fake.calls[-1][2]["to"] == "+15550000001"
    assert fake.calls[0][2]["idempotency_key"] == "test-prepare"
    assert fake.calls[1][2]["idempotency_key"] == "test-quote"
