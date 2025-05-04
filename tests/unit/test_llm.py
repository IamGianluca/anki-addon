from addon.llm import FakeLLM


def test_llm_engine_collab():
    # Given
    llm = FakeLLM()
    prompt = "Respond with one word. The Italian word for Hello is: "

    # When
    result = llm.run(prompt)

    # Then
    assert result == "ciao"
