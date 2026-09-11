import logging
import time

from config import SESSION_TIMEOUT, CACHE_TTL

sessions = {}
processed_messages = {}
cache_clientes = {}
cache_opps = {}

def cambiar_estado(s, estado, trace_id=None):

    s["estado"] = estado

    s["last_activity"] = time.time()

    if trace_id:

        logging.info(
            f"[{trace_id}] nuevo estado -> {estado}"
        )

def sesion_expirada(s):

    return time.time() - s.get(
        "last_activity",
        0
    ) > SESSION_TIMEOUT

def cleanup_sessions():

    borrar = []

    for u, s in sessions.items():

        if sesion_expirada(s):

            borrar.append(u)

    for u in borrar:

        del sessions[u]

def cleanup_processed_messages():

    now = time.time()

    copia = processed_messages.copy()

    for mid, ts in copia.items():

        if now - ts > 3600:

            del processed_messages[mid]

def cache_get(cache, key):

    if key not in cache:
        return None

    item = cache[key]

    if time.time() - item["timestamp"] > CACHE_TTL:

        del cache[key]

        return None

    return item["data"]

def cache_set(cache, key, value):

    cache[key] = {
        "data": value,
        "timestamp": time.time()
    }

def cleanup_cache(cache):

    borrar = []

    for key, value in cache.items():

        if time.time() - value["timestamp"] > CACHE_TTL:

            borrar.append(key)

    for key in borrar:

        del cache[key]
