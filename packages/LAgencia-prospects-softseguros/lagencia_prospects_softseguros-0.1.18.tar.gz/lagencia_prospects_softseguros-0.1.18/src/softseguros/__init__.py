from dotenv import load_dotenv

load_dotenv()

from softseguros.config.settings import get_settings

config = get_settings()
