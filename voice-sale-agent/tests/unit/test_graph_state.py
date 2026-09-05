"""验证 Worker 错误映射和父图错误 reducer 的上限。

这样长会话即使连续降级，也不会让 Checkpoint 中的 errors 无限增长。
"""

from app.agents.contracts import IntentUnderstandingOutput
from app.graph.state import merge_agent_errors


def test_worker_error_maps_to_structured_supervisor_error():
    patch = IntentUnderstandingOutput(
        current_intent="OUT_OF_SCOPE",
        error="intent_understanding_failed",
    ).to_state_patch()

    assert patch["errors"] == [
        {
            "agent": "intent",
            "code": "intent_understanding_failed",
            "recoverable": True,
        }
    ]


def test_error_reducer_keeps_a_bounded_history():
    current = [
        {"agent": "intent", "code": f"old-{index}", "recoverable": True}
        for index in range(49)
    ]
    new = [
        {"agent": "order", "code": "new-1", "recoverable": True},
        {"agent": "order", "code": "new-2", "recoverable": True},
    ]

    merged = merge_agent_errors(current, new)

    assert len(merged) == 50
    assert merged[-1]["code"] == "new-2"
    assert merged[0]["code"] == "old-1"
