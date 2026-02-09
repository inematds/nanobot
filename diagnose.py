#!/usr/bin/env python3
"""Diagnostic script for nanobot config issues."""
import json
from pathlib import Path

path = Path.home() / ".nanobot" / "config.json"
print(f"1. Path: {path}")
print(f"2. Exists: {path.exists()}")

if not path.exists():
    print("ERRO: Arquivo nao existe! Crie com: nano ~/.nanobot/config.json")
    exit(1)

content = path.read_text()
print(f"3. Size: {len(content)} bytes")
print(f"4. Content:\n{content}")

try:
    raw = json.loads(content)
    print(f"5. JSON OK - keys: {list(raw.keys())}")
except json.JSONDecodeError as e:
    print(f"5. JSON INVALIDO: {e}")
    exit(1)

providers = raw.get("providers", {})
print(f"6. Providers: {list(providers.keys())}")

or_config = providers.get("openrouter", {})
or_key = or_config.get("apiKey", "")
print(f"7. OpenRouter apiKey: {'SIM (' + or_key[:8] + '...)' if or_key else 'VAZIO'}")

try:
    from nanobot.config.loader import convert_keys
    from nanobot.config.schema import Config
    converted = convert_keys(raw)
    config = Config.model_validate(converted)
    print(f"8. Config loaded OK")
    print(f"9. Model: {config.agents.defaults.model}")
    print(f"10. OR api_key: {'SIM' if config.providers.openrouter.api_key else 'VAZIO'}")
except Exception as e:
    print(f"8. ERRO ao carregar config: {e}")
