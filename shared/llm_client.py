"""
Libreria compartida: carga de prompt, llamada a OpenRouter con economia de tokens.
Usada por todos los agentes FastAPI del ecosistema mayk.dev
"""
import os
import json
import urllib.request
import urllib.error
from pathlib import Path

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_URL     = "https://openrouter.ai/api/v1/chat/completions"

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_URL     = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"

# Mapa de modelos por agente (equilibrio calidad/coste)
MODEL_MAP = {
    "agente-auditor":   "google/gemini-flash-1.5",      # Contexto largo, barato
    "agente-estratega": "anthropic/claude-3-haiku",      # Razonamiento, bajo coste
    "agente-visual":    "openai/gpt-4o-mini",            # Creativo, economico
    "agente-dev":       "anthropic/claude-3-5-sonnet",   # Codigo complejo: mas potente
    "agente-qa-ops":    "google/gemini-flash-1.5",       # Analisis rapido
    # Modelos de pago desactivados temporalmente por falta de saldo
    # "agente-hr-evaluador": "google/gemini-2.5-pro",
    # "agente-hr-sastre":    "anthropic/claude-3-5-haiku",
    # "agente-hr-rrhh":      "google/gemini-2.5-pro",

    "agente-hr-rrhh":      "gemini-2.0-flash",
    "agente-hr-evaluador": "gemini-2.0-flash",
    "agente-hr-sastre":    "gemini-2.0-flash",
    "agente-hr-diseno":    "google/gemma-3-27b-it:free",
    "agente-scanner":      "meta-llama/llama-3.2-3b-instruct:free",
}

# Lista de fallback ante 429 (se prueba en orden)
FALLBACK_FREE_MODELS = [
    "meta-llama/llama-3.3-70b-instruct:free",
    "google/gemma-3-27b-it:free",
    "nousresearch/hermes-3-llama-3.1-405b:free",
    "minimax/minimax-m2.5:free",
    "nvidia/nemotron-3-super-120b-a12b:free",
    "meta-llama/llama-3.2-3b-instruct:free",
]

# Timeout por modelo (segundos) — hermes-405b es el mas grande, puede tardar hasta 200s
TIMEOUT_MAP = {
    "agente-hr-evaluador": 240,
    "agente-hr-rrhh":      240,
    "agente-dev":          120,
    "agente-hr-sastre":    200,
    "agente-hr-diseno":    180,
    "agente-scanner":      120,
}
DEFAULT_TIMEOUT = 90


def load_prompt(agent_id: str) -> str:
    """Carga el prompt.md del agente desde su directorio (Local o en Docker)."""
    # 1. Rutas Docker (/app/prompt.md)
    base_docker = Path(__file__).parent.parent / "prompt.md"
    if base_docker.exists():
        return base_docker.read_text(encoding="utf-8")
        
    # 2. Rutas Desarrollo Local (mayk-agents/agente_id/prompt.md)
    base_local = Path(__file__).parent.parent / agent_id / "prompt.md"
    if base_local.exists():
        return base_local.read_text(encoding="utf-8")
        
    print(f"[ERROR CRITICO] No se encontro prompt.md para {agent_id}. El agente operará ciego.")
    return f"Eres el {agent_id} del ecosistema mayk.dev. Ejecuta tu rol con precision pero responde SIEMPRE en JSON."


def call_llm(agent_id: str, user_message: str, max_tokens: int = 2048) -> str:
    """
    Llama a OpenRouter con el modelo correcto para el agente.
    - Rotacion automatica de modelos gratuitos ante 429 (rate-limit).
    - Retry con backoff exponencial por modelo.
    - Timeout adaptado por modelo.
    """
    if not OPENROUTER_API_KEY and not GEMINI_API_KEY:
        return "ERROR: Ni OPENROUTER_API_KEY ni GEMINI_API_KEY configuradas en el entorno."

    system_prompt = load_prompt(agent_id)
    primary_model = MODEL_MAP.get(agent_id, "google/gemini-flash-1.5")
    timeout = TIMEOUT_MAP.get(agent_id, DEFAULT_TIMEOUT)

    # Construir lista de modelos a intentar (primario + fallbacks sin duplicados)
    models_to_try = [primary_model] + [m for m in FALLBACK_FREE_MODELS if m != primary_model]

    import time
    
    # [ESTRATEGIA SMART FALLBACK RAPIDO PARA API GRATUITA]
    for model in models_to_try:
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_message},
            ],
            "max_tokens":  max_tokens,
            "temperature": 0.3,
        }
        if "gemini" in model.lower() and GEMINI_API_KEY:
            # Enrutar a Native Google API
            used_url = GEMINI_URL
            used_headers = {
                "Authorization": f"Bearer {GEMINI_API_KEY}",
                "Content-Type":  "application/json"
            }
        else:
            # Enrutar a OpenRouter
            if not OPENROUTER_API_KEY:
                print(f"[llm_client] Saltando {model} por falta de OPENROUTER_API_KEY")
                continue
            used_url = OPENROUTER_URL
            used_headers = {
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type":  "application/json",
                "HTTP-Referer":  "https://github.com/MaykNLD/mayk-orchestrators",
                "X-Title":       "mayk.dev Orchestrator",
            }

        req = urllib.request.Request(
            used_url,
            data=json.dumps(payload).encode(),
            headers=used_headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode())
                content = data["choices"][0]["message"]["content"]
                print(f"[llm_client] Exito con modelo: {model}")
                return content
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            if e.code == 429 or e.code == 404 or e.code == 528:
                print(f"[llm_client] {e.code} Saturado u offline en {model}. Saltando al siguiente...")
                time.sleep(1) # Pequeña pausa para no enojar al rate-limit global de la cuenta
                continue
            print(f"[llm_client] Error critico {e.code} en {model}: {body[:200]}")
            continue
        except Exception as e:
            print(f"[llm_client] Excepcion en {model}: {str(e)}")
            continue

    # ----------------------------------------------------
    # ESTRATEGIA ORIGINAL (RETOQUES EXPONENCIALES PARA IAS DE PAGO)
    # Dejo esto comentado para activarlo cuando pasemos a tiers premium
    # ----------------------------------------------------
    '''
    for model in models_to_try:
        wait_seconds = [10, 20, 40]
        for attempt in range(3):
            # ...payload setup...
            try:
                # ...request limit...
            except urllib.error.HTTPError as e:
                if e.code == 429:
                    wait = wait_seconds[attempt] if attempt < len(wait_seconds) else 40
                    time.sleep(wait)
                    continue
                break
    '''

    return "ERROR LLM: todos los modelos gratuitos estan saturados o no disponibles. Intenta en unos minutos."