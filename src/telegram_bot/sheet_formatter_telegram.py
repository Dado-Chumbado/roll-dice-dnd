"""PT-BR character sheet formatting for Telegram (HTML parse mode)."""

import html

_ATTR_SHORT = {
    "strength": "FOR", "dexterity": "DES", "constitution": "CON",
    "intelligence": "INT", "wisdom": "SAB", "charisma": "CAR",
}

_ATTR_PT = {
    "strength": "Força", "dexterity": "Destreza", "constitution": "Constituição",
    "intelligence": "Inteligência", "wisdom": "Sabedoria", "charisma": "Carisma",
}

_SKILL_PT = {
    "Acrobatics": "Acrobacia", "AnimalHandling": "Trato com Animais",
    "Arcana": "Arcanismo", "Athletics": "Atletismo", "Deception": "Enganação",
    "History": "História", "Insight": "Intuição", "Intimidation": "Intimidação",
    "Investigation": "Investigação", "Medicine": "Medicina", "Nature": "Natureza",
    "Perception": "Percepção", "Performance": "Atuação", "Persuasion": "Persuasão",
    "Religion": "Religião", "SleightOfHand": "Prestidigitação",
    "Stealth": "Furtividade", "Survival": "Sobrevivência",
}


def _s(n: int) -> str:
    return f"+{n}" if n >= 0 else str(n)


def _b(text) -> str:
    return f"<b>{html.escape(str(text))}</b>"


def _hp_bar(current: int, maximum: int, width: int = 10) -> str:
    if maximum <= 0:
        return ""
    filled = round(max(0, min(current / maximum, 1)) * width)
    return "[" + "█" * filled + "░" * (width - filled) + "]"


# ---------------------------------------------------------------------------
# Simple view — essentials, one message
# ---------------------------------------------------------------------------

def format_sheet_simple_telegram(data: dict) -> str:
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
        f"{_b(base['name'])} — {html.escape(level_str)} | {html.escape(base['race'])}",
        f"❤️ HP: {_b(f'{hp_cur}/{hp_max}')}{html.escape(temp_str)} {bar}",
        f"🛡️ CA: {_b(base['armor_class'])} | Init: {_b(_s(base['initiative']))} | Vel: {_b(base['speed'])}",
    ]

    attrs = base.get("attributes", {})
    lines.append("  ".join(
        f"{_b(_ATTR_SHORT[k])} {_s(attrs.get(k, {}).get('modifier', 0))}"
        for k in _ATTR_PT
    ))

    attacks = base.get("attacks", [])
    if attacks:
        atk_parts = [
            f"{_b(a['name'])} {html.escape(a.get('bonus') or '—')} {html.escape(a.get('damage') or '—')}"
            for a in attacks
        ]
        lines.append("⚔️ " + "  |  ".join(atk_parts))

    slots_max  = base.get("spell_slots_max", {})
    slots_used = session.get("spell_slots_used", {})
    if slots_max:
        slot_parts = [
            f"Nv{lvl}: {_b(f'{slots_max[lvl] - slots_used.get(lvl,0)}/{slots_max[lvl]}')}"
            for lvl in sorted(slots_max.keys(), key=int)
        ]
        lines.append("✨ " + "  ".join(slot_parts))

    synced = meta.get("synced_at", "?")[:10]
    lines.append(f"<i>Sync: {synced}</i>")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Full view — complete sheet
# ---------------------------------------------------------------------------

def format_sheet_full_telegram(data: dict) -> str:
    base    = data["base"]
    session = data["session"]
    meta    = data["meta"]

    lines = []

    level_str = base.get("multiclass") or f"{base['class']} {base['level']}"
    lines.append(f"{_b(base['name'])} — {html.escape(level_str)}")
    lines.append(
        f"Raça: {html.escape(base['race'])} | "
        f"Antecedente: {html.escape(base['background'])} | "
        f"Alinhamento: {html.escape(base.get('alignment','—'))}"
    )
    lines.append("")

    hp_cur   = session["hp_current"]
    hp_max   = base["hp_max"]
    temp     = session.get("temp_hp", 0)
    temp_str = f"  (+{temp} temp)" if temp else ""
    lines.append(f"❤️ HP: {_b(f'{hp_cur}/{hp_max}')}{temp_str}  {_hp_bar(hp_cur, hp_max)}")
    lines.append(
        f"🛡️ CA: {_b(base['armor_class'])} | "
        f"Iniciativa: {_b(_s(base['initiative']))} | "
        f"Velocidade: {_b(base['speed'])}"
    )
    lines.append(
        f"Dados de Vida: {_b(base['hit_dice'])} | "
        f"Bônus de Proficiência: {_b(_s(base['proficiency_bonus']))}"
    )
    lines.append("")

    lines.append("<b>Atributos</b>")
    attrs = base.get("attributes", {})
    lines.append("  ".join(
        f"{_ATTR_SHORT[k]} {attrs.get(k,{}).get('score','?')} ({_s(attrs.get(k,{}).get('modifier',0))})"
        for k in _ATTR_PT
    ))
    lines.append("")

    lines.append("<b>Salvaguardas</b>")
    saves = base.get("saving_throws", {})
    lines.append("  ".join(
        f"{'●' if saves.get(k,{}).get('proficient') else '○'} {_ATTR_SHORT[k]} {_s(saves.get(k,{}).get('modifier',0))}"
        for k in _ATTR_PT
    ))
    lines.append("")

    prof_skills = [(k, v) for k, v in base.get("skills", {}).items() if v.get("proficient")]
    if prof_skills:
        lines.append("<b>Perícias (proficiências)</b>")
        lines.append("  |  ".join(
            f"{html.escape(_SKILL_PT.get(sk, sk))} {_s(sv.get('modifier', 0))}"
            for sk, sv in sorted(prof_skills, key=lambda x: _SKILL_PT.get(x[0], x[0]))
        ))
        lines.append("")

    lines.append(
        f"Percepção Passiva: {_b(base.get('passive_perception','?'))} | "
        f"Intuição Passiva: {_b(base.get('passive_insight','?'))} | "
        f"Investigação Passiva: {_b(base.get('passive_investigation','?'))}"
    )
    lines.append("")

    attacks = base.get("attacks", [])
    if attacks:
        lines.append("<b>Ataques</b>")
        for atk in attacks:
            lines.append(
                f"  • {_b(atk['name'])} | "
                f"Ataque: {html.escape(atk.get('bonus') or '—')} | "
                f"Dano: {html.escape(atk.get('damage') or '—')}"
            )
        lines.append("")

    slots_max  = base.get("spell_slots_max", {})
    slots_used = session.get("spell_slots_used", {})
    if slots_max:
        lines.append("<b>Espaços de Magia</b>")
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
        lines.append("<b>Moedas:</b> " + "  ".join(coins))
        lines.append("")

    synced = meta.get("synced_at", "?")[:10]
    lines.append(f"<i>Sync: {synced} | Jogador: {html.escape(meta.get('player','?'))}</i>")

    return "\n".join(lines)
