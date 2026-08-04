"""Entry point for ``python -m codequest`` and for the ``codequest`` console script.

Through Phase 2 this is a command line harness over the engine: it can run a mission,
list the catalogue, manage saves and play a mission into a save file. The Textual UI
arrives in Phase 4 and will call the same services, not reimplement them.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from codequest import __version__
from codequest.config import get_settings
from codequest.models.verdict import FailureReason, Verdict
from codequest.services.game_session import GameSession
from codequest.services.mission_service import MissionService
from codequest.services.progress_service import (
    DuplicateProfileNameError,
    ProfileLimitReachedError,
    ProgressService,
)
from codequest.storage.db import init_db

_SYMBOL = {True: "PASS", False: "FAIL"}


def _print_verdict(verdict: Verdict) -> None:
    """Render a Verdict for a terminal, hidden cases included but never disclosed."""
    print(f"\n{_SYMBOL[verdict.passed]}  {verdict.summary}")

    for outcome in verdict.outcomes:
        kind = "visible" if outcome.visible else "hidden "
        mark = "ok  " if outcome.passed else "FAIL"
        line = f"  [{mark}] case {outcome.index + 1} ({kind})"
        if outcome.detail and not outcome.passed:
            line += f" - {outcome.detail}"
        print(line)

    if verdict.stdout:
        print("\n  your output:")
        for line in verdict.stdout.rstrip().splitlines():
            print(f"    {line}")

    if verdict.reason is not FailureReason.PASSED and not verdict.outcomes:
        print(f"\n  reason: {verdict.reason.value}")


def cmd_run(args: argparse.Namespace) -> int:
    """Run a solution file against a mission file. No save, no persistence."""
    from codequest.engine.loader import load_mission

    mission = load_mission(args.mission)
    code = Path(args.solution).read_text(encoding="utf-8")

    print(f"{mission.title}  ({mission.id}, {mission.difficulty.value}, {mission.xp} XP)")
    outcome = GameSession().attempt(mission, code)
    _print_verdict(outcome.verdict)

    return 0 if outcome.passed else 1


def cmd_check(args: argparse.Namespace) -> int:
    """Run every mission's own declared solution against its own tests."""
    service = MissionService(args.content or get_settings().content_dir, args.track)
    session = GameSession()

    failures = 0
    for mission in service.missions:
        outcome = session.check_solution(mission)
        status = _SYMBOL[outcome.passed]
        print(f"[{status}] {mission.id}  {mission.title}")
        if not outcome.passed:
            failures += 1
            print(f"        {outcome.verdict.summary}")

    print(f"\n{len(service.missions) - failures}/{len(service.missions)} missions self-consistent")
    return 1 if failures else 0


def cmd_missions(args: argparse.Namespace) -> int:
    """List the catalogue of a track."""
    service = MissionService(args.content or get_settings().content_dir, args.track)

    for island in service.islands:
        print(f"\n{island.order}. {island.name}  [{island.id}]")
        for mission in service.missions_in(island.id):
            print(f"   {mission.order}. {mission.title:<28} {mission.id:<20} {mission.xp:>3} XP")

    print(f"\n{len(service.missions)} missions, {service.total_xp_available()} XP available")
    return 0


def _open_service(args: argparse.Namespace) -> ProgressService:
    settings = get_settings()
    return ProgressService(init_db(args.db or settings.database_path))


def cmd_saves(args: argparse.Namespace) -> int:
    """List career saves."""
    service = _open_service(args)
    profiles = service.list_profiles()

    if not profiles:
        print("No saves yet. Create one with: codequest new-save <name>")
        return 0

    for profile in profiles:
        completed = service.progress.completed_count(profile.id)
        print(
            f"  #{profile.id}  {profile.name:<16} {profile.track:<10} "
            f"level {profile.level}  {profile.total_xp:>5} XP  {completed} missions"
        )
    return 0


def cmd_new_save(args: argparse.Namespace) -> int:
    """Create a career save."""
    service = _open_service(args)
    try:
        profile = service.create_profile(args.name, args.track)
    except (ProfileLimitReachedError, DuplicateProfileNameError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(f"Created save #{profile.id} '{profile.name}' on the {profile.track} track.")
    return 0


def cmd_play(args: argparse.Namespace) -> int:
    """Attempt a mission as a saved profile, persisting the result."""
    settings = get_settings()
    progress = _open_service(args)
    missions = MissionService(args.content or settings.content_dir, args.track)

    profile = progress.profiles.get_by_name(args.save)
    if profile is None:
        print(f"No save called '{args.save}'. Try: codequest saves", file=sys.stderr)
        return 1

    mission = missions.get_mission(args.mission)
    if mission is None:
        print(f"No mission with id '{args.mission}'. Try: codequest missions", file=sys.stderr)
        return 1

    code = Path(args.solution).read_text(encoding="utf-8")
    session = GameSession(progress=progress)
    outcome = session.attempt(mission, code, profile, missions.islands)

    print(f"{mission.title}  ({mission.id})")
    _print_verdict(outcome.verdict)

    if outcome.award:
        award = outcome.award
        if award.xp_awarded:
            print(f"\n  +{award.xp_awarded} XP   total {award.profile.total_xp}")
        elif award.already_completed and outcome.passed:
            print(f"\n  Already completed, no XP this time. Total {award.profile.total_xp}")
        if award.leveled_up:
            print(f"  Level up! You are now level {award.profile.level}.")
        for island_id in award.newly_unlocked:
            print(f"  Unlocked island: {island_id}")

    return 0 if outcome.passed else 1


def cmd_ui(args: argparse.Namespace) -> int:
    """Launch the terminal interface. The normal way to play.

    The import is local so ``codequest check`` in CI never loads Textual, and so a
    headless machine can still run the whole content suite.
    """
    from codequest.tui.app import run

    run(database=args.db, track=args.track)
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Build the command line parser.

    Split out from ``main`` so a test can inspect the interface without running it.
    """
    parser = argparse.ArgumentParser(prog="codequest", description="CodeQuest")
    parser.add_argument("--version", action="version", version=f"codequest {__version__}")
    subcommands = parser.add_subparsers(dest="command")

    def add_content_options(sub: argparse.ArgumentParser) -> None:
        sub.add_argument("--track", default="python", help="track id (default: python)")
        sub.add_argument("--content", default=None, help="content directory override")

    ui = subcommands.add_parser("ui", help="launch the game (the normal way to play)")
    ui.add_argument("--track", default="python")
    ui.add_argument("--db", default=None, help="database path override")
    ui.set_defaults(func=cmd_ui)

    run = subcommands.add_parser("run", help="run a solution file against a mission file")
    run.add_argument("mission", help="path to a mission YAML file")
    run.add_argument("solution", help="path to a Python file with your solution")
    run.set_defaults(func=cmd_run)

    check = subcommands.add_parser("check", help="verify every mission's own solution passes")
    add_content_options(check)
    check.set_defaults(func=cmd_check)

    missions = subcommands.add_parser("missions", help="list the catalogue")
    add_content_options(missions)
    missions.set_defaults(func=cmd_missions)

    saves = subcommands.add_parser("saves", help="list career saves")
    saves.add_argument("--db", default=None, help="database path override")
    saves.set_defaults(func=cmd_saves)

    new_save = subcommands.add_parser("new-save", help="create a career save")
    new_save.add_argument("name")
    new_save.add_argument("--track", default="python")
    new_save.add_argument("--db", default=None, help="database path override")
    new_save.set_defaults(func=cmd_new_save)

    play = subcommands.add_parser("play", help="attempt a mission as a saved profile")
    play.add_argument("save", help="name of the career save")
    play.add_argument("mission", help="mission id")
    play.add_argument("solution", help="path to a Python file with your solution")
    add_content_options(play)
    play.add_argument("--db", default=None, help="database path override")
    play.set_defaults(func=cmd_play)

    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the CodeQuest command line entry point.

    Args:
        argv: Command line arguments **without** the program name. When ``None``,
            ``sys.argv[1:]`` is used. Taking this as a parameter is what makes the
            function testable without touching the real process arguments.

    Returns:
        The process exit code. ``0`` means success; any non-zero value means failure.
        A failing mission returns 1, which is what lets CI run ``codequest check``.
    """
    if argv is None:
        argv = sys.argv[1:]

    if not argv:
        print(f"codequest {__version__}")
        return 0

    parser = build_parser()
    args = parser.parse_args(argv)

    if not hasattr(args, "func"):
        parser.print_help()
        return 1

    try:
        return args.func(args)
    except FileNotFoundError as exc:
        print(f"File not found: {exc.filename}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
