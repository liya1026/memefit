# Release checks — 30 October 2026

Release protocol: **sunny-audio-4**. Tests use temporary profiles rather than
the player's working save. These results document development checks, not a
guarantee of a particular assessment mark or compatibility with every computer.

## Automated regression checks rerun for this package

| Area | Result | Main coverage |
| --- | --- | --- |
| Two-round challenge | 3,677 assertions passed | 100 seeded suitcases; ordinary passing alternatives; everyday first round and playful second round; both costumes work in each possible finale. |
| Timer | 41 checks passed | Shared deadline, boundary actions, expired rounds and saved submissions. |
| Premium shop | 162 checks passed | Unlock threshold, permanent access, purchases, ownership, bonus maths, old-save migration and rejected transactions. |
| Scene scoring | 38,580 assertions passed | Passing combinations, negative scores for inappropriate looks, coin rules and no reward on failure. |
| Bilingual interface | 424 assertions passed | Translation behaviour and soundtrack controls. |
| Audio and funny finales | 69 assertions passed | Separate Pig/Roach captions, local-only music, continuity during results/replays, stopping audio, imports and hero animation rig. |

All three frontend JavaScript files passed Node syntax checks. Python sources
are compiled during final package verification without writing cache files
into the distributed folder.

## Distribution checks

The code archive is checked after extraction into a temporary path containing
spaces. An actual local HTTP server serves the browser assets and completes
both challenge rounds through the API. The check also confirms that the ZIP
contains every runtime file, retains executable launcher permissions and
contains neither a personal player profile nor Python cache files. The
packaged Python and browser/data files are compared with the canonical game.
Only the English documentation is rewritten for the submission copy.

The Padlet description contains 100 words by whitespace count. The English
poster is rendered at 1600 × 1200 and visually inspected. English documents
are checked for accidentally retained Chinese drafts. Chinese game strings
remain deliberately available through the language switch. A Python comment
scan found no Chinese comments in the five modules.

## Browser checks already completed on the same release

The current release was checked in Chromium with temporary profiles: Pig Hero
and Roach showed their distinct result text and spinning characters; the local
theme could be stopped; no iframe, video element or remote script remained.
No console errors were reported in that check. The compact desktop submission
bar, premium entrance and motion-off behaviour were also inspected during
development. These checks do not imply a fresh test on every operating system.

## Known limits

- Windows and every browser/voice combination have not been tested directly.
- Speech quality depends on installed system voices and is optional.
- Browsers may require a click before audio playback. Core play does not
  depend on sound, speech or online services.
- Commercial songs are not included. Browser-local imports do not travel
  with the code ZIP; the original instrumental is the fallback.
- An old Python server must be stopped before starting the new copy.
- Keep the complete folder together. Missing browser or scene files are not
  all automatically repaired by the save/wardrobe fallbacks.
- Ed/Canvas upload acceptance, Padlet posting, the live presentation and
  course policy approval are outside these software tests.
