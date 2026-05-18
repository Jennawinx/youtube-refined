from django.apps import AppConfig

class FeedConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'feed'

    def ready(self):
        from feed.services.schedule import get_rules_schedule
        from feed.services.categorizer_llm import LLM_SYS_PROMPT_CATEGORIZE

        print(
            "\n=============================================\nInitialized rules cache:                    \n=============================================\n"
        )
        # Preload rules into cache on startup
        get_rules_schedule()
    
        print(
            "\n=============================================\nInitialized openai client and system prompts:\n=============================================\n"
        )
        print(f"Categorize Video System Message:\n{LLM_SYS_PROMPT_CATEGORIZE}")