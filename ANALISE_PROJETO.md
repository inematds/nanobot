# Análise do Projeto: nanobot

**nanobot** é um assistente pessoal de IA ultra-leve, inspirado no Clawdbot, desenvolvido pela HKUDS. O projeto entrega funcionalidades completas de agente em apenas **~6.621 linhas** de código Python.

---

## Dados Gerais

| Item | Valor |
|------|-------|
| **Versão** | 0.1.3.post5 |
| **Licença** | MIT |
| **Python** | >= 3.11 |
| **Arquivos .py** | 48 |
| **Linhas de código** | ~6.621 |
| **Entry point** | `nanobot.cli.commands:app` (Typer) |

---

## Arquitetura Modular

| Módulo | Linhas | Responsabilidade |
|--------|--------|------------------|
| `agent/` | 2.162 | Loop principal do agente, contexto, memória, skills e tools |
| `channels/` | 1.670 | Integrações: Telegram, WhatsApp, Discord, Feishu, DingTalk |
| `cli/` | 764 | Interface de linha de comando (Typer + readline) |
| `providers/` | 662 | Abstração de LLMs (12+ provedores via LiteLLM) |
| `cron/` | 411 | Agendamento de tarefas (cron, intervalos, timestamps) |
| `config/` | 288 | Configuração com Pydantic (`~/.nanobot/config.json`) |
| `session/` | 207 | Histórico de conversas (JSONL por canal/chat) |
| `heartbeat/` | 135 | Tarefas periódicas a cada 30 min |
| `bus/` | 124 | Message bus assíncrono (desacoplamento canal ↔ agente) |
| `utils/` | 96 | Helpers genéricos |

---

## Principais Features

- **Multi-canal**: Telegram, WhatsApp (via bridge Node.js/Baileys), Discord, Feishu, DingTalk
- **Multi-provedor**: OpenRouter, Anthropic, OpenAI, DeepSeek, Groq, Gemini, DashScope (Qwen), Moonshot, Zhipu, AiHubMix, vLLM local
- **Tools built-in**: filesystem (read/write/edit/list), shell, web search (Brave API), web fetch, mensagens, spawn de subagentes, cron
- **Sistema de Skills**: Skills em Markdown com YAML frontmatter (github, weather, summarize, tmux, cron, skill-creator)
- **Memória persistente**: `workspace/memory/MEMORY.md`
- **Personalidade configurável**: `SOUL.md`, `AGENTS.md`, `USER.md` no workspace
- **Async-first**: Construído sobre asyncio para operações concorrentes
- **Docker**: Dockerfile incluído para deploy containerizado

---

## Componentes Externos

- **`bridge/`**: Aplicação TypeScript/Node.js (Baileys + WebSocket) para integração com WhatsApp
- **`tests/`**: Apenas 1 arquivo de testes (`test_tool_validation.py`) — cobertura de testes é muito baixa
- **`workspace/`**: Templates de configuração do agente (AGENTS.md, SOUL.md, USER.md, TOOLS.md, HEARTBEAT.md)

---

## Pontos Fortes

1. **Código extremamente compacto** — fácil de entender e modificar
2. **Arquitetura limpa** — separação clara de responsabilidades
3. **Extensível** — adicionar novo provider = 2 passos; skills = um arquivo Markdown
4. **Provider Registry** — padrão declarativo elegante em `registry.py`

## Pontos de Atenção

1. **Cobertura de testes mínima** — apenas 88 linhas de testes para 6.600+ de código
2. **Sem type hints completos** em vários módulos
3. **Segurança de shell** — `ExecTool` executa comandos do shell (mitigado por `restrictToWorkspace`)
4. **Dependência de runtime externo** — WhatsApp requer Node.js >= 20 rodando em paralelo
5. **Sem CI/CD** configurado no repositório local

---

*Relatório gerado em 2026-02-08*
