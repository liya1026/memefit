# How MemeFit works

The assessed game starts with `studio.py`. Python runs a local HTTP
server and owns the wardrobe, scoring, timing and persistent progress.
HTML, CSS, JavaScript and SVG provide the interactive visual interface.
The browser is the display and input layer, not the authority for coins.

## Advanced topic 1: file input and output

- `main.load_wardrobe()` reads `data/wardrobe.json` and constructs
  `ClothingItem` objects. `main.challenge_pool()` reads the scene data
  from `data/studio.json`.
- `studio.StudioServer.__init__()` reads a saved player profile using
  JSON and reconstructs `PlayerProfile` from the data.
- `studio.StudioServer.save_profile()` serialises the updated profile
  to a temporary file and replaces the old save after a successful
  write. Coins, owned items and Lookbook entries survive a restart.

This is used for real game content and progress, not a disconnected
example. No player save is distributed with the submission.

## Advanced topic 2: exception handling

- The studio profile loader catches `OSError`, `ValueError` and
  `TypeError` and keeps a default profile when a save cannot be read.
- The wardrobe loader handles missing or malformed wardrobe input and
  writes a default wardrobe. This fallback is not a promise that every
  damaged supporting file can be repaired automatically.
- `StudioHandler.do_POST()` catches invalid game actions and returns an
  error response for the interface to display.
- A failed save raises a descriptive error before the in-memory profile
  is replaced, so the affected transaction is not silently applied.

File I/O and error handling are both examples named in the supplied
rubric. This explanation does not assume that any JavaScript animation
counts as an advanced Python topic.

## Structure and problem solving

- `main.py`: dataclasses and core outfit calculations.
- `fashion.py`: Style/Fun calculation, shop rules and coin receipts.
- `progression.py`: scene-aware score, optional stars and judges.
- `cup.py`: a shared suitcase, two-round order and announced events.
- `studio.py`: input validation, sessions, purchases and persistence.

`cup.deal()` looks for ordinary passing combinations for each selected
brief, then packs alternatives into the twelve-piece suitcase. The
second scene is drawn from the playful scenes. The two costume sets
remain available separately. There is no single prescribed outfit and
no score gate between rounds.

`progression.score_look()` combines Fit (35%), Style (40%) and Fun (25%),
then applies the scene adjustment, announced event and premium bonus.
Total scores are clamped to -100 through 100. A complete look with a
total of 60 passes for rewards, but any complete submitted look can
advance the challenge. Full Fun does not cancel scene penalties.

`time.monotonic()` supports the server-side 120-second deadline. Both
rounds, result screens and dancing share that clock. Submission IDs
and recorded outfit keys prevent repeat payouts. Browser speech uses
local system voices; judge comments are rule-based, not live AI output.

## Runtime boundary

Python uses only the standard library. The server binds to localhost.
Core play and the bundled instrumental work offline. Optional browser
audio imports and system speech are not required for scoring or saves.
The release uses protocol `sunny-audio-4`; stop the old Python process
before running an updated copy to avoid mixed interface/server versions.
