from __future__ import annotations

from webresearch.pipeline.runtime import ExecutionResult, calculate_cost


def test_calculate_cost_known_model() -> None:
    cost = calculate_cost(1_000_000, 500_000, "gpt-4.1")
    # input: 1M * $2/1M = $2.00, output: 500k * $8/1M = $4.00
    assert cost == 6.00


def test_calculate_cost_mini_model() -> None:
    cost = calculate_cost(1_000_000, 500_000, "gpt-4.1-mini")
    # input: 1M * $0.40/1M = $0.40, output: 500k * $1.60/1M = $0.80
    assert cost == 1.20


def test_calculate_cost_o4_mini() -> None:
    cost = calculate_cost(500_000, 250_000, "o4-mini")
    # input: 500k * $1.10/1M = $0.55, output: 250k * $4.40/1M = $1.10
    assert cost == 1.65


def test_calculate_cost_unknown_model() -> None:
    cost = calculate_cost(1_000_000, 500_000, "unknown-model")
    assert cost == 0.0


def test_calculate_cost_zero_tokens() -> None:
    cost = calculate_cost(0, 0, "gpt-4.1")
    assert cost == 0.0


def test_execution_result_holds_values() -> None:
    result = ExecutionResult(
        output={"key": "value"},
        input_tokens=100,
        output_tokens=50,
        model="gpt-4.1-mini",
    )
    assert result.output == {"key": "value"}
    assert result.input_tokens == 100
    assert result.output_tokens == 50
    assert result.model == "gpt-4.1-mini"
