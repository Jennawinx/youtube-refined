import json
from dataclasses import dataclass
from openai import OpenAI
from youtube_refined.settings import LLM_API_KEY

client = OpenAI(api_key=LLM_API_KEY)
presentation = ["Vlog", "Music", "Podcast", "Commentary", "Talk show", "Info"]

topics = [
    "Actors",
    "Animation",
    "Anime and Manga",
    "Art",
    "ASMR",
    "Beauty",
    "Biography",
    "Cooking",
    "Culture",
    "Craft",
    "Day in the life",
    "Decor",
    "DIY",
    "Economy",
    "Educational",
    "Finance and Investing",
    "Fitness",
    "Food",
    "Gaming",
    "Innovation",
    "Interior Design",
    "Kpop",
    "Language arts",
    "Living",
    "Meme",
    "Mental Health",
    "Morning Routine",
    "Motivation",
    "Movie and TV",
    "Music",
    "Nature",
    "News",
    "Parenting",
    "Pets",
    "Politics",
    "Product Review",
    "Psychology",
    "Relaxation",
    "Science",
    "Shopping",
    "Singers",
    "Software Development",
    "Sports",
    "Technology",
    "Travel",
]

sample_output = [
    {
        "presentation": "Vlog",
        "topics": ["ASMR", "Art", "Nature"],
        "energy": 2,
        "educational": 1,
    }
]

system_message = f"""
Help categorize the videos.
For presentation select 1 of {", ".join(presentation)}.
For topics select any of {", ".join(topics)}.
For energy give 1-10 rating on how stimulating content is.
For educational give 1-10 rating on how useful content is for daily use or hobbies.
Example
{json.dumps(sample_output, separators=(',', ':'))}
"""

print(
    "=============================================\nInitialized openai client and system prompts:\n=============================================\n"
)
print(f"Categorize Video System Message:\n{system_message}")


"""
example inputs
[
  {
    "thumbnail_url": "https://i1.ytimg.com/vi/DA0wx41nWzw/hqdefault.jpg",
    "title": "Trying to teach Pichi literally any trick"
  },
  {
    "thumbnail_url": "https://i1.ytimg.com/vi/8QsHpDjzunY/hqdefault.jpg",
    "title": "Raising kids: the Japanese or American way?"
  },
  {
    "thumbnail_url": "https://i.ytimg.com/vi/JstGCPsj9wg/hq720.jpg",
    "title": "How Tech Companies Lie to You."
  },
  {
    "thumbnail_url": "https://i.ytimg.com/vi/cTymndypryw/hq720.jpg",
    "title": "Quiet Night Reset | 夜の静けさ – Relaxing Music to Unwind & Clear Your Mind"
  }
]
"""


@dataclass
class VideoDetails:
    thumbnail_url: str
    title: str


@dataclass
class CategorizedVideo:
    presentation: str
    topics: list[str]
    energy: int = 0
    educational: int = 0

# TODO: support many to save tokens
def categorize_video(list_of_videos: list[VideoDetails]) -> list[CategorizedVideo]:
    response = client.responses.create(
        # model="gpt-5.4-nano", # Better with instructions
        model="gpt-4o-mini",
        instructions=system_message,
        input=json.dumps(list_of_videos),
        reasoning={},
        max_output_tokens=1024,
        store=True,
        include=["web_search_call.action.sources"],
    )
    print(response)
    return response.output
