# mayk-agents

Repositorio privado que contiene los **agentes globales** del ecosistema mayk.dev. Estos agentes son independientes del tipo de proyecto (Web, App, SaaS) y están diseñados para ser invocados por los diferentes orquestadores.

## Arquitectura del repositorio

```
mayk-agents/
├── agents-registry.yaml         ← Registro maestro de los agentes
├── agente-auditor/              ← Análisis de código legado web y móvil
├── agente-estratega/            ← Toma de decisiones de negocio, stacks de web y móvil
├── agente-visual/               ← UI/UX, mobile-first, patrones de diseño web y móvil
├── agente-dev/                  ← React, Node.js, React Native, Flutter, Swift, Kotlin
└── agente-qa-ops/               ← QA completo: web (Lighthouse) y móvil (Crashes, tiendas)
```

Cada carpeta de agente contiene:
- `agent.yaml`: Contrato del agente, donde se define la versión, entradas, salidas y la **IA recomendada** (ej: Gemini 1.5 Pro, Claude Opus, GPT-4o, etc.).
- `prompt.md`: El prompt estructurado para la Inteligencia Artificial.

---

## Uso

Este repositorio **no** está destinado a abrirse con el cliente. Su propósito principal es servir como "sistema de archivos" para los repositorios Orquestadores:

1. Los orquestadores leen `agents-registry.yaml`.
2. Durante una sesión (p.ej. con Antigravity, Claude Code o Cursor), el orquestador tiene acceso completo al contexto y comportamiento de estos agentes.

---

## 🤖 IAs Recomendadas por Agente

Aunque el sistema es independiente del LLM, el diseño de estos prompts ha sido validado recomendando específicamente:

| Agente | IA Recomendada | Justificación |
|---|---|---|
| **Auditor** | `Gemini 1.5 Pro` | Contexto masivo + Búsqueda Web para bases de código largas y SEO/Lighthouse |
| **Estratega** | `Claude Opus/Sonnet` | Razonamiento complejo de arquitecturas organizacionales |
| **Visual** | `GPT-4o` | Multimodalidad nativa (analizar mockups o logos del cliente) |
| **Dev** | `Claude Sonnet` | Máxima adherencia arquitectónica y menor tasa de alucinaciones en código |
| **QA-Ops** | `Gemini 1.5 Flash` | Velocidad superlativa para checklists reiterativos |

---

## Modificación de Agentes

Si deseas ampliar las capacidades de los agentes (ej: nuevo framework, nuevas métricas), edita el `prompt.md` del agente correspondiente y actualiza su versión en `agent.yaml`. Al hacerlo, **todos los orquestadores** que lo utilicen obtendrán las nuevas capacidades automáticamente.
