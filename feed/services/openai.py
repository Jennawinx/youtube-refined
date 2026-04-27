import json
from dataclasses import dataclass
from openai import OpenAI
from youtube_refined.settings import LLM_API_KEY

client = OpenAI(api_key=LLM_API_KEY)
presentation = ["Vlog", "Music", "Podcast", "Commentary", "Talk show", "Info"]

topics = [
    "Educational",
    "Language arts",
    "Finance and Investing",
    "Technology",
    "Science",
    "Innovation",
    "Psychology",
    "DIY",
    "Pets",
    "Mental Health",
    "Animation",
    "Software Development",
    "Beauty",
    "Day in the life",
    "Travel",
    "Decor",
    "Biography",
    "Parenting",
    "Shopping",
    "Product Review",
    "Interior Design",
    "Gaming",
    "Movie and TV",
    "Anime and Manga",
    "Art",
    "Meme",
    "ASMR",
    "Food",
    "News",
    "Politics",
    "Economy",
    "Cooking",
    "Fitness",
    "Music",
    "Sports",
    "Living",
    "Kpop",
    "Actors",
    "Singers",
    "Nature",
]

sample_output = {
    "presentation": "Vlog",
    "topics": ["ASMR", "Art", "Nature"],
    "energy": 2,
}

system_message = f"""
Help categorize the video.
For presentation select 1 of {", ".join(presentation)}.
For topics select any of {", ".join(topics)}.
For energy give 1-10 rating on how stimulating content is.
Example
{json.dumps(sample_output, separators=(',', ':'))}
"""

print(
    "=============================================\nInitialized openai client and system prompts:\n=============================================\n"
)
print(f"Categorize Video System Message:\n{system_message}")


@dataclass
class CategorizeVideoOutput:
    presentation: str
    topics: list[str]
    energy: int = 0


def categorize_video(url: str, title: str) -> CategorizeVideoOutput:
    response = client.responses.create(
        model="gpt-4o-mini",
        instructions=system_message,
        input=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": "Analyze this video: Title: 'Raising kids: the Japanese or American way?'",
                    },
                    {
                        "type": "input_image",
                        "image_url": "https://i1.ytimg.com/vi/8QsHpDjzunY/hqdefault.jpg",
                    },
                ],
            }
        ],
        reasoning={},
        max_output_tokens=1024,
        store=True,
        include=["web_search_call.action.sources"],
    )
    print(response)
    return response.output
