import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
JOB_TOKEN = os.getenv("JOB_TOKEN")
WEBEX_API = "https://webexapis.com/v1"

TENANT_ID = os.getenv("TENANT_ID")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
DATAVERSE_URL = os.getenv("DATAVERSE_URL")

required_vars = [
    "BOT_TOKEN",
    "JOB_TOKEN",
    "TENANT_ID",
    "CLIENT_ID",
    "CLIENT_SECRET",
    "DATAVERSE_URL"
]

for var in required_vars:
    if not os.getenv(var):
        raise Exception(f"Falta variable de entorno: {var}")

SESSION_TIMEOUT = 1800
CACHE_TTL = 600


# Administradores del bot, separados por coma.
# Se puede sobrescribir en Render mediante la variable ADMIN_EMAILS.
ADMIN_EMAILS = {
    email.strip().lower()
    for email in os.getenv(
        "ADMIN_EMAILS",
        ""
    ).split(",")
    if email.strip()
}
