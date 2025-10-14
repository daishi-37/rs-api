import os
from dotenv import load_dotenv

load_dotenv()


# Slack
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "https://hooks.slack.com/services/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")

# Environment
PORT: int = int(os.getenv("PORT"))
BASE_URL: str = str(os.getenv("BASE_URL"))
BASE_PATH: str = str(os.getenv("BASE_PATH"))
API_PATH = "/api"
DEBUG: bool = str(os.getenv("DEBUG")).lower() == "true"

# Logging
LOG_DIR = "logs"
LOG_FILENAME_APP = "app.log"
LOG_FILE_APP = os.path.join(LOG_DIR, LOG_FILENAME_APP)
LOG_FILENAME_HC = "healthchecks.log"
LOG_FILE_HC = os.path.join(LOG_DIR, LOG_FILENAME_HC)
HEALTHCHECKS_BASE_URL = os.getenv("HEALTHCHECKS_BASE_URL")
HEALTHCHECKS_PING_KEY = os.getenv("HEALTHCHECKS_PING_KEY")
HEALTHCHECKS_SLUG_PREFIX = "rs-api"

# Upload Directory
UPLOAD_DIR: str = str(os.getenv("UPLOAD_DIR"))
