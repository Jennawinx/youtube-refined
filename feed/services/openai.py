from openai import OpenAI
import json
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
For topics select any of {", ".join(presentation)}.
For energy give 1-10 rating on how stimulating content is.
Example
{json.dumps(sample_output, separators=(',', ':'))}
"""

print(system_message)

response = client.responses.create(
    model="gpt-4o-mini",
    instructions=system_message,
    input=[
        {
            "thumbnail_url": "https://i1.ytimg.com/vi/8QsHpDjzunY/hqdefault.jpg",
            "title": "Raising kids: the Japanese or American way?",
        }
    ],
    # text={"format": {"type": "text"}},
    reasoning={},
    max_output_tokens=1024,
    store=True,
    include=["web_search_call.action.sources"],
)
