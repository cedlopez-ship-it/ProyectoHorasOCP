from flask import Flask, jsonify, request
import hmac
import json
import logging
import os
import time
import uuid

app = Flask(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

logging.info("ProyectoHoras v47 iniciado")

from config import JOB_TOKEN, ADMIN_EMAILS
from dataverse import validar_ingeniero
from handlers import (
    manejar_menu_inicio, manejar_carga_rapida, manejar_tipo, manejar_rapida_opp, manejar_rapida_confirmacion,
    manejar_conoce_opp, manejar_buscar_cliente, manejar_seleccionar_cliente,
    manejar_ingresar_opp, manejar_opp, manejar_fecha, manejar_horas, manejar_inicio,
    manejar_fin, manejar_comentario, manejar_confirmacion, manejar_cargar_mas,
    manejar_misma_opp, manejar_cruza_medianoche, manejar_comentario_medianoche,
    manejar_confirmacion_medianoche, manejar_mis_registros_continuar, manejar_admin_menu, manejar_admin_consultar_periodo
)
from jobs import ejecutar_recordatorio
from messages import MSG_TIPO, MSG_ADMIN_MENU
from session_manager import (
    sessions, processed_messages, cache_clientes, cache_opps, cambiar_estado,
    sesion_expirada, cleanup_sessions, cleanup_processed_messages, cleanup_cache
)
from webex import get_message, send_message


def iniciar_sesion_usuario(user, ingeniero, trace_id):
    sessions[user] = {
        "ingeniero_data": ingeniero
    }

    if user.lower() in ADMIN_EMAILS:
        cambiar_estado(sessions[user], "admin_menu", trace_id)
        return "admin_menu"

    cambiar_estado(sessions[user], "menu_inicio", trace_id)
    return "menu_inicio"


@app.route("/webhook", methods=["POST"])
def webhook():

    trace_id = str(uuid.uuid4())[:8]

    try:

        request_start = time.time()

        logging.info(f"[{trace_id}] webhook recibido")

        cleanup_sessions()

        cleanup_processed_messages()

        cleanup_cache(cache_clientes)

        cleanup_cache(cache_opps)

        cleanup_sessions()

        cleanup_processed_messages()

        data=request.json

        if data["resource"]!="messages":
            return "ok"

        message_id=data["data"]["id"]

        room=data["data"]["roomId"]

        user=data["data"]["personEmail"]

        logging.info(f"[{trace_id}] usuario {user}")

        # ------------------------------------------------
        # DEDUPLICACION
        # ------------------------------------------------

        now = time.time()

        processed_copy = processed_messages.copy()

        for mid, ts in processed_copy.items():

            if now - ts > 3600:
                del processed_messages[mid]

        if message_id in processed_messages:

            logging.info(f"[{trace_id}] mensaje duplicado")

            return "ok"

        processed_messages[message_id] = now

        # ------------------------------------------------

        if user.endswith("@webex.bot"):
            return "ok"

        msg = get_message(message_id)

        try:

            logging.info(
                f"[{trace_id}] MENSAJE WEBEX {json.dumps(msg)}"
            )

        except Exception:

            logging.info(
                f"[{trace_id}] MENSAJE WEBEX NO SERIALIZABLE"
            )

        text = msg.get(
            "text",
            ""
        ).lower().strip()

        logging.info(f"[{trace_id}] texto [{text}]")

        # ------------------------------------------------
        # CANCELAR GLOBAL
        # ------------------------------------------------

        if text in ["cancelar","cancel"]:

            if user in sessions:
                del sessions[user]

            send_message(
                room,
                "❌ Operación cancelada"
            )

            return "ok"

        # ------------------------------------------------
        # RESET GLOBAL
        # ------------------------------------------------

        if text in ["menu","inicio","reset"]:

            if user in sessions:
                del sessions[user]

            send_message(
                room,
                "👋 Bienvenido a ProyectoHoras\n\nEscriba:\n• horas\n• menu\n• inicio\n\npara comenzar."
            )

            return "ok"

        # ------------------------------------------------
        # INICIO
        # ------------------------------------------------

        if text in ["horas","hola","menu","inicio","cargar","registro"]:

            ingeniero = validar_ingeniero(user)

            if not ingeniero:

                send_message(
                    room,
                    "❌ No estás habilitado"
                )

                return "ok"

            estado_inicial = iniciar_sesion_usuario(
                user,
                ingeniero,
                trace_id
            )

            if estado_inicial == "admin_menu":
                nombre = ingeniero.get(
                    "hxp_ingenieronombre",
                    "Administrador"
                )
                send_message(
                    room,
                    MSG_ADMIN_MENU.format(nombre=nombre)
                )
            else:
                send_message(
                    room,
                    MSG_TIPO
                )

            return "ok"

        # ------------------------------------------------

        if user not in sessions:

            ingeniero = validar_ingeniero(user)

            if not ingeniero:
                send_message(room, "❌ No estás habilitado")
                return "ok"

            estado_inicial = iniciar_sesion_usuario(
                user,
                ingeniero,
                trace_id
            )

            if estado_inicial == "admin_menu":
                nombre = ingeniero.get(
                    "hxp_ingenieronombre",
                    "Administrador"
                )
                send_message(
                    room,
                    MSG_ADMIN_MENU.format(nombre=nombre)
                )
            else:
                send_message(room, MSG_TIPO)

            return "ok"

        # ------------------------------------------------
        # TIMEOUT SESION
        # ------------------------------------------------

        if sesion_expirada(sessions[user]):

            del sessions[user]

            send_message(
                room,
                "⌛ La sesión expiró"
            )

            return "ok"

        s=sessions[user]

        

        # =================================================
        # ROUTER ESTADOS
        # =================================================

        estado = s["estado"]

        ESTADOS = {

            "admin_menu": manejar_admin_menu,
            "admin_consultar_periodo": manejar_admin_consultar_periodo,
            "menu_inicio": manejar_menu_inicio,
            "tipo_real": manejar_tipo,
            "carga_rapida": manejar_carga_rapida,
            "rapida_opp": manejar_rapida_opp,
            "rapida_confirmacion": manejar_rapida_confirmacion,
            
            "conoce_opp": manejar_conoce_opp,
            "buscar_cliente": manejar_buscar_cliente,
            "seleccionar_cliente": manejar_seleccionar_cliente,
            "ingresar_opp": manejar_ingresar_opp,
            "opp": manejar_opp,
            "fecha": manejar_fecha,
            "horas": manejar_horas,
            "inicio": manejar_inicio,
            "fin": manejar_fin,
            "comentario": manejar_comentario,
            "confirmacion": manejar_confirmacion,
            "cargar_mas": manejar_cargar_mas,
            "misma_opp": manejar_misma_opp,
            "cruza_medianoche": manejar_cruza_medianoche,
            "comentario_medianoche": manejar_comentario_medianoche,
            "confirmacion_medianoche": manejar_confirmacion_medianoche,
            "mis_registros_continuar": manejar_mis_registros_continuar
        }

        # =================================================
        # SALIR DESDE MENUES
        # =================================================

        opciones_salir = {
            "admin_menu": 3,
            "admin_consultar_periodo": 5,
            "menu_inicio": 7,
            "carga_rapida": 4,
            "tipo_real": 4,
            "conoce_opp": 3,
            "rapida_confirmacion": 3,
            "confirmacion": 3,
            "cargar_mas": 3,
            "misma_opp": 3,
            "cruza_medianoche": 3,
            "confirmacion_medianoche": 3,
            "mis_registros_continuar": 3
        }

        opcion_salir = opciones_salir.get(estado)

        if estado == "seleccionar_cliente":
            opcion_salir = len(s.get("clientes", [])[:8]) + 2

        elif estado == "opp":
            opcion_salir = len(s.get("opps", [])) + 2

        if opcion_salir is not None and text == str(opcion_salir):

            nombre = s.get("ingeniero_data", {}).get(
                "hxp_ingenieronombre",
                "Ingeniero"
            )

            if user in sessions:
                del sessions[user]

            send_message(
                room,
                f"👋 Gracias {nombre}.\n\n🚀 Hasta la próxima."
            )

            return "ok"

        handler = ESTADOS.get(estado)

        if not handler:

            logging.error(
                f"[{trace_id}] estado inexistente {estado}"
            )

            return "ok"

        if estado in [
            "horas",
            "comentario",
            "confirmacion",
            "cargar_mas",
            "misma_opp",
            "rapida_confirmacion",
            "comentario_medianoche",
            "confirmacion_medianoche",
            "mis_registros_continuar",
            ]:

            handler(
                room,
                text,
                s,
                user,
                trace_id
            )

        else:

            handler(
                room,
                text,
                s,
                trace_id
            )

        return "ok"

    except Exception as e:

        logging.exception(
            f"[{trace_id}] ERROR GENERAL"
        )

        try:

            send_message(
                room,
                "❌ Error inesperado"
            )

        except:
            pass

        return "ok"

@app.route("/api/jobs/recordatorio-horas", methods=["POST"])
def ejecutar_job_recordatorio_horas():

    job_id = f"JOB-{str(uuid.uuid4())[:8]}"
    authorization = request.headers.get("Authorization", "")
    token_esperado = f"Bearer {JOB_TOKEN}"

    if not hmac.compare_digest(authorization, token_esperado):

        logging.warning(f"[{job_id}] Token de job inválido")

        return jsonify({
            "ok": False,
            "job_id": job_id,
            "error": "Unauthorized"
        }), 401

    resultado = ejecutar_recordatorio(job_id)

    return jsonify(resultado)

@app.route("/health")
def health():

    return "ok"

if __name__ == "__main__":

    port = int(os.environ.get("PORT", 10000))

    app.run(
        host="0.0.0.0",
        port=port
    )
