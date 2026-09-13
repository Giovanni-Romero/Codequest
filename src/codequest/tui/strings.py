"""UI chrome text, in one place, in two languages.

Every ``Static``/``Label``/``Button``/dialog string a player reads in the *chrome* of
the game - titles, taglines, panel headers, prompts - is looked up here instead of
typed inline in a screen or widget. That is what makes a language switch possible: one
module owns the translation table, so a screen only ever asks "what does this key say
right now" and never hardcodes an answer.

Two things are deliberately **not** here, and staying out is as much a design decision
as being in:

- **Mission content** (teaching, brief, hints). That comes from YAML in ``content/``,
  picked per language by ``MissionService`` - a different mechanism, because a mission
  is a document a curriculum designer writes, not UI copy a screen composes.
- **Engine-produced sentences** (a verdict's summary, a failure detail, a service
  exception's message). Those are written by ``engine/`` and ``services/`` - the layer
  that owns the failure taxonomy and the wording that goes with it, per
  ``widgets/test_results.py``'s own docstring. Translating them here would let the UI
  quietly re-author a sentence a different layer is responsible for, which is exactly
  the kind of drift ``CLAUDE.md`` section 3 exists to prevent. They stay English until
  that layer grows its own language support.

Runtime language state is a module-level variable rather than something threaded
through every widget's constructor, because it changes rarely (a player flips it once
in Settings) and is read constantly (every screen, every render). Passing it explicitly
everywhere would mean touching every ``compose()`` in the package for no benefit; a
single mutable slot, read only from the UI thread, is the honest size of the problem.
"""

from __future__ import annotations

Language = str  # "en" or "pt"

DEFAULT_LANGUAGE: Language = "en"
LANGUAGES: tuple[Language, ...] = ("en", "pt")

_current_language: Language = DEFAULT_LANGUAGE

#: key -> {"en": ..., "pt": ...}. Grouped by screen with a comment header, in the same
#: order the screens appear in ``tui/screens/``, so a translator can work top to bottom.
_STRINGS: dict[str, dict[Language, str]] = {
    # -------------------------------------------------------------- main_menu.py
    "main_menu.title": {"en": "C O D E Q U E S T", "pt": "C O D E Q U E S T"},
    "main_menu.tagline": {"en": "chart a course", "pt": "trace um rumo"},
    "main_menu.settings": {"en": "Settings", "pt": "Configurações"},
    "main_menu.quit": {"en": "Quit", "pt": "Sair"},
    "track.python.note": {
        "en": "foundations to async, ten islands",
        "pt": "do básico ao assíncrono, dez ilhas",
    },
    "track.ai_engineering.note": {
        "en": "seventeen islands, 136 missions",
        "pt": "dezessete ilhas, 136 missões",
    },
    "track.java.note": {"en": "planned for v1.1", "pt": "planejado para v1.1"},
    "track.typescript.note": {"en": "planned for v1.2", "pt": "planejado para v1.2"},
    # ------------------------------------------------------------ save_select.py
    "save_select.title": {"en": "Career saves", "pt": "Jogos salvos"},
    "save_select.new_save": {"en": "New save", "pt": "Novo save"},
    "save_select.delete": {"en": "Delete", "pt": "Apagar"},
    "save_select.back": {"en": "Back", "pt": "Voltar"},
    "save_select.name_placeholder": {
        "en": "name for a new save",
        "pt": "nome para o novo save",
    },
    "save_select.slots_free": {
        "en": "{remaining} of {max} slots free - N to create",
        "pt": "{remaining} de {max} vagas livres - N para criar",
    },
    "save_select.slots_full": {
        "en": "All {max} slots used - delete one to create another",
        "pt": "Todas as {max} vagas em uso - apague uma para criar outra",
    },
    "save_select.delete_confirm": {
        "en": "Delete '{name}'?\n\n"
        "[$parchment-dim]{xp} XP and every solution written on this save are removed. "
        "This cannot be undone.[/$parchment-dim]",
        "pt": "Apagar '{name}'?\n\n"
        "[$parchment-dim]{xp} XP e todas as soluções escritas neste save serão removidas. "
        "Isso não pode ser desfeito.[/$parchment-dim]",
    },
    "save_select.level_xp_missions": {
        "en": "level {level}  {xp:>4} XP  {done}/{total} missions",
        "pt": "nível {level}  {xp:>4} XP  {done}/{total} missões",
    },
    # -------------------------------------------------------------- island_map.py
    "island_map.saves": {"en": "Saves", "pt": "Saves"},
    "island_map.refresh": {"en": "Refresh", "pt": "Atualizar"},
    "island_map.heading": {
        "en": "{name}  -  level {level}  -  {xp} XP  -  {done}/{total} missions",
        "pt": "{name}  -  nível {level}  -  {xp} XP  -  {done}/{total} missões",
    },
    "island_map.requirement_missions": {
        "en": "complete {n} missions",
        "pt": "complete {n} missões",
    },
    "island_map.requirement_xp": {"en": "reach {n} XP", "pt": "alcance {n} XP"},
    "island_map.requirement_island": {
        "en": "unlock {island} first",
        "pt": "desbloqueie {island} primeiro",
    },
    "island_map.requirement_mission": {
        "en": "complete {mission}",
        "pt": "conclua {mission}",
    },
    "island_map.locked_prefix": {"en": "locked", "pt": "bloqueada"},
    "island_map.hints_used": {"en": "{n} hints", "pt": "{n} dicas"},
    # ----------------------------------------------------------------- mission.py
    "mission.run": {"en": "Run", "pt": "Rodar"},
    "mission.hint": {"en": "Hint", "pt": "Dica"},
    "mission.mentor": {"en": "Mentor", "pt": "Mentor"},
    "mission.teaching": {"en": "Teaching", "pt": "Lição"},
    "mission.reset": {"en": "Reset", "pt": "Reiniciar"},
    "mission.map": {"en": "Map", "pt": "Mapa"},
    "mission.teaching_title": {"en": "Teaching", "pt": "Lição"},
    "mission.brief_title": {"en": "Brief", "pt": "Missão"},
    "mission.your_code": {"en": "Your code", "pt": "Seu código"},
    "mission.tab_results": {"en": "Results", "pt": "Resultados"},
    "mission.tab_hints": {"en": "Hints", "pt": "Dicas"},
    "mission.tab_output": {"en": "Output", "pt": "Saída"},
    "mission.worked_example": {"en": "Worked example", "pt": "Exemplo resolvido"},
    "mission.key_points": {"en": "Key points", "pt": "Pontos-chave"},
    "mission.subtitle": {"en": "{title}  -  {xp} XP", "pt": "{title}  -  {xp} XP"},
    "mission.running": {"en": "running...", "pt": "rodando..."},
    "mission.case_progress": {"en": "case {done} of {total}", "pt": "caso {done} de {total}"},
    "mission.unlocked": {"en": "Unlocked: {islands}", "pt": "Desbloqueado: {islands}"},
    "mission.level_up": {"en": "Level {level}!", "pt": "Nível {level}!"},
    "mission.congrats": {"en": "Solved!", "pt": "Resolvido!"},
    "mission.next_hint": {"en": "F6 for the next mission", "pt": "F6 para a próxima missão"},
    "mission.reduced_notice": {
        "en": "  Narrow terminal: teaching and brief are in the tabs. Widen to see all panels.",
        "pt": "  Terminal estreito: lição e missão estão nas abas. Alargue para ver todos os "
        "painéis.",
    },
    "mission.reset_confirm": {
        "en": "Reset the editor to the original stub?\n\n"
        "[$parchment-dim]Everything you have typed is discarded.[/$parchment-dim]",
        "pt": "Reiniciar o editor para o esqueleto original?\n\n"
        "[$parchment-dim]Tudo o que você digitou será descartado.[/$parchment-dim]",
    },
    "mission.reset_label": {"en": "Reset", "pt": "Reiniciar"},
    # The two questions below say what is *lost*, not what changes. "Go to the next
    # mission?" reads as navigation and gets a reflex yes; the cost has to be in the
    # sentence, because the whole reason the dialog exists is a mistyped key.
    "mission.next_confirm": {
        "en": "Move on to the next mission?\n\n"
        "[$parchment-dim]The code in the editor is not saved anywhere. "
        "Leaving discards it.[/$parchment-dim]",
        "pt": "Avançar para a próxima missão?\n\n"
        "[$parchment-dim]O código do editor não está salvo em lugar nenhum. "
        "Sair descarta ele.[/$parchment-dim]",
    },
    "mission.next_label": {"en": "Move on", "pt": "Avançar"},
    "mission.leave_confirm": {
        "en": "Go back to the island map?\n\n"
        "[$parchment-dim]The code in the editor is not saved anywhere. "
        "Leaving discards it.[/$parchment-dim]",
        "pt": "Voltar para o mapa da ilha?\n\n"
        "[$parchment-dim]O código do editor não está salvo em lugar nenhum. "
        "Sair descarta ele.[/$parchment-dim]",
    },
    "mission.leave_label": {"en": "Leave", "pt": "Sair"},
    "output.empty": {"en": "No output", "pt": "Sem saída"},
    "output.not_executed": {"en": "Not executed", "pt": "Não executado"},
    # -------------------------------------------------------------- dialogs.py
    "dialog.cancel": {"en": "Cancel", "pt": "Cancelar"},
    "dialog.delete": {"en": "Delete", "pt": "Apagar"},
    # ---------------------------------------------------------------- settings.py
    "settings.title": {"en": "Settings", "pt": "Configurações"},
    "settings.back": {"en": "Back", "pt": "Voltar"},
    "settings.tagline": {
        "en": "Configured in .env - copy .env.example to start",
        "pt": "Configurado em .env - copie .env.example para começar",
    },
    "settings.language_label": {"en": "Language", "pt": "Idioma"},
    "settings.language_toggle": {"en": "Language", "pt": "Idioma"},
    "settings.language_name.en": {"en": "English", "pt": "Inglês"},
    "settings.language_name.pt": {"en": "Portuguese (BR)", "pt": "Português (BR)"},
    "settings.language_hint": {
        "en": "L toggles the game's language.",
        "pt": "L alterna o idioma do jogo.",
    },
    "settings.mentor": {"en": "Mentor", "pt": "Mentor"},
    "settings.mentor_enabled": {"en": "enabled", "pt": "ativado"},
    "settings.mentor_host": {"en": "host", "pt": "endereço"},
    "settings.mentor_model": {"en": "model", "pt": "modelo"},
    "settings.mentor_timeout": {"en": "timeout", "pt": "tempo limite"},
    "settings.sandbox": {"en": "Sandbox", "pt": "Sandbox"},
    "settings.sandbox_timeout": {"en": "default timeout", "pt": "tempo limite padrão"},
    "settings.sandbox_memory": {"en": "default memory", "pt": "memória padrão"},
    "settings.paths": {"en": "Paths", "pt": "Caminhos"},
    "settings.paths_content": {"en": "content", "pt": "conteúdo"},
    "settings.paths_saves": {"en": "saves", "pt": "saves"},
    "settings.footer_note": {
        "en": "The game is fully playable with the mentor off. It teaches from the "
        "hand-written content, not from a model.",
        "pt": "O jogo é totalmente jogável com o mentor desligado. Ele ensina a partir do "
        "conteúdo escrito à mão, não de um modelo.",
    },
    # ------------------------------------------------------------ mentor_chat.py
    "mentor.title": {"en": "Mentor", "pt": "Mentor"},
    "mentor.input_placeholder": {"en": "ask the mentor...", "pt": "pergunte ao mentor..."},
    "mentor.greeting": {
        "en": "[$parchment-dim]Ask a question. I will not hand you the answer - "
        "that is what the hint panel is for.[/$parchment-dim]",
        "pt": "[$parchment-dim]Faça uma pergunta. Eu não vou te dar a resposta pronta - "
        "é para isso que existe o painel de dicas.[/$parchment-dim]",
    },
    "mentor.you_label": {"en": "you", "pt": "você"},
    "mentor.mentor_label": {"en": "mentor", "pt": "mentor"},
    "mentor.thinking": {"en": "thinking...", "pt": "pensando..."},
    "mentor.redacted": {
        "en": "(answer withheld by the anti-spoiler rule)",
        "pt": "(resposta retida pela regra anti-spoiler)",
    },
    # -------------------------------------------------------- widgets/test_results.py
    "results.press_f5": {
        "en": "Press F5 to run your code.",
        "pt": "Aperte F5 para rodar seu código.",
    },
    "results.running_case": {
        "en": "Running case {done} of {total}...",
        "pt": "Rodando caso {done} de {total}...",
    },
    "results.passed": {"en": "PASSED", "pt": "PASSOU"},
    "results.failed": {"en": "FAILED", "pt": "FALHOU"},
    "results.reason": {"en": "reason: {reason}", "pt": "motivo: {reason}"},
    "results.visible": {"en": "visible", "pt": "visível"},
    "results.hidden": {"en": "hidden", "pt": "oculto"},
    "results.case": {"en": "case {n} ({kind})", "pt": "caso {n} ({kind})"},
    "results.xp_gained": {"en": "+{xp} XP", "pt": "+{xp} XP"},
    "results.already_completed": {
        "en": "Already completed, no XP this time.",
        "pt": "Já concluída, sem XP desta vez.",
    },
    # ---------------------------------------------------------- widgets/hint_panel.py
    "hints.rung_1": {
        "en": "a question pointing at the missing idea",
        "pt": "uma pergunta que aponta para a ideia que falta",
    },
    "hints.rung_2": {
        "en": "the name of the construct you need",
        "pt": "o nome da construção que você precisa",
    },
    "hints.rung_3": {
        "en": "the pattern as code, on a different problem",
        "pt": "o padrão em código, aplicado a um problema diferente",
    },
    "hints.rung_other": {"en": "another nudge", "pt": "mais um empurrão"},
    "hints.hint_n": {"en": "Hint {n}", "pt": "Dica {n}"},
    "hints.locked_hint": {
        "en": "Hint {n} - locked: {label}",
        "pt": "Dica {n} - trancada: {label}",
    },
    "hints.none_revealed": {
        "en": "F1 reveals the next hint. Each one costs XP.",
        "pt": "F1 revela a próxima dica. Cada uma custa XP.",
    },
    "hints.exhausted": {
        "en": "No hints left. Assembling it is still your job.",
        "pt": "Sem dicas restantes. Montar a solução ainda é com você.",
    },
}


def get_language() -> Language:
    """The language currently active for UI chrome."""
    return _current_language


def set_language(language: Language) -> None:
    """Switch the active language. Unknown codes are refused, not silently ignored.

    A typo here is a programming error (every caller passes a constant or a value read
    back from the same ``LANGUAGES`` tuple), not player input, so it earns a loud
    failure rather than a quiet fallback to English.
    """
    if language not in LANGUAGES:
        raise ValueError(f"unknown language {language!r}, expected one of {LANGUAGES}")
    global _current_language
    _current_language = language


def t(key: str, **kwargs: object) -> str:
    """Look up ``key`` in the active language and format it with ``kwargs``.

    Falls back to English when a key has no Portuguese entry yet, and to the key
    itself when the key is missing entirely - visible-but-ugly in the rare case a
    translation is forgotten, rather than a crash that takes the whole screen down
    over one missing label.
    """
    entry = _STRINGS.get(key)
    if entry is None:
        return key
    text = entry.get(_current_language) or entry.get(DEFAULT_LANGUAGE) or key
    return text.format(**kwargs) if kwargs else text
