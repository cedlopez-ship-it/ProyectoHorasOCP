from datetime import datetime

from messages import MSG_FECHA_FUTURA, MSG_FECHA_ANTIGUA, MSG_FECHA_FORMATO

def saludo_final():

    hora = datetime.now().hour

    if 6 <= hora < 12:
        return "☀️ Que tenga un buen día."
    elif 12 <= hora < 20:
        return "🌤️ Que tenga una buena tarde."
    else:
        return "🌙 Que tenga una buena noche."

def fecha_dataverse(fecha):

    d = datetime.strptime(
        fecha,
        "%d-%m-%Y"
    )

    return d.strftime("%Y-%m-%d")

def validar_fecha(text):

    try:

        fecha = datetime.strptime(
            text,
            "%d-%m-%Y"
        )

        hoy = datetime.now()

        if fecha.date() > hoy.date():

            return (
                False,
                MSG_FECHA_FUTURA
            )

        if (hoy - fecha).days > 30:

            return (
                False,
                MSG_FECHA_ANTIGUA
            )

        return True, ""

    except:

        return (
            False,
            MSG_FECHA_FORMATO
        )

def validar_hora(text):

    if text == "24:00":
        return True

    try:

        partes = text.split(":")

        if len(partes) != 2:
            return False

        if partes[1] not in ["00", "30"]:
            return False

        datetime.strptime(text,"%H:%M")

        return True

    except:
        return False

def normalizar_cantidad_horas(text):

    try:
        valor = float(str(text).strip().replace(",", "."))
    except (TypeError, ValueError):
        return None

    if valor * 2 != int(valor * 2):
        return None

    return valor

def formatear_horas(horas):

    valor = float(horas)

    if valor.is_integer():
        return str(int(valor))

    return str(valor).replace(".", ",")

def validar_horas_normales(horas):

    return 0.5 <= horas <= 9 and horas * 2 == int(horas * 2)

def calcular_horas(inicio,fin):

    fmt="%H:%M"

    i=datetime.strptime(inicio,fmt)

    if fin in ["00:00","24:00"]:

        horas = 24 - (i.hour + i.minute / 60)

        if horas < 0.5 or horas > 24:
            return None

        return round(horas,2)

    f=datetime.strptime(fin,fmt)

    if f <= i:
        return None

    horas = (f-i).seconds / 3600

    if horas < 0.5 or horas > 24:
        return None

    return round(horas,2)

def menu_clientes(lista,titulo):

    text="━━━━━━━━━━━━━━━━━━\n"
    text+=f"🔹 {titulo.upper()}\n"
    text+="━━━━━━━━━━━━━━━━━━\n\n"
    clientes_mostrados = lista[:8]

    for i,item in enumerate(clientes_mostrados,1):
        text+=f"{i}️⃣ {item['texto']}\n"

    text+=f"\n{len(clientes_mostrados)+1}️⃣ ◀️ Volver"
    text+=f"\n{len(clientes_mostrados)+2}️⃣ 🚪 Salir"

    return text

def menu_opps(lista,titulo):

    text="━━━━━━━━━━━━━━━━━━\n"
    text+=f"🔹 {titulo.upper()}\n"
    text+="━━━━━━━━━━━━━━━━━━\n\n"
    for i,item in enumerate(lista,1):
        text+=f"**{i}.** {item['texto']}\n"
    text+=f"\n**{len(lista)+1}.** ◀️ Volver"
    text+=f"\n**{len(lista)+2}.** 🚪 Salir"
    return text

def es_volver(text, lista):

    try:

        opcion = int(text)

        return opcion == len(lista) + 1

    except:

        return False

def opcion_valida(text, lista):

    try:

        opcion = int(text)

        return 1 <= opcion <= len(lista)

    except:

        return False

def resumen(user,s):

    txt="""
━━━━━━━━━━━━━━━━━━
📋
RESUMEN
━━━━━━━━━━━━━━━━━━
"""

    txt+=f"""
👤 {user}
🏢 {s.get('cliente','')}
📂 {s['opp']}
📅 {s['fecha']}
"""

    if "inicio" in s:

        txt+=f"""

🕒 Inicio: {s['inicio']}
🕒 Fin: {s['fin']}
"""

    txt+=f"""

⏱️ {formatear_horas(s['horas'])} h
"""

    if s.get("comentario","").strip():

        txt+=f"""

💬 {s['comentario']}
"""

    txt+="""

1️⃣ Confirmar
2️⃣ Cancelar
3️⃣ 🚪 Salir
"""

    return txt

def resumen_medianoche(s):

    txt = "📋 RESUMEN\n\n"

    for i,r in enumerate(s["registros_medianoche"],1):

        txt += (
            f"Registro {i}\n"
            f"📅 {r['fecha']}\n"
            f"🕒 {r['inicio']} → {r['fin']}\n"
            f"⏱️ {formatear_horas(r['horas'])} h\n\n"
        )

    total = sum(r["horas"] for r in s["registros_medianoche"])

    if s.get("comentario","").strip():
        txt += f"💬 {s['comentario']}\n\n"

    txt += f"⏱️ Total: {formatear_horas(total)} h\n\n1️⃣ Confirmar\n2️⃣ Cancelar\n3️⃣ 🚪 Salir"

    return txt
