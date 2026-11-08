MEMEFIT — TWO MINUTES, TWO LOOKS
LijiaYao | SID 560364910 | COMP9001
Release prepared 30 October 2026 | sunny-audio-4

A local dress-up game with an everyday first round and a funny finale.
Read the scene, put together an outfit and give it a moment on stage.
The interface can be switched between English and Chinese.

WHAT YOU NEED
Python 3.10 or later and a current web browser. No pip packages,
online account or game engine. Extract the whole folder before playing.
The standard-library Python server runs only on your own computer.

OPEN THE GAME
1. Open Terminal (Mac) or PowerShell/Command Prompt (Windows).
2. Type cd followed by a space, then the path to this memefit folder.
   Put the path in quotes if it contains spaces, for example:
     cd "/path/to/memefit"
   On Mac, dragging the extracted folder into Terminal after typing
   cd and a space is another way to enter its path. Press Enter.
3. Run:
     Mac:      python3 studio.py
     Windows:  py studio.py
   If your Windows installation uses python instead of py, use:
     python studio.py
4. The game opens in your browser. If it does not, copy the complete
   http://127.0.0.1:... address printed in the terminal into the browser.
   Keep the terminal open while playing. Press Control+C to stop it.

Mac shortcut: double-click launch.command if your system permits it.
launch_chinese.command opens the Chinese interface. The terminal steps
above are the fallback if double-clicking does not launch Python.
Chinese interface from a terminal: python3 studio.py --lang zh
English: python3 studio.py --lang en (also the default).
The language switch in the game works in either version.

If Python is not found, install Python 3.10+ from python.org, then open
a new terminal. There are no further dependency-installation steps.
Keep main.py, studio.py, fashion.py, progression.py, cup.py, data/ and
web/ together. Use the printed URL, not a hard-coded port from an old
session. To choose a port manually: python3 studio.py --port 8765
Omit --port if that address is already occupied.

THREE RULES
1. Read the brief: the first round is everyday, the second is playful.
2. Wear a top, bottoms and shoes. Layers and accessories are optional.
3. Submit both looks before the shared two-minute timer runs out.
   There is no minimum score to move to round two. Results and dances
   use the same clock. Free Play has no timer.

You share a random suitcase of 12 ordinary pieces across both rounds.
Pig Hero and Roach are always available too. Picking any special-suit
piece asks for confirmation, then equips and locks all five pieces for
that round. The next round unlocks them. Both suits have Fun 100, but a
funny outfit is not suitable for every scene.

SCORES AND COINS (DETAILS ARE OPTIONAL DURING A FIRST GAME)
Fit, Style and Fun are shown separately. Scene rules can add or subtract
points, so a mismatched look can score below zero. A complete look with
a total of at least 60 passes the brief for rewards, but that threshold
is NOT a gate to the next round.

A new passing look earns 10 coins, plus 20 for Style of at least 80 and
20 for Fun of at least 80 where the scene allows the funny bonus.
Repeated submissions and dance replays do not pay out again. Clothes'
displayed outfit values are not automatic wallet charges.

New profiles begin with 60 coins. The shop opens permanently at 100
lifetime coins (the starting 60 plus 40 earned). Spending does not
relock it. Shop pieces cost 70–150 coins; owned pieces can be reused.
Each premium piece adds 4 points to a complete look, up to 20 extra
points. The final score is still capped at 100. Premium looks get a
spotlight entrance. Ordinary looks take a ballet turn; funny suits
bounce and spin. Optional stars and judge comments are extra detail,
not extra rules needed to finish the two-round challenge.

SOUND, MOTION AND SAVING
Pocket Parade, a short original instrumental, is included. Press Play
Theme if the browser waits for a click before playing sound. Stop Theme
stops it. Motion and spoken feedback can be switched off separately;
speech is off by default and uses voices available on your computer.

Optional song imports need audio you have permission to use. They are
stored locally in the browser and are not submitted with this folder.
No commercial recording, sung lyric or online video is bundled. Without
an import, the game uses Pocket Parade. Clear imported files or disable
imported themes if you want the same soundtrack on every character.

player_data.json is created locally when progress is saved. It holds
coins, purchases and saved looks. Back it up before replacing a played
copy. This submission deliberately contains no personal save. Resetting
the profile is unnecessary for normal play or updates. Refreshing alone
cannot update a running Python server: stop and restart it after changes.

FILE GUIDE
studio.py       Browser entry point, local HTTP API and saved progress.
main.py         Shared data models, loaders and core outfit calculations.
fashion.py      Visual scoring, shop and coin reward rules.
progression.py  Scene-aware totals, stars and explainable suggestions.
cup.py          Two-round suitcase selection and event bonuses.
data/           Wardrobe and scene definitions.
web/            Browser interface, layered characters, translations/music.

TECHNICAL_OVERVIEW.md explains the Python concepts. ASSET_CREDITS.md
records character/media references and AI assistance. QA_REPORT.md
describes the checks run on this release. The optional older text-only
practice mode (python3 main.py --terminal) is not the showcase interface.
