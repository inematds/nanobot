# Análise de Segurança do nanobot

Análise detalhada das vulnerabilidades e riscos de segurança do projeto.

---

## RISCO ALTO (Prioridade 1)

### 1. Injeção de Comandos (`agent/tools/shell.py`)
- Usa `asyncio.create_subprocess_shell()` — executa comandos via shell
- Filtro por blacklist (regex) é facilmente burlável com `$()`, backticks, pipes `|`, encadeamento `;`/`&&`/`||`
- Verificação de path traversal (`..`) é superficial — ignorada com symlinks ou variáveis de ambiente

**Recomendações:**
- Usar `asyncio.create_subprocess_exec()` com array de argumentos
- Bloquear operadores de encadeamento (`;`, `&&`, `||`, `|`, `$(`, `` ` ``)
- Implementar whitelist de comandos permitidos em vez de blacklist
- Adicionar rate limiting por sessão

### 2. Autenticação Aberta por Padrão (`channels/base.py`)
- `allowFrom: []` = **permite qualquer pessoa** interagir com o bot
- Matching de usernames fraco — aceita matches parciais via separador `|`
- Sem rate limiting — atacante pode esgotar créditos da API

**Recomendações:**
- Mudar default para DENY ALL (exigir allowlist explícita)
- Implementar rate limiting por usuário
- Adicionar expiração de sessão e rotação de tokens
- Adicionar CAPTCHA ou desafio para novos usuários

### 3. Credenciais em Texto Plano (`config/`)
- API keys, tokens de bot, secrets — tudo em JSON sem criptografia
- Keys colocadas em `os.environ` (visíveis em `/proc/<pid>/environ`)
- Erros do LiteLLM podem vazar API keys nas mensagens de erro retornadas ao usuário

**Recomendações:**
- Usar OS keychain (biblioteca `keyring`)
- Criptografar config com senha do usuário
- Implementar rotação de keys
- Sanitizar API keys de mensagens de erro
- Adicionar verificação de permissões de arquivo (forçar 0600)

### 4. Prompt Injection (`agent/loop.py`)
- Input do usuário inserido diretamente no contexto do LLM sem sanitização
- Resultados de tools adicionados ao contexto sem filtragem
- Mensagens de sistema de subagents são confiadas sem verificação
- Atacante pode manipular o agente para executar comandos arbitrários

**Recomendações:**
- Implementar detecção de prompt injection
- Sanitizar resultados de tools antes de adicionar ao contexto
- Usar structured outputs quando possível
- Adicionar filtragem de conteúdo para padrões sensíveis
- Separar instruções de sistema do conteúdo do usuário com delimitadores claros

### 5. SSRF (`agent/tools/web.py`)
- `WebFetchTool` não bloqueia IPs internos (`127.0.0.1`, `10.x`, `172.16.x`, `192.168.x`)
- Segue redirects sem validar destino — redirect externo → rede interna
- Endpoint de metadata cloud acessível: `http://169.254.169.254/`

**Recomendações:**
- Bloquear ranges de IP privados e localhost
- Validar destinos de redirect
- Usar parser HTML adequado (BeautifulSoup) em vez de regex
- Implementar allowlist/blocklist de URLs
- Adicionar proteção contra DNS rebinding

---

## RISCO MÉDIO (Prioridade 2)

### 6. Path Traversal (`agent/tools/filesystem.py`)
- `_resolve_path()` usa comparação de string (inseguro)
- Vulnerável a TOCTOU (time-of-check-time-of-use) — arquivo pode virar symlink entre check e leitura
- `WriteFileTool` cria diretórios pai sem validação

**Recomendações:**
- Usar `Path.is_relative_to()` (Python 3.9+) em vez de comparação de string
- Verificar symlinks: `if file_path.is_symlink()`
- Rejeitar paths contendo `~username`
- Validar criação de diretórios pai

### 7. Vazamento de Keys em Logs
- `loop.py` loga argumentos de tool calls (podem conter dados sensíveis)
- Exceções do LiteLLM retornadas como conteúdo visível ao usuário

**Recomendações:**
- Sanitizar dados sensíveis dos logs
- Filtrar API keys de mensagens de erro antes de retornar ao usuário

### 8. Race Conditions
- Operações de arquivo (read/write/edit) têm TOCTOU
- Dicionário de tasks em `subagent.py` não é thread-safe

**Recomendações:**
- Usar operações atômicas de arquivo onde possível
- Adicionar file locking para operações críticas
- Usar async locks para estruturas de dados compartilhadas

### 9. Sem Limites de Tamanho
- Sem limite no tamanho de mensagens
- Sem limite no histórico de conversas (exaustão de memória)
- Download de arquivos sem validação robusta de tamanho (Discord: bypass se `size` é None)

**Recomendações:**
- Implementar limites de tamanho de mensagem
- Limitar histórico de conversas (max mensagens ou max tokens)
- Validar tamanho de arquivos antes do download

### 10. Sanitização de Input
- `telegram.py`: parser Markdown→HTML via regex — possível XSS em URLs
- `whatsapp.py`: JSON do bridge aceito sem validação de schema
- `discord.py`: sanitização de filenames incompleta (só troca `/`)

**Recomendações:**
- Usar biblioteca de sanitização HTML adequada (bleach)
- Validar todos os campos JSON contra schema
- Implementar limites de tamanho em todos os inputs
- Sanitizar filenames adequadamente (usar `safe_filename()` do helpers)

---

## RISCO BAIXO (Prioridade 3)

| Problema | Local | Recomendação |
|----------|-------|--------------|
| Sessions sem expiração, keys previsíveis | `session/manager.py` | Adicionar TTL e limpeza automática |
| Subagents com mesmos privilégios do agente principal | `subagent.py` | Aplicar princípio de menor privilégio |
| Expressões cron sem validação (DoS com intervalo mínimo) | `tools/cron.py` | Validar expressões com whitelist |
| Message bus sem autenticação entre componentes | `bus/queue.py` | Adicionar assinatura/verificação de mensagens |
| Bootstrap files do workspace sem limite de tamanho | `context.py` | Sanitizar e limitar tamanho dos arquivos |

---

## Resumo Geral

| Aspecto | Avaliação |
|---------|-----------|
| **Execução de comandos** | Inseguro — blacklist fraca, shell direto |
| **Autenticação** | Inseguro — aberto por padrão |
| **Armazenamento de secrets** | Inseguro — texto plano sem criptografia |
| **Proteção contra prompt injection** | Inexistente |
| **Proteção contra SSRF** | Inexistente |
| **Validação de input** | Parcial — gaps em múltiplos canais |
| **File operations** | Parcial — path check fraco, TOCTOU |
| **Testes de segurança** | Inexistente — 0 testes de segurança |

---

## Veredicto

**Risco ALTO para uso em produção.** O projeto é adequado para estudo e pesquisa, como o README declara, mas não deve ser exposto publicamente sem hardening significativo. As vulnerabilidades mais críticas são a execução de shell com filtro fraco, autenticação aberta por padrão, e ausência total de proteção contra prompt injection — um atacante em qualquer canal de chat poderia potencialmente executar comandos no servidor.

---

*Relatório gerado em 2026-02-08*
