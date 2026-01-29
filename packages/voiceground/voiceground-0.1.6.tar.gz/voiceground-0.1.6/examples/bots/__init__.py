"""Bot implementations for Voiceground examples."""

# Note: Using relative imports to avoid issues when examples are run directly
try:
    from .friendly_assistant_bot import run_friendly_assistant_bot
    from .restaurant_bot import run_restaurant_bot
except ImportError:
    # Fallback for when running as script
    from examples.bots.friendly_assistant_bot import run_friendly_assistant_bot
    from examples.bots.restaurant_bot import run_restaurant_bot

__all__ = ["run_restaurant_bot", "run_friendly_assistant_bot"]
