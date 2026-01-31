from llmops_observability.pricing import calculate_cost, BEDROCK_PRICING


def test_calculate_cost_known_model():
    # pick any known model id
    model_id = next(iter(BEDROCK_PRICING.keys()))
    costs = calculate_cost(input_tokens=1000, output_tokens=2000, model_id=model_id)

    assert costs["input"] > 0
    assert costs["output"] > 0
    assert costs["total"] == round(costs["input"] + costs["output"], 6)


def test_calculate_cost_unknown_model_returns_zero():
    costs = calculate_cost(input_tokens=1000, output_tokens=2000, model_id="nonexistent-model")
    assert costs == {"input": 0.0, "output": 0.0, "total": 0.0}

