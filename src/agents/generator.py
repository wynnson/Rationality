from enums import Models


def generate_gemma(client, query: str) -> str: 
    response = client.models.generate_content(
        model = Models.Gemma4,
        contents = query
    )

    return response.text