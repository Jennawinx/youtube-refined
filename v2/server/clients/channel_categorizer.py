import json
import re
from openai import OpenAI
from model import COMMON_TOPICS
from config import LLM_API_KEY

SAMPLE_OUTPUT = ["ASMR", "Art", "Nature"]

LLM_SYS_PROMPT = f"""
Help determine the main topics of a YouTube channel based on its description.
For topics select 2-8 options from {", ".join(COMMON_TOPICS)}.
{json.dumps(SAMPLE_OUTPUT, separators=(',', ':'))}
Return result as a JSON array
"""


class ChannelCategorizer:

    _client: OpenAI | None = None

    def __init__(self):
        if not ChannelCategorizer._client:
            ChannelCategorizer._client = OpenAI(api_key=LLM_API_KEY)
            print("Initialized Channel Categorizer with prompt: \n")
            print(LLM_SYS_PROMPT, "\n")

    def determine_channel_topics(self, description: str) -> list[str]:

        if not description:
            return []

        response = ChannelCategorizer._client.responses.create(
            # model="gpt-5.4-nano", # Better with instructions
            model="gpt-4o-mini",
            instructions=LLM_SYS_PROMPT,
            input=description[:800],  # Truncate to fit token limits
            reasoning={},
            max_output_tokens=1024,
            store=True,
        )

        responseText = response.output[0].content[0].text

        print("\n\nresponseText", responseText)

        try:
            json_snippet = re.search(
                r"```json\s*(.*?)\s*```", responseText, re.DOTALL
            ).group(1)
            print("\nChannel Categorization JSON snippet:\n", json_snippet, "\n")
            results = json.loads(json_snippet)
            return results

        except Exception as exc:
            print(f"Error parsing channel categorization response: {exc}")
            print(f"Raw response content: {response.output[0].content[0].text}")
            raise exc
