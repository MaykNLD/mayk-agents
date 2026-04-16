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
    # Career agents (Modelos de pago desactivados temporalmente por falta de saldo)
    # "agente-hr-evaluador": "google/gemini-2.5-pro",      # Evaluacion profunda
    # "agente-hr-sastre":    "anthropic/claude-3-5-haiku", # Adaptacion rapida
    # "agente-hr-evaluador": "meta-llama/llama-3.3-70b-instruct:free",  # Rate-limited por Venice
    # "agente-hr-sastre":    "meta-llama/llama-3.3-70b-instruct:free",
    "agente-hr-evaluador": "nousresearch/hermes-3-llama-3.1-405b:free",
    "agente-hr-sastre":    "nousresearch/hermes-3-llama-3.1-405b:free",
}

# Timeout por modelo (segundos) — hermes-405b es el mas grande, puede tardar hasta 200s
TIMEOUT_MAP = {
    "agente-hr-evaluador": 240,
    "agente-dev":          120,
    "agente-hr-sastre":    200,
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
    - Retry automático con backoff exponencial ante 429 (rate-limit).
    - Timeout adaptado por modelo.
    - Maximos 3 intentos antes de fallar con detalle claro.
    """
    if not OPENROUTER_API_KEY:
        return "ERROR: OPENROUTER_API_KEY no configurada en el entorno."

    system_prompt = load_prompt(agent_id)
    model   = MODEL_MAP.get(agent_id, "google/gemini-flash-1.5")
    timeout = TIMEOUT_MAP.get(agent_id, DEFAULT_TIMEOUT)

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

    max_retries = 3
    wait_seconds = [15, 30, 60]  # backoff: 15s -> 30s -> 60s ante 429

    for attempt in range(max_retries):
        req = urllib.request.Request(
            OPENROUTER_URL,
            data=json.dumps(payload).encode(),
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode())
                return data["choices"][0]["message"]["content"]

        except urllib.error.HTTPError as e:
            body = e.read().decode()
            if e.code == 429:
                wait = wait_seconds[attempt] if attempt < len(wait_seconds) else 60
                import time
                print(f"[llm_client] 429 rate-limit en intento {attempt+1}. Reintentando en {wait}s...")
                time.sleep(wait)
                continue  # reintentar
            return f"ERROR LLM [{e.code}]: {body}"

        except Exception as e:
            return f"ERROR LLM: {str(e)}"

    return f"ERROR LLM: se agotaron {max_retries} reintentos por rate-limit (429). Espera unos minutos e intenta de nuevo."