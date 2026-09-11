import json
import logging
import time

from config import TENANT_ID, CLIENT_ID, CLIENT_SECRET, DATAVERSE_URL
from http_client import http
from session_manager import cache_clientes, cache_opps, cache_get, cache_set
from utils import fecha_dataverse, validar_fecha, normalizar_cantidad_horas

dv_token = None
dv_token_expire = 0

def get_dataverse_token():

    global dv_token
    global dv_token_expire

    if dv_token and time.time() < dv_token_expire:
        return dv_token

    url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"

    payload = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scope": f"{DATAVERSE_URL}/.default"
    }

    headers_token = {
        "Content-Type": "application/x-www-form-urlencoded"
    }

    response = http.post(
        url,
        data=payload,
        headers=headers_token,
        timeout=15
    )

    if response.status_code != 200:

        logging.error(response.text)

        return None

    data = response.json()

    dv_token = data["access_token"]

    dv_token_expire = time.time() + 3500

    return dv_token

def validar_ingeniero(email):
    token = get_dataverse_token()

    if not token:
        return None

    headers_dv = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }

    url = (
        f"{DATAVERSE_URL}/api/data/v9.2/hxp_ingenieros"
        f"?$filter=hxp_ingenieromail eq '{email}'"
    )

    response = http.get(
        url,
        headers=headers_dv,
        timeout=15
    )

    if response.status_code != 200:

        logging.error(response.text)

        return None

    data = response.json()

    if len(data["value"]) == 0:
        return None

    return data["value"][0]

def buscar_clientes(texto):

    texto = texto.replace("'","''")

    cache = cache_get(
        cache_clientes,
        texto
    )

    if cache is not None:

        logging.info(
            f"cache clientes hit {texto}"
        )

        return cache

    token = get_dataverse_token()

    if not token:
        return []

    headers_dv = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }

    inicio = time.time()

    url = (
        f"{DATAVERSE_URL}/api/data/v9.2/hxp_clientes"
        f"?$filter=contains(hxp_clientenombre,'{texto}')"
    )

    response = http.get(
        url,
        headers=headers_dv,
        timeout=15
    )

    duracion = round(
        time.time() - inicio,
        2
    )

    logging.info(
        f"buscar_clientes {duracion}s"
    )

    if response.status_code != 200:

        logging.error(response.text)

        return []

    data = response.json()

    clientes = []

    for c in data["value"]:

        clientes.append({
            "id": c["hxp_clienteid"],
            "nombre": c["hxp_clientenombre"],
            "texto": c["hxp_clientenombre"]
        })

    cache_set(
        cache_clientes,
        texto,
        clientes
    )

    return clientes

def get_opp_por_numero(numero):

    cache = cache_get(
        cache_opps,
        numero
    )

    if cache is not None:

        logging.info(
            f"cache opp hit {numero}"
        )

        return cache

    token = get_dataverse_token()

    if not token:
        return []

    headers_dv = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Prefer": 'odata.include-annotations="*"'
    }

    inicio = time.time()

    url = (
        f"{DATAVERSE_URL}/api/data/v9.2/hxp_opps"
        f"?$filter=hxp_opp1 eq '{numero}'"
        f"&$expand=hxp_OppCliente($select=hxp_clientenombre)"
    )

    response = http.get(
        url,
        headers=headers_dv,
        timeout=15
    )

    duracion = round(
        time.time() - inicio,
        2
    )

    logging.info(
        f"get_opp_por_numero {duracion}s"
    )

    if response.status_code != 200:

        logging.error(response.text)

        return []

    data = response.json()

    opps = []

    for opp in data["value"]:

        cliente = opp.get(
            "_hxp_oppcliente_value@OData.Community.Display.V1.FormattedValue",
            ""
        )

        comentario = opp.get(
            "hxp_oppcomentario",
            ""
        )

        codigo = opp.get(
            "hxp_opp1",
            ""
        )

        opps.append({
            "codigo": codigo,
            "cliente": cliente,
            "comentario": comentario,
            "texto": f"{codigo} - {cliente} - {comentario}"
        })

    cache_set(
        cache_opps,
        numero,
        opps
    )

    return opps

def get_opps_por_cliente(cliente_id):

    cache = cache_get(
        cache_opps,
        f"cliente_{cliente_id}"
    )

    if cache is not None:

        logging.info(
            f"cache opps cliente hit {cliente_id}"
        )

        return cache

    token = get_dataverse_token()

    if not token:
        return []

    headers_dv = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Prefer": 'odata.include-annotations="*"'
    }

    inicio = time.time()

    url = (
        f"{DATAVERSE_URL}/api/data/v9.2/hxp_opps"
        f"?$filter=_hxp_oppcliente_value eq {cliente_id}"
    )

    response = http.get(
        url,
        headers=headers_dv,
        timeout=15
    )

    duracion = round(
        time.time() - inicio,
        2
    )

    logging.info(
        f"get_opps_por_cliente {duracion}s"
    )

    if response.status_code != 200:

        logging.error(response.text)

        return []

    data = response.json()

    opps = []

    for opp in data["value"]:

        cliente = opp.get(
            "_hxp_oppcliente_value@OData.Community.Display.V1.FormattedValue",
            ""
        )

        comentario = opp.get(
            "hxp_oppcomentario",
            ""
        )

        codigo = opp.get(
            "hxp_opp1",
            ""
        )

        opps.append({
            "codigo": codigo,
            "cliente": cliente,
            "comentario": comentario,
            "texto": f"{codigo} - {cliente} - {comentario}"
        })

    cache_set(
        cache_opps,
        f"cliente_{cliente_id}",
        opps
    )

    return opps

def get_opp_por_guid(opp_guid, trace_id=None):

    if not opp_guid:
        return None

    cache_key = f"guid_{opp_guid.lower()}"

    cache = cache_get(cache_opps, cache_key)

    if cache is not None:

        logging.info(f"[{trace_id}] cache opp guid hit {opp_guid}")

        return cache

    token = get_dataverse_token()

    if not token:
        return None

    headers_dv = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Prefer": 'odata.include-annotations="*"'
    }

    inicio = time.time()

    url = (
        f"{DATAVERSE_URL}/api/data/v9.2/hxp_opps({opp_guid})"
        "?$select=hxp_opp1,hxp_oppcomentario,_hxp_oppcliente_value"
    )

    response = http.get(
        url,
        headers=headers_dv,
        timeout=15
    )

    duracion = round(time.time() - inicio, 2)

    logging.info(f"[{trace_id}] get_opp_por_guid {duracion}s")

    if response.status_code != 200:

        logging.error(f"[{trace_id}] Error OPP {opp_guid}: {response.text}")

        return None

    opp = response.json()

    datos_opp = {
        "codigo": opp.get("hxp_opp1", ""),
        "cliente": opp.get(
            "_hxp_oppcliente_value@OData.Community.Display.V1.FormattedValue",
            ""
        ),
        "proyecto": opp.get("hxp_oppcomentario", "")
    }

    cache_set(cache_opps, cache_key, datos_opp)

    return datos_opp

def get_horas_ingeniero(ingeniero_id, fecha_desde, fecha_hasta, trace_id):

    token = get_dataverse_token()

    if not token:
        return None

    headers_dv = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }

    filtro = (
        f"_hxp_horasingeniero_value eq {ingeniero_id} and "
        f"hxp_horasfecha ge {fecha_desde} and "
        f"hxp_horasfecha le {fecha_hasta}"
    )

    url = (
        f"{DATAVERSE_URL}/api/data/v9.2/hxp_horas"
        "?$select=hxp_horasfecha,hxp_horastipo,hxp_horascantidaddecimal,"
        "hxp_horainicio_,hxp_horafin_,hxp_comentario,_hxp_horasopp_value"
        f"&$filter={filtro}"
        "&$orderby=hxp_horasfecha desc"
    )

    registros = []
    inicio = time.time()

    while url:

        response = http.get(
            url,
            headers=headers_dv,
            timeout=15
        )

        if response.status_code != 200:

            logging.error(f"[{trace_id}] Error consultando horas: {response.text}")

            return None

        data = response.json()

        registros.extend(data.get("value", []))

        url = data.get("@odata.nextLink")

    logging.info(
        f"[{trace_id}] consulta hxp_horas {round(time.time() - inicio, 2)}s"
    )

    return registros

def validar_guardado_final(s):

    try:

        horas = normalizar_cantidad_horas(s["horas"])

        if horas is None or horas < 0.5 or horas > 24:
            return False

        validar = validar_fecha(s["fecha"])

        if not validar[0]:
            return False

        if not s.get("opp"):
            return False

        return True

    except:

        return False

def guardar_horas_dataverse(user,s,trace_id):

    if not validar_guardado_final(s):

        return False, "Validación final inválida"
    
    token = get_dataverse_token()

    if not token:
        return False, "No se pudo obtener token"

    headers_dv = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    url = f"{DATAVERSE_URL}/api/data/v9.2/hxp_horas"

    ingeniero_mail = s["ingeniero_data"]["hxp_ingenieromail"]

    payload = {

        "hxp_HorasIngeniero@odata.bind":
            f"/hxp_ingenieros(hxp_ingenieromail='{ingeniero_mail}')",

        "hxp_HorasOpp@odata.bind":
            f"/hxp_opps(hxp_opp1='{s['opp']}')",

        "hxp_horastipo": s["tipo"],

        "hxp_horasfecha": fecha_dataverse(s["fecha"]),

        "hxp_horascantidaddecimal": float(s["horas"]),

        "hxp_comentario": s.get("comentario","")
    }

    if "inicio" in s:

        payload["hxp_horainicio_"] = s["inicio"]

    if "fin" in s:

        payload["hxp_horafin_"] = s["fin"]

    logging.info(f"[{trace_id}] PAYLOAD")
    logging.info(json.dumps(payload,indent=2))

    response = http.post(
        url,
        headers=headers_dv,
        json=payload,
        timeout=15
    )

    logging.info(f"[{trace_id}] STATUS {response.status_code}")

    logging.info(f"[{trace_id}] RESPUESTA {response.text}")

    if response.status_code in [200,201,204]:

        return True, "OK"

    return False, response.text


def get_horas_equipo(fecha_desde=None, fecha_hasta=None, trace_id=None):
    """Obtiene registros de horas de todos los ingenieros.

    Si no se recibe período, devuelve todo el histórico.
    """
    token = get_dataverse_token()

    if not token:
        return None

    headers_dv = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Prefer": 'odata.include-annotations="*"'
    }

    filtros = []

    if fecha_desde:
        filtros.append(f"hxp_horasfecha ge {fecha_desde}")

    if fecha_hasta:
        filtros.append(f"hxp_horasfecha le {fecha_hasta}")

    url = (
        f"{DATAVERSE_URL}/api/data/v9.2/hxp_horas"
        "?$select=hxp_horasfecha,hxp_horastipo,hxp_horascantidaddecimal,"
        "hxp_horainicio_,hxp_horafin_,hxp_comentario,"
        "_hxp_horasopp_value,_hxp_horasingeniero_value"
    )

    if filtros:
        url += "&$filter=" + " and ".join(filtros)

    url += "&$orderby=hxp_horasfecha desc"

    registros = []
    inicio = time.time()

    while url:
        response = http.get(
            url,
            headers=headers_dv,
            timeout=30
        )

        if response.status_code != 200:
            logging.error(
                f"[{trace_id}] Error consultando horas del equipo: "
                f"{response.text}"
            )
            return None

        data = response.json()
        registros.extend(data.get("value", []))
        url = data.get("@odata.nextLink")

    logging.info(
        f"[{trace_id}] consulta horas equipo "
        f"{round(time.time() - inicio, 2)}s - {len(registros)} registros"
    )

    return registros
