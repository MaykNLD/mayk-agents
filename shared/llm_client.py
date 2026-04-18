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

    "agente-hr-rrhh":      "nousresearch/hermes-3-llama-3.1-405b:free",
    "agente-hr-evaluador": "nvidia/nemotron-3-super-120b-a12b:free",
    "agente-hr-sastre":    "nousresearch/hermes-3-llama-3.1-405b:free",
    "agente-hr-diseno":    "google/gemma-4-31b-it:free",
    "agente-scanner":      "meta-llama/llama-3.2-3b-instruct:free",
}

# Lista de fallback ante 429 (se prueba en orden)
FALLBACK_FREE_MODELS = [
    "nousresearch/hermes-3-llama-3.1-405b:free",
    "nvidia/nemotron-3-super-120b-a12b:free",
    "openai/gpt-oss-120b:free",
    "meta-llama/llama-3.3-70b-instruct:free",
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
    """Carga el prompt.md del agente desde su directorio."""
    base = Path(__file__).parent.parent / agent_id / "prompt.md"
    if base.exists():
        return base.read_text(encoding="utf-8")
    return f"Eres el {agent_id} del ecosistema mayk.dev. Ejecuta tu rol con precision."


def call_llm(agent_id: str, user_message: str, max_tokens: int = 2048) -> str:
    """
    Llama a OpenRouter con el modelo correcto para el agente.
    - Rotacion automatica de modelos gratuitos ante 429 (rate-limit).
    - Retry con backoff exponencial por modelo.
    - Timeout adaptado por modelo.
    """
    if not OPENROUTER_API_KEY:
        return "ERROR: OPENROUTER_API_KEY no configurada en el entorno."

    system_prompt = load_prompt(agent_id)
    primary_model = MODEL_MAP.get(agent_id, "google/gemini-flash-1.5")
    timeout = TIMEOUT_MAP.get(agent_id, DEFAULT_TIMEOUT)

    # Construir lista de modelos a intentar (primario + fallbacks sin duplicados)
    models_to_try = [primary_model] + [m for m in FALLBACK_FREE_MODELS if m != primary_model]

    import time
    for model in models_to_try:
        wait_seconds = [10, 20, 40]
        for attempt in range(3):
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user",   "content": user_message},
                ],
                "max_tokens":  max_tokens,
                "temperature": 0.3,
            }
            headers = {
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type":  "application/json",
                "HTTP-Referer":  "https://github.com/MaykNLD/mayk-orchestrators",
                "X-Title":       "mayk.dev Orchestrator",
            }
            req = urllib.request.Request(
                OPENROUTER_URL,
                data=json.dumps(payload).encode(),
                headers=headers,
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
                if e.code == 429:
                    wait = wait_seconds[attempt] if attempt < len(wait_seconds) else 40
                    print(f"[llm_client] 429 rate-limit en {model} (intento {attempt+1}). Reintentando en {wait}s...")
                    time.sleep(wait)
                    continue
                print(f"[llm_client] Error {e.code} en {model}: {body[:200]}")
                break  # Error no recuperable con este modelo, pasar al siguiente
            except Exception as e:
                print(f"[llm_client] Excepcion en {model}: {str(e)}")
                break

    return "ERROR LLM: todos los modelos gratuitos estan saturados o no disponibles. Intenta en unos minutos."