"""PT-BR formatting of character sheet data for Discord messages."""

_ATTR_PT = {
    "strength":     "Força",
    "dexterity":    "Destreza",
    "constitution": "Constituição",
    "intelligence": "Inteligência",
    "wisdom":       "Sabedoria",
    "charisma":     "Carisma",
}

_ATTR_SHORT = {
    "strength": "FOR", "dexterity": "DES", "constitution": "CON",
    "intelligence": "INT", "wisdom": "SAB", "charisma": "CAR",
}

_SKILL_PT = {
    "Acrobatics":    "Acrobacia",
    "AnimalHandling":"Trato com Animais",
    "Arcana":        "Arcanismo",
    "Athletics":     "Atletismo",
    "Deception":     "Enganação",
    "History":       "História",
    "Insight":       "Intuição",
    "Intimidation":  "Intimidação",
    "Investigation": "Investigação",
    "Medicine":      "Medicina",
    "Nature":        "Natureza",
    "Perception":    "Percepção",
    "Performance":   "Atuação",
    "Persuasion":    "Persuasão",
    "Religion":      "Religião",
    "SleightOfHand": "Prestidigitação",
    "Stealth":       "Furtividade",
    "Survival":      "Sobrevivência",
}


def _sign(n: int) -> str:
    return f"+{n}" if n >= 0 else str(n)


def _prof_mark(proficient: bool) -> str:
    return "●" if proficient else "○"


def _hp_bar(current: int, maximum: int, width: int = 10) -> str:
    if maximum <= 0:
        return ""
    ratio = max(0, min(current / maximum, 1))
    filled = round(ratio * width)
    return "[" + "█" * filled + "░" * (width - filled) + "]"


# ---------------------------------------------------------------------------
# Simple view — one compact message, essentials only
# ---------------------------------------------------------------------------

def format_sheet_simple(data: dict) -> str:
    base    = data["base"]
    session = data["session"]
    meta    = data["meta"]

    level_str = base.get("multiclass") or f"{base['class']} {base['level']}"
    hp_cur    = session["hp_current"]
    hp_max    = base["hp_max"]
    temp      = session.get("temp_hp", 0)
    temp_str  = f" (+{temp} temp)" if temp else ""
    bar       = _hp_bar(hp_cur, hp_max)

    lines = [
        f"**{base['name']}** — {level_str} | {base['race']}",
        f"❤️ HP: **{hp_cur}/{hp_max}**{temp_str} {bar}",
        f"🛡️ CA: **{base['armor_class']}** | Init: **{_sign(base['initiative'])}** | Vel: **{base['speed']}**",
    ]

    # Attributes row
    attrs = base.get("attributes", {})
    attr_row = "  ".join(
        f"**{_ATTR_SHORT[k]}** {_sign(attrs.get(k, {}).get('modifier', 0))}"
        for k in _ATTR_PT
    )
    lines.append(attr_row)

    # Attacks (compact)
    attacks = base.get("attacks", [])
    if attacks:
        atk_parts = []
        for a in attacks:
            bonus = f" Atk:{a['bonus']}" if a.get("bonus") else ""
            dmg   = f" {a.get('damage')}" if a.get("damage") else ""
            atk_parts.append(f"**{a['name']}**{bonus}{dmg}")
        lines.append("⚔️ " + "  |  ".join(atk_parts))

    # Spell slots (compact)
    slots_max  = base.get("spell_slots_max", {})
    slots_used = session.get("spell_slots_used", {})
    if slots_max:
        slot_parts = []
        for lvl in sorted(slots_max.keys(), key=int):
            remaining = slots_max[lvl] - slots_used.get(lvl, 0)
            slot_parts.append(f"Nv{lvl}: {remaining}/{slots_max[lvl]}")
        lines.append("✨ " + "  ".join(slot_parts))

    synced = meta.get("synced_at", "?")[:10]
    lines.append(f"*Sync: {synced}*")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Full view — complete sheet
# ---------------------------------------------------------------------------

def format_sheet_full(data: dict) -> str:
    base    = data["base"]
    session = data["session"]
    meta    = data["meta"]

    lines = []

    level_str = base.get("multiclass") or f"{base['class']} {base['level']}"
    lines.append(f"**{base['name']}** — {level_str}")
    lines.append(f"Raça: {base['race']} | Antecedente: {base['background']} | Alinhamento: {base.get('alignment','—')}")
    lines.append("")

    hp_cur   = session["hp_current"]
    hp_max   = base["hp_max"]
    temp     = session.get("temp_hp", 0)
    temp_str = f"  (+{temp} temp)" if temp else ""
    lines.append(f"❤️ **HP: {hp_cur}/{hp_max}**{temp_str}  {_hp_bar(hp_cur, hp_max)}")
    lines.append(f"🛡️ CA: **{base['armor_class']}** | Iniciativa: **{_sign(base['initiative'])}** | Velocidade: **{base['speed']}**")
    lines.append(f"Dados de Vida: **{base['hit_dice']}** | Bônus de Proficiência: **{_sign(base['proficiency_bonus'])}**")
    lines.append("")

    lines.append("**Atributos**")
    attrs = base.get("attributes", {})
    lines.append("  ".join(
        f"{_ATTR_SHORT[k]} {attrs.get(k,{}).get('score','?')} ({_sign(attrs.get(k,{}).get('modifier',0))})"
        for k in _ATTR_PT
    ))
    lines.append("")

    lines.append("**Salvaguardas**")
    saves = base.get("saving_throws", {})
    lines.append("  ".join(
        f"{_prof_mark(saves.get(k,{}).get('proficient',False))} {_ATTR_SHORT[k]} {_sign(saves.get(k,{}).get('modifier',0))}"
        for k in _ATTR_PT
    ))
    lines.append("")

    prof_skills = [(k, v) for k, v in base.get("skills", {}).items() if v.get("proficient")]
    if prof_skills:
        lines.append("**Perícias (proficiências)**")
        lines.append("  |  ".join(
            f"{_SKILL_PT.get(sk, sk)} {_sign(sv.get('modifier', 0))}"
            for sk, sv in sorted(prof_skills, key=lambda x: _SKILL_PT.get(x[0], x[0]))
        ))
        lines.append("")

    lines.append(
        f"Percepção Passiva: **{base.get('passive_perception','?')}** | "
        f"Intuição Passiva: **{base.get('passive_insight','?')}** | "
        f"Investigação Passiva: **{base.get('passive_investigation','?')}**"
    )
    lines.append("")

    attacks = base.get("attacks", [])
    if attacks:
        lines.append("**Ataques**")
        for atk in attacks:
            lines.append(f"  • **{atk['name']}** | Ataque: {atk.get('bonus') or '—'} | Dano: {atk.get('damage') or '—'}")
        lines.append("")

    slots_max  = base.get("spell_slots_max", {})
    slots_used = session.get("spell_slots_used", {})
    if slots_max:
        lines.append("**Espaços de Magia**")
        for lvl in sorted(slots_max.keys(), key=int):
            total     = slots_max[lvl]
            used      = slots_used.get(lvl, 0)
            remaining = total - used
            lines.append(f"  Nível {lvl}: {'◆'*remaining}{'◇'*used} ({remaining}/{total})")
        lines.append("")

    currency = session.get("currency", {})
    coins = [
        f"{v} {lbl}" for k, lbl in [("pp","PPl"),("gp","PO"),("ep","PE"),("sp","PP"),("cp","PC")]
        if (v := currency.get(k, 0))
    ]
    if coins:
        lines.append("**Moedas:** " + "  ".join(coins))
        lines.append("")

    if base.get("proficiencies_and_languages"):
        lines.append("**Proficiências e Idiomas**")
        lines.append(base["proficiencies_and_languages"])
        lines.append("")

    if base.get("features_text"):
        lines.append("**Habilidades e Traços**")
        lines.append(base["features_text"])
        lines.append("")

    if base.get("actions_text"):
        lines.append("**Ações**")
        lines.append(base["actions_text"])
        lines.append("")

    traits = []
    if base.get("personality_traits"):
        traits.append(f"*Personalidade:* {base['personality_traits']}")
    if base.get("ideals"):
        traits.append(f"*Ideais:* {base['ideals']}")
    if base.get("bonds"):
        traits.append(f"*Vínculos:* {base['bonds']}")
    if base.get("flaws"):
        traits.append(f"*Fraquezas:* {base['flaws']}")
    if traits:
        lines.append("**Traços de Personalidade**")
        lines.extend(traits)
        lines.append("")

    synced = meta.get("synced_at", "?")[:10]
    lines.append(f"*Sync: {synced} | Jogador: {meta.get('player','?')}*")

    return "\n".join(lines)


def format_spells(data: dict) -> str:
    base    = data["base"]
    session = data["session"]
    spells  = base.get("spells", [])
    char    = base["name"]

    if not spells:
        return f"✨ **{char}** não possui magias registradas."

    slots_max  = base.get("spell_slots_max", {})
    slots_used = session.get("spell_slots_used", {})

    lines = [f"✨ **Magias — {char}**"]
    if slots_max:
        slot_parts = []
        for lvl in sorted(slots_max.keys(), key=int):
            total     = slots_max[lvl]
            remaining = total - slots_used.get(lvl, 0)
            slot_parts.append(f"Nv{lvl}: {'◆'*remaining}{'◇'*(total-remaining)} ({remaining}/{total})")
        lines.append("  ".join(slot_parts))
    lines.append("")

    for i, s in enumerate(spells):
        prepared = "✅" if s.get("prepared") else "○ "
        cast     = s.get("cast_time") or "—"
        rng      = s.get("range") or "—"
        dur      = s.get("duration") or "—"
        lines.append(f"{prepared} `[{i}]` **{s['name']}**  {cast} | {rng} | {dur}")

    lines.append(f"\n*Use `!magia <índice>` para detalhes de uma magia.*")
    return "\n".join(lines)


def format_spell_detail(data: dict, index: int) -> str:
    spells = data["base"].get("spells", [])
    if not spells:
        return "✨ Nenhuma magia registrada."
    if index < 0 or index >= len(spells):
        return f"✨ Índice inválido. Use `!magias` para ver a lista (0–{len(spells)-1})."

    s    = spells[index]
    char = data["base"]["name"]
    lines = [
        f"✨ **{s['name']}** — {char}",
        f"Preparada: {'✅ Sim' if s.get('prepared') else '○  Não'}",
        f"Tempo de conjuração: **{s.get('cast_time') or '—'}**",
        f"Alcance: **{s.get('range') or '—'}**",
        f"Componentes: **{s.get('components') or '—'}**",
        f"Duração: **{s.get('duration') or '—'}**",
    ]
    if s.get("save_hit") and s["save_hit"] not in ("--", ""):
        lines.append(f"Ataque/Salvaguarda: **{s['save_hit']}**")
    if s.get("source"):
        lines.append(f"Fonte: *{s['source']}*")
    if s.get("notes"):
        lines.append(f"Notas: {s['notes']}")
    return "\n".join(lines)


def format_sheet(data: dict, mode: str = "simples") -> str:
    if mode == "completa":
        return format_sheet_full(data)
    return format_sheet_simple(data)
