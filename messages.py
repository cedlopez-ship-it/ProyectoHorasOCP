# Mensajes de ProyectoHoras v47. Contenido preservado desde app.py estable.

MSG_TIPO = """
━━━━━━━━━━━━━━━━━━
⏱️ REGISTRO DE HORAS
━━━━━━━━━━━━━━━━━━

1️⃣ Soporte - Horas normales
2️⃣ Soporte - Horas extras
3️⃣ Implementación - Horas normales
4️⃣ Implementación - Horas extras
5️⃣ Consultoría
6️⃣ Mis registros — Últimos 30 días
7️⃣ 🚪 Salir
"""

MSG_CARGA_RAPIDA = """
¿Desea realizar una carga rápida?

1️⃣ Sí
2️⃣ No
3️⃣ ◀️ Volver
4️⃣ 🚪 Salir
"""

MSG_BUSCAR_CLIENTE = """
━━━━━━━━━━━━━━━━━━
🔎 BUSCAR CLIENTE
━━━━━━━━━━━━━━━━━━

Ingrese al menos 3 letras
del nombre del cliente
"""

MSG_INGRESAR_OPP = """
━━━━━━━━━━━━━━━━━━
🔢 INGRESAR OPP
━━━━━━━━━━━━━━━━━━

Número de 4 dígitos
"""

MSG_FECHA = """
━━━━━━━━━━━━━━━━━━
📅 INGRESAR FECHA (DD-MM-AAAA)
━━━━━━━━━━━━━━━━━━
"""

MSG_HORAS = """
━━━━━━━━━━━━━━━━━━
⏱️ CANTIDAD DE HORAS (ENTERAS O MEDIAS)
━━━━━━━━━━━━━━━━━━
"""

MSG_HORA_INICIO = """
━━━━━━━━━━━━━━━━━━
🕒 HORA INICIO (HH:00 o HH:30)
━━━━━━━━━━━━━━━━━━
"""

MSG_HORA_FIN = """
━━━━━━━━━━━━━━━━━━
🕒 HORA FIN (HH:00 o HH:30)
━━━━━━━━━━━━━━━━━━
"""

MSG_CLIENTE_NO_ENCONTRADO = (
    "❌ No se encontraron coincidencias.\n\n"
    "Ingrese un nuevo texto de búsqueda."
)

MSG_CLIENTE_DEMASIADOS = (
    "🔎 Se encontraron {cantidad} coincidencias.\n\n"
    "Ingrese más caracteres para refinar la búsqueda."
)

MSG_CLIENTE_SIN_OPPS = "❌ El cliente no tiene OPPs"

MSG_OPP_INVALIDA = "❌ La OPP no existe"

MSG_FECHA_FUTURA = "⚠️ No puede ingresar fechas futuras"

MSG_FECHA_ANTIGUA = "⚠️ Solo puede cargar hasta 30 días atrás"

MSG_FECHA_FORMATO = "⚠️ Formato inválido (DD-MM-AAAA)"

MSG_HORAS_RANGO = "⚠️ Las horas deben estar entre 0,5 y 24"

MSG_HORAS_NORMALES_MAXIMO = """⚠️ Las horas normales permiten registrar un máximo de **9 horas** por día.

Si necesitás registrar una cantidad mayor, utilizá la opción **Horas Extra**.

Por favor, ingresá nuevamente la cantidad de horas normales (0,5 a 9, en intervalos de media hora)."""

MSG_RECORDATORIO_SEMANAL = """📌 **Recordatorio semanal**

Te recordamos que hoy es viernes y aún estás a tiempo de registrar las horas trabajadas de esta semana.

Por favor ingresá al bot y completá la carga antes de finalizar la jornada.

¡Muchas gracias!"""

MSG_COMENTARIO = """
━━━━━━━━━━━━━━━━━━
💬 COMENTARIO
━━━━━━━━━━━━━━━━━━
"""


MSG_ADMIN_MENU = """
👋 Hola, {nombre}

🔐 Acceso de administrador

¿Qué deseas hacer?

1️⃣ Consultar horas del equipo
2️⃣ Cargar horas
3️⃣ 🚪 Salir
"""

MSG_ADMIN_CONSULTAR_PERIODO = """
📊 CONSULTAR HORAS DEL EQUIPO

Seleccione el período:

1️⃣ Últimos 30 días
2️⃣ Mes actual
3️⃣ Todo el histórico
4️⃣ ◀️ Volver
5️⃣ 🚪 Salir
"""
