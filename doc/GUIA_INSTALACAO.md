# Guia Completo: Nanobot em Ubuntu Limpo

---

## PARTE 1 — Instalacao (so faz uma vez)

### 1. Acessar o servidor

```bash
ssh root@IP_DO_SERVIDOR
```
Voce entra no terminal do servidor. Tudo que fizer aqui e no servidor, nao na sua maquina.

### 2. Atualizar o sistema

```bash
apt update && apt upgrade -y
```
Baixa a lista de pacotes e atualiza tudo que estiver desatualizado. O `-y` confirma automaticamente.

### 3. Instalar ferramentas necessarias

```bash
apt install -y python3 python3-venv python3-pip git
```
- **python3** → linguagem que o nanobot usa
- **python3-venv** → permite criar ambientes virtuais (o Ubuntu 24.04 nao traz por padrao)
- **python3-pip** → gerenciador de pacotes Python
- **git** → pra clonar o repositorio

### 4. Clonar o repositorio

```bash
cd /root
git clone https://github.com/inematds/nanobot.git
cd nanobot
```
Baixa todo o codigo do GitHub pra `/root/nanobot/`. O `cd` entra na pasta.

### 5. Criar o ambiente virtual (venv)

```bash
python3 -m venv venv
```
Cria uma pasta `venv/` com uma copia isolada do Python. Isso e como uma "caixa" onde
as dependencias do nanobot ficam separadas do sistema.

**Por que?** O Ubuntu usa Python internamente. Se voce instalar pacotes direto no
sistema, pode quebrar coisas. O venv evita isso.

### 6. Ativar o venv

```bash
source venv/bin/activate
```
Agora seu terminal esta "dentro" do venv. O prompt muda:

```
root@servidor:~/nanobot#          ← antes
(venv) root@servidor:~/nanobot#  ← depois (venv ativo)
```

A partir daqui, `python` e `pip` apontam pro venv, nao pro sistema.

### 7. Instalar o nanobot e dependencias

```bash
pip install -e .
```
- O `pip` le o arquivo `pyproject.toml` que lista tudo que o nanobot precisa (~50 pacotes)
- Baixa e instala tudo **dentro do venv**
- O `-e` significa "editavel" — se fizer `git pull` depois, as mudancas ja valem sem reinstalar
- O `.` significa "instala o projeto da pasta atual"

Isso demora 1-2 minutos.

### 8. Rodar o onboard

```bash
nanobot onboard
```
Cria a estrutura de dados em `~/.nanobot/`:

```
/root/.nanobot/
├── config.json     ← config com valores padrao (vazia)
└── workspace/
    ├── AGENTS.md   ← instrucoes pro agente
    ├── SOUL.md     ← personalidade
    ├── USER.md     ← info sobre voce
    └── memory/     ← memoria persistente
```

### 9. Editar a configuracao

```bash
nano ~/.nanobot/config.json
```
`nano` e um editor de texto no terminal. Substitua o conteudo por:

```json
{
  "providers": {
    "openrouter": {
      "apiKey": "SUA_CHAVE_OPENROUTER_AQUI"
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
      "token": "SEU_TOKEN_TELEGRAM_AQUI",
      "allowFrom": ["SEU_ID_TELEGRAM"]
    }
  }
}
```

Para salvar no nano: `Ctrl+O`, Enter, `Ctrl+X`.

**Onde conseguir cada coisa:**
- Chave OpenRouter → https://openrouter.ai/keys
- Token Telegram → Fala com o @BotFather no Telegram, cria um bot, ele te da o token
- Seu ID Telegram → Fala com o @userinfobot no Telegram

### 10. Proteger o config

```bash
chmod 600 ~/.nanobot/config.json
```
Faz com que so o root consiga ler o arquivo (tem senhas dentro).

### 11. Configurar atalhos no terminal

```bash
echo '' >> ~/.bashrc
echo '# Nanobot - atalhos' >> ~/.bashrc
echo 'alias nb="cd /root/nanobot && source venv/bin/activate"' >> ~/.bashrc
echo 'alias nbhelp="cd /root/nanobot && bash help.sh"' >> ~/.bashrc
source ~/.bashrc
```
Isso cria dois atalhos que funcionam toda vez que voce entrar via SSH:
- `nb` → ativa o ambiente do nanobot
- `nbhelp` → mostra o guia rapido

**O que e o `.bashrc`?**
E um arquivo que o Linux le automaticamente toda vez que voce abre um terminal ou
entra via SSH. E como uma "lista de preparacao automatica". Colocamos atalhos la.

**O que e um `alias`?**
E um apelido pra um comando longo. Em vez de digitar
`cd /root/nanobot && source venv/bin/activate`, voce digita so `nb`.
Funciona como o contato do celular — em vez de decorar o numero, salva com um nome.

### 12. Testar

```bash
nanobot status
```
Deve mostrar o modelo, chaves configuradas, etc.

```bash
nanobot agent -m "Ola, tudo bem?"
```
Manda uma mensagem direta pro agente. Se responder, esta tudo funcionando.

### 13. Iniciar o gateway

**Em foreground** (pra ver o que acontece, Ctrl+C pra parar):
```bash
nanobot gateway
```

**Em background** (fica rodando mesmo se fechar o terminal):
```bash
nohup python -m nanobot gateway > ~/.nanobot/gateway.log 2>&1 &
```
- `nohup` → nao morre quando fechar o SSH
- `&` → roda em segundo plano
- `> ~/.nanobot/gateway.log 2>&1` → joga a saida pro arquivo de log

### Resumo da instalacao em uma linha

```bash
apt install -y python3 python3-venv git && cd /root && git clone https://github.com/inematds/nanobot.git && cd nanobot && python3 -m venv venv && source venv/bin/activate && pip install -e . && nanobot onboard
```

---

## PARTE 2 — Uso no dia a dia (toda vez que entrar via SSH)

### O que e o `source` e por que precisa dele

Quando voce roda um script normal (`./start.sh` ou `bash start.sh`), ele abre um
terminal temporario, executa os comandos la dentro, e fecha. As mudancas morrem junto.

Quando usa `source start.sh`, os comandos rodam **no seu terminal atual**. Assim o
venv fica ativo pra voce usar.

Analogia:
- **Sem source** → alguem entra numa sala, liga a luz, sai e fecha a porta. Voce continua no escuro.
- **Com source** → voce mesmo liga a luz na sala onde esta.

### Scripts disponiveis

Na pasta `/root/nanobot/` existem dois scripts de ajuda:

**`start.sh`** — Ativa o ambiente virtual do nanobot:
```bash
source start.sh
```
Depois disso o venv esta ativo e todos os comandos `nanobot` funcionam.

**`help.sh`** — Mostra um guia rapido com todos os comandos:
```bash
bash help.sh
```

### Atalhos (aliases)

Se voce configurou os atalhos no passo 11, pode usar de qualquer lugar:

```bash
nb          # mesmo que: cd /root/nanobot && source venv/bin/activate
nbhelp      # mesmo que: cd /root/nanobot && bash help.sh
```

### Formas de ativar o ambiente

Todas fazem a mesma coisa — escolha a que preferir:

```bash
# Opcao 1: atalho (mais rapido)
nb

# Opcao 2: source no start.sh (dentro da pasta)
cd /root/nanobot
source start.sh

# Opcao 3: comando completo (sem atalho)
cd /root/nanobot && source venv/bin/activate
```

### Comandos apos ativar o ambiente

| O que quer fazer          | Comando |
|---------------------------|---------|
| Ver configuracao          | `nanobot status` |
| Ver se esta rodando       | `ps aux \| grep 'nanobot gateway'` |
| Iniciar (foreground)      | `nanobot gateway` |
| Iniciar (background)      | `nohup python -m nanobot gateway > ~/.nanobot/gateway.log 2>&1 &` |
| Parar                     | `pkill -f 'nanobot gateway'` |
| Reiniciar                 | `pkill -f 'nanobot gateway' && sleep 2 && nohup python -m nanobot gateway > ~/.nanobot/gateway.log 2>&1 &` |
| Ver log ao vivo           | `tail -f ~/.nanobot/gateway.log` |
| Ver canais                | `nanobot channels status` |
| Ver tarefas agendadas     | `nanobot cron list` |
| Checar seguranca          | `nanobot security-check` |
| Mandar mensagem direto    | `nanobot agent -m "Ola"` |
| Ver ajuda                 | `bash help.sh` |

### Atualizar o codigo

```bash
nb
git pull && pip install -e .
pkill -f 'nanobot gateway'
nohup python -m nanobot gateway > ~/.nanobot/gateway.log 2>&1 &
```

---

## PARTE 3 — Estrutura de diretorios

```
/root/
├── nanobot/                    ← CODIGO (git clone)
│   ├── venv/                   ← Ambiente virtual Python
│   ├── nanobot/                ← Codigo-fonte do bot
│   ├── bridge/                 ← Bridge WhatsApp (Node.js)
│   ├── start.sh                ← Script: ativa o venv
│   ├── help.sh                 ← Script: mostra guia rapido
│   └── pyproject.toml          ← Dependencias do projeto
│
├── .nanobot/                   ← DADOS DE RUNTIME
│   ├── config.json             ← Chaves, modelo, canais (ARQUIVO PRINCIPAL)
│   ├── gateway.log             ← Log do servidor
│   ├── sessions/               ← Historico de conversas
│   ├── cron/                   ← Tarefas agendadas
│   └── workspace/              ← Personalidade do agente
│
└── .bashrc                     ← Atalhos do terminal (nb, nbhelp)
```

**Importante:** Existem DOIS config.json. O que vale e o de `~/.nanobot/config.json`.
O que fica em `/root/nanobot/config.example.json` e so um exemplo e NAO e usado pelo nanobot.

---

## PARTE 4 — Resumo visual

```
Entrou via SSH
    │
    ├── nb                              ← ativa o ambiente
    │
    ├── nanobot status                  ← verifica se tudo ok
    │
    ├── nanobot gateway                 ← inicia (ou nohup ... &)
    │
    └── pronto! bot funcionando
```

```
Quer parar?
    │
    └── pkill -f 'nanobot gateway'      ← mata o processo

Quer ver o que esta acontecendo?
    │
    └── tail -f ~/.nanobot/gateway.log  ← log em tempo real
```
