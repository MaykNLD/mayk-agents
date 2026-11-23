"""
Libreria compartida: carga de prompt, llamada a OpenRouter (Nivel Premium).
Usada por todos los agentes FastAPI del ecosistema mayk.dev
"""
import os
import json
import urllib.request
import urllib.error
import time
from pathlib import Path

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_URL     = "https://openrouter.ai/api/v1/chat/completions"

# Modelos asignados por rol (OpenRouter)
# gemini-2.0-flash-001:    $0.10/M — análisis largo, contexto masivo
# claude-haiku-4.5:          $1.00/M in / $5.00/M out — instrucciones precisas, JSON fiable, rápido
# mistral-small-3.1-24b:   $0.10/M — fallback general
MODEL_MAP = {
    # ── Agentes Career-Ops ────────────────────────────────────────────────
    "agente-hr-evaluador": "anthropic/claude-haiku-4.5",            # FIX: Gemini estaba fallando con el JSON (score 0)
    "agente-hr-sastre":    "anthropic/claude-haiku-4.5",            # reescritura ATS precisa y rápida
    "agente-hr-rrhh":      "anthropic/claude-haiku-4.5",            # mejora y análisis de CV
    "agente-hr-diseno":    "google/gemini-2.0-flash-001",           # generación HTML premium
    "agente-scanner":      "google/gemini-2.0-flash-001",           # clasificación ofertas
    # ── Agentes generales ───────────────────────────────────────────────
    "agente-auditor":      "mistralai/mistral-small-3.1-24b-instruct",
    "agente-estratega":    "mistralai/mistral-small-3.1-24b-instruct",
    "agente-visual":       "mistralai/mistral-small-3.1-24b-instruct",
    "agente-dev":          "mistralai/mistral-small-3.1-24b-instruct",
    "agente-qa-ops":       "mistralai/mistral-small-3.1-24b-instruct",
}

DEFAULT_TIMEOUT = 120

def load_prompt(agent_id: str) -> str:
    """Carga el prompt.md del agente desde su directorio (Local o en Docker)."""
    base_docker = Path(__file__).parent.parent / "prompt.md"
    if base_docker.exists():
        return base_docker.read_text(encoding="utf-8")
        
    base_local = Path(__file__).parent.parent / agent_id / "prompt.md"
    if base_local.exists():
        return base_local.read_text(encoding="utf-8")
        
    print(f"[ERROR CRITICO] No se encontro prompt.md para {agent_id}. El agente operará ciego.")
    return f"Eres el {agent_id} del ecosistema mayk.dev. Ejecuta tu rol con precision pero responde SIEMPRE en JSON."

def call_llm(agent_id: str, user_message: str, max_tokens: int = 4096) -> str:
    """
    Llama a OpenRouter Premium.
    Garantiza estabilidad absoluta para parseo JSON sin fallbreaks infinitos.
    """
    if not OPENROUTER_API_KEY:
        return "ERROR: OPENROUTER_API_KEY no configurada en el entorno."

    system_prompt = load_prompt(agent_id)
    model = MODEL_MAP.get(agent_id, "anthropic/claude-haiku-4.5")
    timeout = DEFAULT_TIMEOUT

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_message},
        ],
        "max_tokens":  max_tokens,
        "temperature": 0.3, # Baja temperatura para json predecible
    }
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type":  "application/json",
        "HTTP-Referer":  "https://github.com/MaykNLD/mayk-orchestrators",
        "X-Title":       "mayk.dev Orchestrator",
    }

    wait_seconds = [1, 3]
    for attempt in range(3):
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
                print(f"[llm_client] Exito con modelo Premium: {model}")
                return content
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            print(f"[llm_client] Error HTTP {e.code} en attempt {attempt + 1}: {body[:200]}")
            if e.code == 429:
                 return "ERROR: Saldo de OpenRouter agotado. Por favor, recargue su cuenta (429 Rate Limit)."
            if e.code == 402:
                 return "ERROR: Pago requerido (402). Por favor, recargue su saldo en OpenRouter."
            if attempt < len(wait_seconds):
                time.sleep(wait_seconds[attempt])
                continue
            return f"ERROR: Fallo permanente llamando a {model} - {body}"
        except Exception as e:
            print(f"[llm_client] Excepcion de red en attempt {attempt + 1}: {str(e)}")
            if attempt < len(wait_seconds):
                time.sleep(wait_seconds[attempt])
                continue
            return f"ERROR: Fallo de red - {str(e)}"
    return ""
