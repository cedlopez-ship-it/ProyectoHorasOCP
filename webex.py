import logging

from config import BOT_TOKEN, WEBEX_API
from http_client import http

headers = {
    "Authorization": f"Bearer {BOT_TOKEN}",
    "Content-Type": "application/json"
}

def send_message_to_email(email, mensaje):

    response = http.post(
        f"{WEBEX_API}/messages",
        headers=headers,
        json={
            "toPersonEmail": email,
            "markdown": mensaje
        },
        timeout=15
    )

    if response.status_code not in [200, 201]:

        logging.error(
            f"Error al enviar mensaje a {email}: "
            f"{response.status_code} {response.text}"
        )

        return False

    return True

def send_message(room,text):

    http.post(
        f"{WEBEX_API}/messages",
        headers=headers,
        json={
            "roomId": room,
            "markdown": text
        },
        timeout=15
    )

def send_file(room, filename, content, trace_id=None):

    headers_file = {
        "Authorization": f"Bearer {BOT_TOKEN}"
    }

    response = http.post(
        f"{WEBEX_API}/messages",
        headers=headers_file,
        data={"roomId": room},
        files={
            "files": (
                filename,
                content,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        },
        timeout=30
    )

    if response.status_code not in [200, 201]:

        logging.error(f"[{trace_id}] Error enviando archivo Webex: {response.text}")

        return False

    return True

def get_message(message_id):

    try:

        r = http.get(
            f"{WEBEX_API}/messages/{message_id}",
            headers=headers,
            timeout=15
        )

        logging.info(
            f"GET MESSAGE STATUS {r.status_code}"
        )

        logging.info(
            f"GET MESSAGE BODY {r.text}"
        )

        return r.json()

    except Exception as e:

        logging.exception(
            f"ERROR GET MESSAGE: {e}"
        )

        return {}
