import logging
import time

from config import DATAVERSE_URL
from dataverse import get_dataverse_token
from http_client import http
from messages import MSG_RECORDATORIO_SEMANAL
from webex import send_message_to_email

def obtener_ingenieros_activos(job_id):

    token = get_dataverse_token()

    if not token:
        logging.error(f"[{job_id}] No se pudo obtener token de Dataverse")
        return None

    headers_dv = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }

    url = (
        f"{DATAVERSE_URL}/api/data/v9.2/hxp_ingenieros"
        "?$select=hxp_ingenieroid,hxp_ingenieronombre,hxp_ingenieromail"
        "&$filter=statecode eq 0"
    )

    ingenieros = []

    while url:

        response = http.get(
            url,
            headers=headers_dv,
            timeout=15
        )

        if response.status_code != 200:

            logging.error(
                f"[{job_id}] Error al consultar ingenieros activos: "
                f"{response.status_code} {response.text}"
            )

            return None

        data = response.json()

        for ingeniero in data.get("value", []):

            if ingeniero.get("hxp_ingenieromail"):
                ingenieros.append(ingeniero)

        url = data.get("@odata.nextLink")

    logging.info(
        f"[{job_id}] Ingenieros activos obtenidos: {len(ingenieros)}"
    )

    return ingenieros

def enviar_recordatorio_semanal(ingeniero, job_id):

    email = ingeniero["hxp_ingenieromail"]

    if not send_message_to_email(email, MSG_RECORDATORIO_SEMANAL):
        logging.error(f"[{job_id}] Error al enviar recordatorio a {email}")
        return False

    logging.info(
        f"[{job_id}] Recordatorio enviado a {email}"
    )

    return True

def ejecutar_recordatorio(job_id):

    inicio = time.time()
    enviados = 0
    errores = 0

    logging.info(f"[{job_id}] Inicio recordatorio semanal")

    ingenieros = obtener_ingenieros_activos(job_id)

    if ingenieros is None:

        return {
            "ok": False,
            "job_id": job_id,
            "ingenieros": 0,
            "enviados": 0,
            "errores": 1,
            "duracion_segundos": round(time.time() - inicio, 2)
        }

    for ingeniero in ingenieros:

        email = ingeniero.get("hxp_ingenieromail", "sin email")

        try:

            if enviar_recordatorio_semanal(
                ingeniero,
                job_id
            ):
                enviados += 1
            else:
                errores += 1

        except Exception:

            errores += 1

            logging.exception(
                f"[{job_id}] Error al enviar recordatorio a {email}"
            )

    duracion = round(time.time() - inicio, 2)

    logging.info(
        f"[{job_id}] Fin recordatorio semanal. "
        f"Ingenieros: {len(ingenieros)}. Enviados: {enviados}. "
        f"Errores: {errores}. Duración: {duracion}s"
    )

    return {
        "ok": errores == 0,
        "job_id": job_id,
        "ingenieros": len(ingenieros),
        "enviados": enviados,
        "errores": errores,
        "duracion_segundos": duracion
    }
