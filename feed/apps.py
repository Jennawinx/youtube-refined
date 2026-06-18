from django.apps import AppConfig

class FeedConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'feed'

    def ready(self):
        from feed.services.llm_video_categorizer import LLM_SYS_PROMPT_CATEGORIZE
    
        print(
            "\n=============================================\nInitialized openai client and system prompts:\n=============================================\n"
        )
        print(f"Categorize Video System Message:\n{LLM_SYS_PROMPT_CATEGORIZE}")