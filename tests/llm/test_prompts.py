"""Tests for prompt construction."""

from __future__ import annotations

from semantic_net_cli.llm.prompts import build_system_prompt, build_user_prompt


def test_build_system_prompt_prefers_chinese_output_guidance() -> None:
    prompt = build_system_prompt("global_state")

    assert "中文" in prompt
    assert "JSON" in prompt
    assert "agent" in prompt


def test_build_user_prompt_requires_chinese_when_possible() -> None:
    prompt = build_user_prompt("link_quality", {"snapshot_id": "demo-001"})

    assert "尽量使用中文" in prompt
    assert "findings" in prompt
    assert "evidence" in prompt
    assert "demo-001" in prompt
