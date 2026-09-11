from datetime import datetime, timedelta

from dataverse import (
    buscar_clientes, get_opp_por_numero, get_opps_por_cliente, guardar_horas_dataverse
)
from messages import (
    MSG_TIPO, MSG_BUSCAR_CLIENTE, MSG_INGRESAR_OPP, MSG_FECHA, MSG_HORAS,
    MSG_HORA_INICIO, MSG_HORA_FIN, MSG_CLIENTE_NO_ENCONTRADO,
    MSG_CLIENTE_DEMASIADOS, MSG_CLIENTE_SIN_OPPS, MSG_HORAS_RANGO,
    MSG_HORAS_NORMALES_MAXIMO, MSG_COMENTARIO, MSG_CARGA_RAPIDA, MSG_ADMIN_MENU, MSG_ADMIN_CONSULTAR_PERIODO
)
from reportes import manejar_mis_registros, generar_y_enviar_excel_equipo
from session_manager import sessions, cambiar_estado
from utils import (
    validar_fecha, validar_hora, validar_horas_normales, calcular_horas,
    normalizar_cantidad_horas, formatear_horas, menu_clientes, menu_opps, es_volver, opcion_valida, resumen, resumen_medianoche
)
from webex import send_message

def manejar_cargar_mas(room, text, s, user, trace_id):

    if text == "1":

        if s.get("opp"):

            cambiar_estado(
                s,
                "misma_opp",
                trace_id
            )

            send_message(
                room,
                f"""¿Desea utilizar la misma OPP?

📂 {s.get('opp','')}
🏢 {s.get('cliente','')}

1️⃣ Sí
2️⃣ No
3️⃣ 🚪 Salir"""
            )

            return

        ingeniero = s["ingeniero_data"]

        sessions[user] = {
            "ingeniero_data": ingeniero
        }

        cambiar_estado(
            sessions[user],
            "menu_inicio",
            trace_id
        )

        send_message(room, MSG_TIPO)

        return

    elif text == "2":

        nombre = s["ingeniero_data"].get(
            "hxp_ingenieronombre",
            "Ingeniero"
        )

        send_message(
            room,
            f"👋 Gracias {nombre}.\n\n🚀 Hasta la próxima."
        )

        if user in sessions:
            del sessions[user]

        return

    send_message(
        room,
        "⚠️ Opción inválida\n\n1️⃣ Sí\n2️⃣ No\n3️⃣ 🚪 Salir"
    )

def manejar_menu_inicio(room, text, s, trace_id):

    opciones = {
        "1": "soporte_normal",
        "2": "soporte_extra",
        "3": "implementacion_normal",
        "4": "implementacion_extra",
        "5": "consultoria"
    }

    if text == "6":
        manejar_mis_registros(room, s, trace_id)
        return

    if text not in opciones:
        send_message(room, "⚠️ Opción inválida")
        return

    s["tipo"] = opciones[text]

    if s["tipo"] in ("soporte_normal", "implementacion_normal"):
        cambiar_estado(s, "carga_rapida", trace_id)
        send_message(room, MSG_CARGA_RAPIDA)
        return

    _continuar_despues_tipo(room, s, trace_id)


def manejar_carga_rapida(room, text, s, trace_id):

    if text == "1":
        s["registros_rapidos"] = []

        cambiar_estado(s, "rapida_opp", trace_id)

        send_message(
            room,
            """
━━━━━━━━━━━━━━━━━━
⚡ CARGA RÁPIDA
━━━━━━━━━━━━━━━━━━

Ingrese uno o más registros.

Formato:
OPP FECHA HORAS

Ejemplos:
8888 20-07-2026 8
9999 20-07-2026 4

Cuando finalice escriba:
FIN
"""
        )
        return

    if text == "2":
        _continuar_despues_tipo(room, s, trace_id)
        return

    if text == "3":
        s.pop("tipo", None)
        cambiar_estado(s, "menu_inicio", trace_id)
        send_message(room, MSG_TIPO)
        return

    send_message(room, "⚠️ Opción inválida\n\n1️⃣ Sí\n2️⃣ No\n3️⃣ ◀️ Volver\n4️⃣ 🚪 Salir")


def _continuar_despues_tipo(room, s, trace_id):

    if s.get("reutilizar_opp"):
        s.pop("reutilizar_opp", None)
        cambiar_estado(s, "fecha", trace_id)
        send_message(room, MSG_FECHA)
        return

    cambiar_estado(s, "conoce_opp", trace_id)
    send_message(room, "¿Conoces la OPP?\n1️⃣ Sí\n2️⃣ No\n3️⃣ 🚪 Salir")


def manejar_tipo(room, text, s, trace_id):
    # Se conserva por compatibilidad con imports/routeres antiguos.
    manejar_menu_inicio(room, text, s, trace_id)


def manejar_rapida_opp(room, text, s, trace_id):

    if text.upper() == "FIN":

        registros = s.get("registros_rapidos", [])

        if len(registros) == 0:
            send_message(room, "⚠️ No hay registros cargados")
            return

        total_horas = sum(r["horas"] for r in registros)

        resumen_txt = "📋 RESUMEN CARGA RAPIDA\n\n"

        for i,r in enumerate(registros,1):
            resumen_txt += f"{i}. {r['opp']} | {r['fecha']} | {formatear_horas(r['horas'])}h | {r['cliente']}\n"

        resumen_txt += f"\n📦 Registros: {len(registros)}"
        resumen_txt += f"\n⏱️ Horas totales: {formatear_horas(total_horas)}"
        resumen_txt += "\n\n1️⃣ Confirmar\n2️⃣ Cancelar\n3️⃣ 🚪 Salir"

        cambiar_estado(
            s,
            "rapida_confirmacion",
            trace_id
        )
        send_message(room,resumen_txt)
        return

    partes = text.split()

    if len(partes) != 3:
        send_message(room,"⚠️ Formato inválido. Use: OPP FECHA HORAS o FIN")
        return

    opp_txt, fecha_txt, horas_txt = partes

    opps = get_opp_por_numero(opp_txt)

    if len(opps) == 0:
        send_message(room,f"❌ La OPP {opp_txt} no existe")
        return

    ok_fecha, mensaje_fecha = validar_fecha(fecha_txt)
    if not ok_fecha:
        send_message(room,mensaje_fecha)
        return

    horas = normalizar_cantidad_horas(horas_txt)

    if horas is None:
        send_message(room, "⚠️ Solo se permiten horas enteras o medias horas.\n\nEjemplos válidos: 2, 2.5, 2,5")
        return

    if horas < 0.5 or horas > 24:
        send_message(room, MSG_HORAS_RANGO)
        return

    if not validar_horas_normales(horas):
        send_message(room, MSG_HORAS_NORMALES_MAXIMO)
        return

    opp = opps[0]

    s.setdefault("registros_rapidos", []).append({
        "opp": opp["codigo"],
        "cliente": opp["cliente"],
        "fecha": fecha_txt,
        "horas": horas
    })

    send_message(room,f"✅ Registro agregado ({len(s['registros_rapidos'])}). Ingrese otro o FIN")

def manejar_rapida_confirmacion(room, text, s, user, trace_id):

    if text == "1":

        errores = 0

        for r in s.get("registros_rapidos",[]):

            tmp = dict(s)
            tmp["opp"] = r["opp"]
            tmp["cliente"] = r["cliente"]
            tmp["fecha"] = r["fecha"]
            tmp["horas"] = r["horas"]
            tmp["comentario"] = ""
            tmp["tipo"] = s["tipo"]

            ok, _ = guardar_horas_dataverse(user,tmp,trace_id)

            if not ok:
                errores += 1

        if errores == 0:
            cambiar_estado(s,"cargar_mas",trace_id)
            send_message(room,"✅ Lote registrado correctamente\n\n¿Desea cargar más horas?\n\n1️⃣ Sí\n2️⃣ No")
        else:
            send_message(room,f"⚠️ Finalizado con {errores} errores")

        return

    if text == "2":
        send_message(room,"❌ Cancelado")
        if user in sessions:
            del sessions[user]
        return

    send_message(room,"⚠️ Opción inválida")



def manejar_conoce_opp(room, text, s, trace_id):

    if text=="1":

        cambiar_estado(
            s,
            "ingresar_opp",
            trace_id
        )

        send_message(room, MSG_INGRESAR_OPP)

    elif text=="2":

        cambiar_estado(
            s,
            "buscar_cliente",
            trace_id
        )

        send_message(room, MSG_BUSCAR_CLIENTE)

    else:

        send_message(room, "⚠️ Opción inválida")

def manejar_buscar_cliente(room, text, s, trace_id):

    if len(text) < 3:

        send_message(
            room,
            "⚠️ Ingrese al menos 3 letras"
        )

        return

    s["clientes"] = buscar_clientes(text)

    if len(s["clientes"]) == 0:

        send_message(
            room,
            MSG_CLIENTE_NO_ENCONTRADO
        )

        return

    if len(s["clientes"]) >= 9:

        send_message(
            room,
            MSG_CLIENTE_DEMASIADOS.format(
                cantidad=len(s["clientes"])
            )
        )

        return

    cambiar_estado(
        s,
        "seleccionar_cliente",
        trace_id
    )

    if len(s["clientes"]) == 1:

        manejar_seleccionar_cliente(
            room,
            "1",
            s,
            trace_id
        )

        return

    send_message(
        room,
        menu_clientes(s["clientes"],"Seleccionar Cliente")
    )

def manejar_seleccionar_cliente(room, text, s, trace_id):

    if (
        (len(s["clientes"]) < 9 and es_volver(text, s["clientes"]))
        or text.strip().lower() == "volver"
    ):

        cambiar_estado(
            s,
            "buscar_cliente",
            trace_id
        )

        send_message(room, MSG_BUSCAR_CLIENTE)

        return

    if not opcion_valida(text, s["clientes"]):

        send_message(room, "⚠️ Opción inválida")

        return

    opcion = int(text)

    cliente = s["clientes"][opcion-1]

    s["cliente"]=cliente["nombre"]

    s["opps"]=get_opps_por_cliente(
        cliente["id"]
    )

    if len(s["opps"]) == 0:

        send_message(
            room,
            MSG_CLIENTE_SIN_OPPS
        )

        return

    s["volver_opp"]="seleccionar_cliente"

    cambiar_estado(
        s,
        "opp",
        trace_id
    )

    send_message(
        room,
        menu_opps(s["opps"],"Seleccionar OPP")
    )

def manejar_ingresar_opp(room, text, s, trace_id):

    # Si venimos de una OPP inválida, procesamos el menú de opciones.
    if s.get("opp_invalida"):
        if text == "1":
            s.pop("opp_invalida", None)
            send_message(room, MSG_INGRESAR_OPP)
            return

        if text == "2":
            s.pop("opp_invalida", None)
            cambiar_estado(
                s,
                "conoce_opp",
                trace_id
            )
            send_message(
                room,
                "¿Conoces la OPP?\n1️⃣ Sí\n2️⃣ No\n3️⃣ 🚪 Salir"
            )
            return

        send_message(
            room,
            "⚠️ Opción inválida\n\n"
            "1️⃣ Intentar nuevamente\n"
            "2️⃣ ◀️ Volver\n"
            "3️⃣ 🚪 Salir"
        )
        return

    s["opps"] = get_opp_por_numero(text)

    if len(s["opps"]) == 0:

        s["opp_invalida"] = True

        send_message(
            room,
            f"❌ La OPP {text} no existe\n\n"
            "1️⃣ Intentar nuevamente\n"
            "2️⃣ ◀️ Volver\n"
            "3️⃣ 🚪 Salir"
        )

        return

    s["volver_opp"]="ingresar_opp"

    cambiar_estado(
        s,
        "opp",
        trace_id
    )

    send_message(
        room,
        menu_opps(s["opps"],"Seleccionar OPP")
    )

def manejar_opp(room, text, s, trace_id):

    if es_volver(text, s["opps"]):

        cambiar_estado(
            s,
            s["volver_opp"],
            trace_id
        )

        if s["volver_opp"]=="ingresar_opp":

            send_message(room, MSG_INGRESAR_OPP)

        else:

            send_message(
                room,
                menu_clientes(s["clientes"],"Seleccionar Cliente")
            )

        return

    if not opcion_valida(text, s["opps"]):

        send_message(room, "⚠️ Opción inválida")

        return

    opcion=int(text)

    opp_seleccionada = s["opps"][opcion-1]

    s["opp"]=opp_seleccionada["codigo"]

    s["cliente"]=opp_seleccionada["cliente"]

    cambiar_estado(
        s,
        "fecha",
        trace_id
    )

    send_message(room, MSG_FECHA)

def manejar_fecha(room, text, s, trace_id):

    ok_fecha, mensaje_fecha = validar_fecha(text)

    if not ok_fecha:

        send_message(room, mensaje_fecha)

        return

    s["fecha"]=text

    if s["tipo"] in ("soporte_normal", "implementacion_normal"):

        cambiar_estado(
            s,
            "horas",
            trace_id
        )

        send_message(room, MSG_HORAS)

    else:

        cambiar_estado(
            s,
            "inicio",
            trace_id
        )

        send_message(room, MSG_HORA_INICIO)

def manejar_horas(room, text, s, user, trace_id):

    horas = normalizar_cantidad_horas(text)

    if horas is None:

        send_message(
            room,
            """⚠️ Solo se permiten horas enteras o medias horas.

Ejemplos válidos: 2, 2.5, 2,5"""
        )

        return

    if horas < 0.5 or horas > 24:

        send_message(room, MSG_HORAS_RANGO)

        return

    if s.get("tipo") in ("soporte_normal", "implementacion_normal") and not validar_horas_normales(horas):

        send_message(room, MSG_HORAS_NORMALES_MAXIMO)

        return

    s["horas"] = horas

    s["comentario"]=""

    cambiar_estado(
        s,
        "confirmacion",
        trace_id
    )

    send_message(room, resumen(user,s))

def manejar_inicio(room, text, s, trace_id):

    if not validar_hora(text):

        send_message(room, "⚠️ Solo se permiten horas enteras o medias horas.\n\nUtilice el formato HH:00 o HH:30\n\nEjemplos válidos:\n03:00\n05:30\n22:00\n00:30\n24:00")

        return

    s["inicio"]=text

    cambiar_estado(
        s,
        "fin",
        trace_id
    )

    send_message(room, MSG_HORA_FIN)

def manejar_cruza_medianoche(room, text, s, trace_id):

    if text == "1":

        fecha1 = datetime.strptime(s["fecha"], "%d-%m-%Y")
        fecha2 = fecha1 + __import__("datetime").timedelta(days=1)

        h1 = calcular_horas(s["inicio"], "24:00")
        h2 = calcular_horas("00:00", s["fin_original"])

        s["registros_medianoche"] = [
            {
                "fecha": s["fecha"],
                "inicio": s["inicio"],
                "fin": "00:00",
                "horas": h1
            },
            {
                "fecha": fecha2.strftime("%d-%m-%Y"),
                "inicio": "00:00",
                "fin": s["fin_original"],
                "horas": h2
            }
        ]

        cambiar_estado(s, "comentario_medianoche", trace_id)
        send_message(room, MSG_COMENTARIO)
        return

    if text == "2":

        cambiar_estado(s, "fin", trace_id)

        send_message(
            room,
            "⚠️ La hora de finalización debe ser posterior a la hora de inicio.\n\nIngrese nuevamente la hora de finalización.\n\n🕒 Formato HH:00 o HH:30"
        )
        return

    send_message(room, "⚠️ Opción inválida\n\n1️⃣ Sí\n2️⃣ No\n3️⃣ 🚪 Salir")

def manejar_comentario_medianoche(room, text, s, user, trace_id):

    s["comentario"] = text

    cambiar_estado(
        s,
        "confirmacion_medianoche",
        trace_id
    )

    send_message(
        room,
        resumen_medianoche(s)
    )

def manejar_confirmacion_medianoche(room, text, s, user, trace_id):

    if text == "1":

        errores = 0

        for r in s["registros_medianoche"]:

            tmp = dict(s)
            tmp["fecha"] = r["fecha"]
            tmp["inicio"] = r["inicio"]
            tmp["fin"] = r["fin"]
            tmp["horas"] = r["horas"]

            ok, _ = guardar_horas_dataverse(user, tmp, trace_id)

            if not ok:
                errores += 1

        if errores == 0:

            cambiar_estado(s, "cargar_mas", trace_id)

            send_message(room,"✅ Horas registradas correctamente\n\n¿Desea cargar más horas?\n\n1️⃣ Sí\n2️⃣ No")
        else:
            send_message(room, f"⚠️ Finalizado con {errores} errores")

        return

    if text == "2":
        send_message(room,"❌ Cancelado")
        return

    send_message(room,"⚠️ Opción inválida")

def manejar_fin(room, text, s, trace_id):

    if not validar_hora(text):

        send_message(room, "⚠️ Solo se permiten horas enteras o medias horas.\n\nUtilice el formato HH:00 o HH:30\n\nEjemplos válidos:\n03:00\n05:30\n22:00\n00:30\n24:00")

        return

    fin_calculo = text

    if text == "24:00":
        s["fin"] = "00:00"
    else:
        s["fin"] = text

    horas = calcular_horas(
        s["inicio"],
        fin_calculo
    )

    if horas is None:

        s["fin_original"] = text

        cambiar_estado(
            s,
            "cruza_medianoche",
            trace_id
        )

        send_message(
            room,
            "🌙 La hora de finalización es menor que la hora de inicio.\n\n¿La actividad finalizó al día siguiente?\n\n1️⃣ Sí\n2️⃣ No\n3️⃣ 🚪 Salir"
        )

        return

    s["horas"] = horas

    cambiar_estado(
        s,
        "comentario",
        trace_id
    )

    send_message(room, MSG_COMENTARIO)

def manejar_comentario(room, text, s, user, trace_id):

    s["comentario"]=text

    cambiar_estado(
        s,
        "confirmacion",
        trace_id
    )

    send_message(room, resumen(user,s))

def manejar_confirmacion(room, text, s, user, trace_id):

    if text=="1":

        ok, error = guardar_horas_dataverse(
            user,
            s,
            trace_id
        )

        if ok:

            cambiar_estado(
                s,
                "cargar_mas",
                trace_id
            )

            send_message(
                room,
                """✅ Horas registradas correctamente

¿Desea cargar más horas?

1️⃣ Sí
2️⃣ No"""
            )

            return

        else:

            send_message(
                room,
                f"❌ Error Dataverse\n\n{error}"
            )

        if user in sessions:
            del sessions[user]

        return

    elif text=="2":

        send_message(room, "❌ Cancelado")

        if user in sessions:
            del sessions[user]

        return

    else:

        send_message(
            room,
            "⚠️ Opción inválida\n\n1️⃣ Confirmar\n2️⃣ Cancelar\n3️⃣ 🚪 Salir"
        )

def manejar_misma_opp(room, text, s, user, trace_id):

    if text == "1":

        for campo in ["fecha","horas","inicio","fin","comentario","tipo","registros_rapidos"]:
            s.pop(campo, None)

        s["reutilizar_opp"] = True

        cambiar_estado(
            s,
            "menu_inicio",
            trace_id
        )

        send_message(room, MSG_TIPO)

        return

    elif text == "2":

        ingeniero = s["ingeniero_data"]

        sessions[user] = {
            "ingeniero_data": ingeniero
        }

        cambiar_estado(
            sessions[user],
            "menu_inicio",
            trace_id
        )

        send_message(room, MSG_TIPO)

        return

    send_message(room, "⚠️ Opción inválida\n\n1️⃣ Sí\n2️⃣ No\n3️⃣ 🚪 Salir")


def manejar_mis_registros_continuar(room, text, s, user, trace_id):

    if text == "1":

        ingeniero = s["ingeniero_data"]

        sessions[user] = {
            "ingeniero_data": ingeniero
        }

        cambiar_estado(sessions[user], "menu_inicio", trace_id)

        send_message(room, MSG_TIPO)

        return

    if text == "2":

        nombre = s["ingeniero_data"].get(
            "hxp_ingenieronombre",
            "Ingeniero"
        )

        send_message(room, f"👋 Gracias {nombre}.\n\n🚀 Hasta la próxima.")

        if user in sessions:
            del sessions[user]

        return

    send_message(room, "⚠️ Opción inválida\n\n1️⃣ Sí\n2️⃣ No\n3️⃣ 🚪 Salir")



def mostrar_menu_admin(room, s, incluir_encabezado=True):
    if incluir_encabezado:
        nombre = s.get("ingeniero_data", {}).get(
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
            "¿Qué deseas hacer?\n\n"
            "1️⃣ Consultar horas del equipo\n"
            "2️⃣ Cargar horas\n"
            "3️⃣ 🚪 Salir"
        )


def manejar_admin_menu(room, text, s, trace_id):
    if text == "1":
        cambiar_estado(s, "admin_consultar_periodo", trace_id)
        send_message(room, MSG_ADMIN_CONSULTAR_PERIODO)
        return

    if text == "2":
        cambiar_estado(s, "menu_inicio", trace_id)
        send_message(room, MSG_TIPO)
        return

    send_message(
        room,
        "⚠️ Opción inválida\n\n"
        "1️⃣ Consultar horas del equipo\n"
        "2️⃣ Cargar horas\n"
        "3️⃣ 🚪 Salir"
    )


def manejar_admin_consultar_periodo(room, text, s, trace_id):
    if text == "4":
        cambiar_estado(s, "admin_menu", trace_id)
        mostrar_menu_admin(room, s)
        return

    hoy = datetime.now().date()

    if text == "1":
        fecha_desde = hoy - timedelta(days=30)
        fecha_hasta = hoy
        nombre_archivo = (
            f"horas_equipo_ultimos_30_dias_{hoy.strftime('%Y%m%d')}.xlsx"
        )

    elif text == "2":
        fecha_desde = hoy.replace(day=1)
        fecha_hasta = hoy
        nombre_archivo = (
            f"horas_equipo_mes_actual_{hoy.strftime('%Y%m%d')}.xlsx"
        )

    elif text == "3":
        fecha_desde = None
        fecha_hasta = None
        nombre_archivo = (
            f"horas_equipo_historico_{hoy.strftime('%Y%m%d')}.xlsx"
        )

    else:
        send_message(
            room,
            "⚠️ Opción inválida\n\n"
            "1️⃣ Últimos 30 días\n"
            "2️⃣ Mes actual\n"
            "3️⃣ Todo el histórico\n"
            "4️⃣ ◀️ Volver\n"
            "5️⃣ 🚪 Salir"
        )
        return

    enviado = generar_y_enviar_excel_equipo(
        room,
        fecha_desde,
        fecha_hasta,
        trace_id,
        nombre_archivo
    )

    if enviado:
        cambiar_estado(s, "admin_menu", trace_id)
        send_message(room, "✅ Excel generado correctamente.\n")
        mostrar_menu_admin(room, s, incluir_encabezado=False)
