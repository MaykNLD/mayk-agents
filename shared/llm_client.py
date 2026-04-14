"""
Librería compartida: carga de prompt, llamada a OpenRouter con economía de tokens.
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
    "agente-visual":    "openai/gpt-4o-mini",            # Creativo, económico
    "agente-dev":       "anthropic/claude-3-5-sonnet",   # Código complejo: más potente
    "agente-qa-ops":    "google/gemini-flash-1.5",      # Análisis rápido
}


def load_prompt(agent_id: str) -> str:
    """Carga el prompt.md del agente desde su directorio."""
    base = Path(__file__).parent.parent / agent_id / "prompt.md"
    if base.exists():
        return base.read_text(encoding="utf-8")
    return f"Eres el {agent_id} del ecosistema mayk.dev. Ejecuta tu rol con precisión."


def call_llm(agent_id: str, user_message: str, max_tokens: int = 2048) -> str:
    """
    Llama a OpenRouter con el modelo correcto para el agente.
    Comprime el contexto al mínimo necesario para economizar tokens.
    """
    if not OPENROUTER_API_KEY:
        return "ERROR: OPENROUTER_API_KEY no configurada en el entorno."

    system_prompt = load_prompt(agent_id)
    model = MODEL_MAP.get(agent_id, "google/gemini-flash-1.5")

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_message},
        ],
        "max_tokens": max_tokens,
        "temperature": 0.3,  # Más determinista = menos tokens perdidos
    }

    headers = {
        "Authorization":  f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type":   "application/json",
        "HTTP-Referer":   "https://github.com/MaykNLD/mayk-orchestrators",
        "X-Title":        "mayk.dev Orchestrator",
    }

    req = urllib.request.Request(
        OPENROUTER_URL,
        data=json.dumps(payload).encode(),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode())
            return data["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as e:
        return f"ERROR LLM [{e.code}]: {e.read().decode()}"
    except Exception as e:
        return f"ERROR LLM: {str(e)}"
