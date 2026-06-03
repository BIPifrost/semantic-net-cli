"""Tests for prompt construction."""

from __future__ import annotations

from semantic_net_cli.llm.prompts import build_system_prompt, build_user_prompt


def test_picture_aligned_agent_prompts_exist() -> None:
    for agent_name in [
        "topology_agent",
        "routing_agent",
        "traffic_agent",
        "performance_agent",
        "node_semantic_agent",
        "understanding_agent",
        "analysis_agent",
        "optimization_agent",
    ]:
        prompt = build_system_prompt(agent_name)
        assert agent_name in prompt
        assert "JSON" in prompt


def test_front_layer_prompts_do_not_allow_root_cause_or_optimization() -> None:
    for agent_name in [
        "topology_agent",
        "routing_agent",
        "traffic_agent",
        "performance_agent",
        "node_semantic_agent",
    ]:
        prompt = build_system_prompt(agent_name)
        assert "不要输出 root-cause" in prompt
        assert "不要输出 optimization" in prompt


def test_build_user_prompt_requires_chinese_when_possible() -> None:
    prompt = build_user_prompt("performance_agent", {"G_k": [{"id": "demo-001"}]})

    assert "尽量使用中文" in prompt
    assert "facts" in prompt
    assert "evidence" in prompt
    assert "demo-001" in prompt
