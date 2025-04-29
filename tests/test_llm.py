from addon.llm import LLM


def test_llm_engine_collab():
    # Given
    llm = LLM()
    prompt = "Respond with one word. The Italian word for Hello is: "

    # When
    result = llm.run(prompt)

    # Then
    assert result == " Ciao"
