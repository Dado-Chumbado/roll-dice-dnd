# D&D Character Sheet — Plano de Implementação (v4)

## Objetivo

Importar fichas de personagem via PDF exportado do D&D Beyond, salvar localmente como JSON e expor os dados ao bot Discord. O JSON local é a **fonte de verdade durante o jogo** — HP, spell slots, inventário e qualquer outro estado são gerenciados pelo bot diretamente no arquivo, sem depender do DnD Beyond.

Todos os comandos usam prefixo `!` (padrão do bot).

---

## Fases de Implementação

### Phase 0 — Validação do PDF (BLOQUEANTE)

**Objetivo:** Inspecionar os form fields reais de um PDF exportado do D&D Beyond e definir o mapeamento campo → JSON antes de qualquer código de produção.

**Tarefas:**
1. Instalar `pdfplumber` no projeto (`poetry add pdfplumber`)
2. Criar `src/plugins/character/pdf_inspector.py` — script one-shot que lista todos os form fields do PDF com seus nomes e valores de exemplo
3. Rodar o script em um PDF real fornecido pelo jogador
4. Documentar o mapeamento `pdf_field_name → json_key` como constante em `pdf_extractor.py`
5. Validar que os campos críticos existem: nome, nível, classe, HP máx, atributos, spell slots

**Entrega:** dicionário de mapeamento validado + `pdfplumber` adicionado ao pyproject.toml

---

### Phase 1 — Importação e Consulta (depende da Phase 0)

**Objetivo:** `!sync` importa o PDF e cria/sobrescreve o JSON; `!ficha` exibe o resumo em PT-BR.

**Arquivos a criar:**
```
src/plugins/character/
  __init__.py
  plugin_character.py       # Plugin principal com !sync e !ficha
  plugin_config.json        # Aliases e descrições dos comandos
  character_manager.py      # load_character() / save_character()
  pdf_extractor.py          # import_pdf(file_path, player_name) → dict
  sheet_formatter.py        # format_sheet(data) → string PT-BR
  tests/
    __init__.py
    test_pdf_extractor.py
    test_sheet_formatter.py
    test_character_manager.py
```

**Comandos:**

| Comando | O que faz |
|---------|-----------|
| `!sync <nome>` (com PDF em anexo) | Baixa o PDF, chama `import_pdf()`, salva JSON em `data/characters/<nome>.json` |
| `!ficha` | Exibe resumo da ficha do autor da mensagem |
| `!ficha <nome>` | Mestre consulta ficha de outro jogador |

**Estrutura do JSON (base + sessão inicial):**
```json
{
  "meta": { "player": "Ana", "source": "pdf", "synced_at": "..." },
  "base": {
    "name": "Thalindra", "level": 3, "class": "Wizard",
    "subclass": "School of Evocation", "race": "Elf", "background": "Sage",
    "hp_max": 18, "armor_class": 13, "initiative": 3, "speed": "30 ft",
    "proficiency_bonus": 2,
    "attributes": {
      "strength":     { "score": 8,  "modifier": -1 },
      "dexterity":    { "score": 16, "modifier": 3  },
      "constitution": { "score": 14, "modifier": 2  },
      "intelligence": { "score": 18, "modifier": 4  },
      "wisdom":       { "score": 12, "modifier": 1  },
      "charisma":     { "score": 10, "modifier": 0  }
    },
    "saving_throws": ["intelligence", "wisdom"],
    "skills": [
      { "name": "Arcana", "modifier": 6, "proficient": true }
    ],
    "attacks": [
      { "name": "Magic Missile", "bonus": null, "damage": "1d4+1 force", "notes": "auto-hit" }
    ],
    "spell_slots_max": { "1": 4, "2": 2 },
    "spells_known": [{ "name": "Fireball", "level": 3 }],
    "class_features": [{ "name": "Arcane Recovery", "description": "..." }],
    "equipment_base": ["Spellbook", "Oak Wand"]
  },
  "session": {
    "hp_current": 18,
    "spell_slots_used": { "1": 0, "2": 0 },
    "inventory": [],
    "notes": ""
  }
}
```

**Regra de sync:** ao rodar `!sync` com novo PDF, `base` é sobrescrito e `session.hp_current` volta ao `hp_max`. `session.inventory` e `session.notes` são preservados.

---

### Phase 2 — Gestão de Sessão (depende da Phase 1)

**Objetivo:** Todos os comandos de mutação do estado de sessão durante o jogo.

**Comandos:**

| Comando | O que faz |
|---------|-----------|
| `!hp -8` / `!hp +4` | Desconta ou recupera HP (clampado entre 0 e hp_max) |
| `!slot <nível>` | Marca 1 slot do nível como usado |
| `!slot <nível> reset` | Restaura todos os slots de um nível |
| `!rest short` / `!rest long` | Restaura recursos conforme regras de descanso |
| `!slots` | Mostra slots disponíveis vs. usados |
| `!inv` | Mostra inventário atual |
| `!item add <nome> [qty]` | Adiciona item ao inventário de sessão |
| `!item remove <nome> [qty]` | Remove item do inventário |

**Funções a implementar em `character_manager.py`:**
- `update_hp(player_name, delta)` → clamp 0..hp_max
- `use_slot(player_name, level)` → erro se já esgotado
- `reset_slot(player_name, level)`
- `rest(player_name, rest_type)` → "short": recupera metade HP; "long": hp=hp_max + todos os slots resetados
- `update_inventory(player_name, item_name, qty, add: bool)`

**Testes adicionais:**
- `test_session_commands.py` — cobre cada mutação com fichas de teste pré-geradas

---

## Storage

```
data/
  characters/
    rafael.json
    ana.json
```

---

## Stack

- **Python 3.12+**
- **pdfplumber** — extração de form fields do PDF
- Arquivos JSON em disco — sem banco de dados adicional
- Comandos `!` via `@bot.command()` (padrão existente no projeto)

---

## Notas

- **O JSON é a fonte de verdade durante o jogo.** DnD Beyond é usado só para gerar o PDF no sync.
- **Tradução PT-BR na formatação, não na extração.** JSONs guardam nomes em inglês conforme vêm do PDF.
- **Phase 0 é bloqueante** — o mapeamento de campos do PDF precisa ser validado antes de implementar o extrator.
- **`!sync` recebe o PDF como attachment** na mensagem Discord (não como path local).
