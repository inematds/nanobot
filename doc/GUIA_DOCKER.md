# Guia Completo: Nanobot com Docker

---

## Como funciona o Docker vs VPS Direto

Na VPS direto, **voce** cria o venv, instala pacotes, ativa o ambiente. Com Docker,
ele faz tudo isso **automaticamente dentro de um container** (uma "mini maquina virtual" isolada).

```
VPS Direto:                          Docker:
  Voce faz tudo manualmente            O Dockerfile faz tudo sozinho
  apt install python3...               FROM python:3.12 (ja vem pronto)
  python3 -m venv venv                 (nao precisa, ja e isolado)
  source venv/bin/activate             (nao precisa)
  pip install -e .                     uv pip install . (automatico)
  nanobot onboard                      (precisa rodar uma vez)
  nanobot gateway                      (inicia sozinho)
```

---

## Passo a passo

### 1. Clonar o repositorio (se ainda nao tem)

```bash
git clone https://github.com/inematds/nanobot.git
cd nanobot
```

### 2. Construir e subir o container

```bash
docker compose up -d
```

O que isso faz por dentro (leva 2-3 minutos na primeira vez):

| Etapa | O que acontece |
|-------|----------------|
| `FROM python3.12` | Baixa uma imagem base com Python 3.12 |
| `apt install nodejs` | Instala Node.js 20 (pra bridge do WhatsApp) |
| `useradd nanobot` | Cria um usuario sem privilegios (seguranca) |
| `uv pip install .` | Instala todas as dependencias do nanobot |
| `npm install && build` | Compila a bridge do WhatsApp |
| `mkdir .nanobot/...` | Cria a estrutura de dados |
| `CMD ["gateway"]` | Quando iniciar, roda `nanobot gateway` automaticamente |

O `-d` significa "detached" — roda em background.

### 3. Rodar o onboard (primeira vez)

```bash
docker compose exec nanobot nanobot onboard
```

Isso entra no container e roda o `nanobot onboard` la dentro, criando o config e o workspace.

### 4. Colocar sua configuracao

O config fica **dentro do container**, num volume Docker. Para editar:

**Opcao A: copiar um arquivo pra dentro do container**

Primeiro crie o arquivo na sua maquina:
```bash
cat > /tmp/nanobot-config.json << 'EOF'
{
  "providers": {
    "openrouter": {
      "apiKey": "sk-or-v1-SUA_CHAVE"
    }
  },
  "agents": {
    "defaults": {
      "model": "qwen/qwen3-coder-next"
    }
  },
  "channels": {
    "telegram": {
      "enabled": true,
      "token": "SEU_TOKEN_DO_BOTFATHER",
      "allowFrom": ["SEU_ID_NUMERICO"]
    }
  }
}
EOF
```

Depois copie pra dentro:
```bash
docker compose cp /tmp/nanobot-config.json nanobot:/home/nanobot/.nanobot/config.json
```

**Opcao B: editar direto dentro do container**
```bash
docker compose exec nanobot bash
nano ~/.nanobot/config.json
exit
```

**Opcao C: usar variaveis de ambiente (sem editar arquivo)**

Edite o `docker-compose.yml` e descomente as linhas de environment:
```yaml
environment:
  - NANOBOT_PROVIDERS__OPENROUTER__API_KEY=sk-or-v1-xxx
  - NANOBOT_CHANNELS__TELEGRAM__ENABLED=true
  - NANOBOT_CHANNELS__TELEGRAM__TOKEN=seu_token
```

### 5. Reiniciar pra pegar a nova config

```bash
docker compose restart
```

### 6. Ver se esta funcionando

```bash
# Ver logs ao vivo
docker compose logs -f

# Ver status
docker compose exec nanobot nanobot status

# Mandar mensagem de teste
docker compose exec nanobot nanobot agent -m "Ola!"
```

---

## Comandos do dia a dia com Docker

| O que quer fazer | Comando |
|------------------|---------|
| Iniciar | `docker compose up -d` |
| Parar | `docker compose down` |
| Reiniciar | `docker compose restart` |
| Ver logs ao vivo | `docker compose logs -f` |
| Ver status | `docker compose exec nanobot nanobot status` |
| Entrar no container | `docker compose exec nanobot bash` |
| Mandar mensagem | `docker compose exec nanobot nanobot agent -m "Ola"` |
| Atualizar codigo | `git pull && docker compose up -d --build` |

---

## Diferenca principal: onde ficam os dados

| | VPS Direto | Docker |
|--|-----------|--------|
| Codigo | `/root/nanobot/` | `/app/` (dentro do container) |
| Config | `/root/.nanobot/config.json` | Volume `nanobot-data` (persistente) |
| Venv | `/root/nanobot/venv/` | Nao precisa (ja e isolado) |
| Precisa ativar venv? | Sim, sempre | Nao |
| Sobrevive reboot? | Nao (sem systemd) | Sim (`restart: unless-stopped`) |
| Limites de recurso | Sem limite | 2GB RAM, 2 CPUs |

---

## Vantagens do Docker

- **Reinicia sozinho** se o servidor reiniciar (`restart: unless-stopped`)
- **Isolado** — nao mexe no sistema, nao precisa de venv
- **Limites de recurso** — maximo 2GB RAM, 2 CPUs (protecao)
- **Seguranca** — roda como usuario sem privilegios, `no-new-privileges`
- **Dados persistentes** — o volume `nanobot-data` sobrevive a rebuilds

---

## O que o docker-compose.yml configura

```yaml
services:
  nanobot:
    build: .                              # Constroi a partir do Dockerfile
    container_name: nanobot               # Nome fixo do container
    restart: unless-stopped               # Reinicia sozinho (exceto se voce parar)
    ports:
      - "127.0.0.1:18790:18790"           # Gateway so em localhost
    volumes:
      - nanobot-data:/home/nanobot/.nanobot  # Dados persistentes
    environment:
      - TZ=America/Sao_Paulo              # Timezone
    deploy:
      resources:
        limits:
          memory: 2G                      # Maximo 2GB RAM
          cpus: "2.0"                     # Maximo 2 CPUs
    security_opt:
      - no-new-privileges:true            # Sem escalar privilegios
    tmpfs:
      - /tmp:size=100M                    # /tmp em memoria (100MB)
```
