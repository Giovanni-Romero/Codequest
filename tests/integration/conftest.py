"""Fixtures and environment guards shared by the integration suite.

## Why this file deletes an environment variable at import time

Textual honours the ``NO_COLOR`` convention, and it does so destructively:
``App.__init__`` runs ``environ.pop("NO_COLOR", None)``, so the *first* app built in a
process consumes the variable and every later app in that same process sees colour. A
developer whose shell exports ``NO_COLOR=1`` therefore gets a snapshot suite where some
images are monochrome and some are not, depending on test order.

The failure is not the problem. The *fix* is: running ``pytest --snapshot-update`` in
such a shell rewrites the stored baselines to colourless images and commits them, which
silently deletes the visual contract in ``docs/art-direction.md``. ``test_main_menu``
exists to prove that unavailable tracks read as unavailable **without relying on colour
alone** — an assertion worth nothing once every colour in the suite is grey.

A fixture cannot fix this. ``monkeypatch.delenv`` restores the variable when the test
ends, handing it straight back to the next app to pop. It has to be removed once, before
any app is constructed, and stay removed. A conftest is imported before the test modules
it serves, which makes this the right place and the earliest one.

Snapshots already pin ``terminal_size`` so the images depend on the code rather than on
the runner's terminal. This is the same rule applied to colour.
"""

from __future__ import annotations

import os

os.environ.pop("NO_COLOR", None)
