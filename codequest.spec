# PyInstaller spec for the portable build (Fase 5.2 - "pendrive"). Build with:
#
#     pyinstaller codequest.spec
#
# Produces dist/CodeQuest/CodeQuest.exe plus a support folder - copy the whole
# dist/CodeQuest/ directory, that is the unit that runs standalone. --onedir on
# purpose, not --onefile: --onefile re-extracts to a fresh temp folder on every
# launch, which would silently reset saves each time the game opens on a different
# machine. --onedir is the stable folder this game's portability actually needs.
#
# Never run PyInstaller against --onefile for this project without re-reading the
# reasoning above - it is a one-line flag change that quietly breaks persistence.

from PyInstaller.utils.hooks import collect_submodules

datas = [
    ("src/codequest/tui/styles.tcss", "codequest/tui"),
    ("content/tracks", "content/tracks"),
]

# The mentor package is imported lazily, behind a feature flag (see
# src/codequest/tui/widgets/mentor_chat.py) - PyInstaller's static import analysis
# never sees those imports, so they must be declared by hand or the packaged build
# would crash the moment CODEQUEST_MENTOR_ENABLED=1 is set on the destination machine.
#
# tree_sitter_python is the same problem from a different direction: Textual loads
# syntax highlighting with `importlib.import_module(f"tree_sitter_{language_name}")`
# (textual/_tree_sitter.py) - a dynamically built module name PyInstaller's static
# analyzer cannot follow. CodeQuest only ever asks for language="python"
# (tui/widgets/code_editor.py), so only that one grammar needs declaring; the other
# tree-sitter-* packages textual[syntax] installs stay unbundled on purpose.
#
# textual itself does the same trick one level further in: textual/widgets/__init__.py
# resolves e.g. TabPane through a module-level __getattr__ that imports
# "textual.widgets._tab_pane" by name on first access, not by a top-level import
# statement PyInstaller's analyzer can see. Confirmed the hard way: the mission screen
# (which uses TabbedContent/TabPane) crashed the packaged build with
# "ModuleNotFoundError: No module named 'textual.widgets._tab_pane'" until every
# textual submodule was pulled in explicitly - trying to hand-pick just the widgets
# CodeQuest happens to use is exactly the kind of list that silently rots the next
# time a screen adds a new one.
hidden_imports = [
    "codequest.mentor.client",
    "codequest.mentor.prompts",
    "codequest.mentor.policy",
    "tree_sitter_python",
]
hidden_imports += collect_submodules("textual")

a = Analysis(
    ["src/codequest/__main__.py"],
    pathex=["src"],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="CodeQuest",
    console=True,  # a Textual TUI needs a real console, not the windowed subsystem
    debug=False,
    strip=False,
    upx=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="CodeQuest",
)
