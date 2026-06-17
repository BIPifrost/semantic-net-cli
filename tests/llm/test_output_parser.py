import pytest

from semantic_net_cli.llm.output_parser import AgentOutputParseError, parse_agent_json_output


def test_parse_agent_json_output_reports_agent_name_and_raw_content() -> None:
    raw_content = '{"summary": "unterminated'

    with pytest.raises(AgentOutputParseError) as exc_info:
        parse_agent_json_output("analysis_agent", {"content": raw_content})

    exc = exc_info.value
    assert exc.agent_name == "analysis_agent"
    assert exc.raw_content == raw_content
    assert "Unterminated string" in exc.parse_error
    assert "agent=analysis_agent" in str(exc)


def test_parse_agent_json_output_returns_valid_payload() -> None:
    payload = parse_agent_json_output("understanding_agent", {"content": '{"status": "degraded"}'})

    assert payload == {"status": "degraded"}
