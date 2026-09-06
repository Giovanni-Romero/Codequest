"""Island map with progressive unlocking.

A locked island shows **what it needs**, never just a padlock. "Locked" tells a player
they cannot go there; "finish 1 mission on Foundations" tells them what to do next, and
those are different products.
"""

from __future__ import annotations

from typing import ClassVar

from textual.app import ComposeResult
from textual.binding import BindingType
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Footer, Header, Label, ListItem, ListView, Static

from codequest.models.curriculum import Island
from codequest.models.mission import Mission
from codequest.models.profile import MissionStatus
from codequest.tui.screens.mission import MissionScreen
from codequest.tui.strings import t
from codequest.tui.symbols import (
    ISLAND,
    ISLAND_CURRENT,
    LOCKED,
    STATUS_CLASS,
    STATUS_SYMBOL,
    progress_bar,
)


class IslandMapScreen(Screen):
    """Islands and their missions, with what is open and what is not."""

    BINDINGS: ClassVar[list[BindingType]] = [
        ("escape", "app.pop_screen", "Saves"),
        ("r", "reload", "Refresh"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="island-list", classes="panel"):
            yield Static("", id="map-heading", classes="panel-title")
            yield ListView(id="entries")
        yield Footer()

    async def on_screen_resume(self) -> None:
        """Refresh whenever this screen becomes active - first push or a later resume.

        Textual posts ``ScreenResume`` both the first time a screen is pushed and every
        time it becomes the top screen again, so this one hook covers both cases and
        there is no separate ``on_mount``. That matters here specifically: popping back
        from ``MissionScreen`` does not remount this screen, and without a resume hook
        the map kept showing whatever it looked like *before* the player solved
        anything.
        """
        await self.action_reload()

    async def action_reload(self) -> None:
        """Rebuild from storage, so XP earned in a mission shows on the way back."""
        self.app.refresh_profile()
        await self._rebuild()

    # ------------------------------------------------------------------ rendering

    async def _rebuild(self) -> None:
        context = self.app.context
        profile = self.app.profile
        listing = self.query_one("#entries", ListView)
        # clear() only schedules the removal; awaiting it is what guarantees the old
        # rows are actually gone before the loop below appends new ones with the same
        # widget IDs. Skipping the await let a second reload collide with the first.
        await listing.clear()

        if profile is None:
            return

        completed_total = context.progress.progress.completed_count(profile.id)
        all_missions = len(context.missions.missions)
        self.query_one("#map-heading", Static).update(
            t(
                "island_map.heading",
                name=profile.name,
                level=profile.level,
                xp=profile.total_xp,
                done=completed_total,
                total=all_missions,
            )
        )

        statuses = context.progress.progress_for(profile)

        for island in context.missions.islands:
            unlocked = context.progress.is_island_unlocked(profile, island)
            missions = context.missions.missions_in(island.id)
            done = sum(
                1
                for mission in missions
                if mission.id in statuses and statuses[mission.id].is_completed
            )

            listing.append(ListItem(Label(self._island_line(island, missions, done, unlocked))))

            if not unlocked:
                listing.append(
                    ListItem(Label(f"      [$becalmed]{self._requirement(island)}[/$becalmed]"))
                )
                continue

            for mission in missions:
                status = (
                    statuses[mission.id].status
                    if mission.id in statuses
                    else MissionStatus.AVAILABLE
                )
                # The class carries the state; the check glyph in the line carries it a
                # second time. Styling the whole row from CSS rather than wrapping the
                # line in markup is what lets the selection highlight override it - inline
                # markup would win over the stylesheet and the highlight would vanish
                # exactly on the rows the player has already finished.
                listing.append(
                    ListItem(
                        Label(self._mission_line(mission, status, statuses)),
                        id=f"mission-{mission.id}",
                        classes="completed" if status is MissionStatus.COMPLETED else "",
                    )
                )

        # Land on the first row so Enter has something to open. A rebuilt ListView has
        # no highlight, and a list that refuses to respond looks broken rather than empty.
        if listing.children:
            listing.index = 0
            listing.focus()

    def _island_line(
        self, island: Island, missions: tuple[Mission, ...], done: int, unlocked: bool
    ) -> str:
        mark = ISLAND_CURRENT if unlocked and done < len(missions) else ISLAND
        if not unlocked:
            mark = LOCKED
        bar = progress_bar(done, len(missions))
        style = "accent" if unlocked else "locked"
        return (
            f"[{style}]{mark} {island.order}. {island.name:<18}[/{style}] "
            f"[$brass]{bar}[/$brass] {done}/{len(missions)}"
        )

    def _mission_line(self, mission: Mission, status: MissionStatus, statuses) -> str:
        symbol = STATUS_SYMBOL[status]
        style = STATUS_CLASS[status]
        record = statuses.get(mission.id)

        suffix = ""
        if record is not None and record.is_completed:
            suffix = f"[$parchment-dim]{record.best_xp} XP[/$parchment-dim]"
            if record.hints_used:
                hints = t("island_map.hints_used", n=record.hints_used)
                suffix += f" [$becalmed]({hints})[/$becalmed]"
        else:
            suffix = f"[$parchment-dim]{mission.xp} XP[/$parchment-dim]"

        return f"    [{style}]{symbol}[/{style}] {mission.order}. {mission.title:<30} {suffix}"

    def _requirement(self, island: Island) -> str:
        """Say what the island needs, in words a player can act on."""
        rule = island.unlock_requires
        parts: list[str] = []
        if rule.missions_completed:
            parts.append(t("island_map.requirement_missions", n=rule.missions_completed))
        if rule.total_xp:
            parts.append(t("island_map.requirement_xp", n=rule.total_xp))
        if rule.requires_island:
            parts.append(t("island_map.requirement_island", island=rule.requires_island))
        if rule.requires_mission:
            parts.append(t("island_map.requirement_mission", mission=rule.requires_mission))
        locked = t("island_map.locked_prefix")
        return f"{locked} - " + ", ".join(parts) if parts else locked

    # ------------------------------------------------------------------ actions

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        item_id = event.item.id or ""
        if not item_id.startswith("mission-"):
            return
        mission = self.app.context.missions.get_mission(item_id.removeprefix("mission-"))
        if mission is not None:
            self.app.push_screen(MissionScreen(mission))
