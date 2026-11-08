"""Small, solvable suitcases and transparent event bonuses for a local cup."""

import itertools
import random


CATEGORIES = ("top", "bottom", "outer", "shoes", "accessory")
ROUND_COUNT = 2
EVENTS = {
    0: [
        {"title": "Your group needs a spokesperson. Nobody makes eye contact.",
         "rule": "Wear a formal piece for +8. Otherwise +0. No hidden penalty.", "tag": "formal"},
    ],
    1: [
        {"title": "Camera on. The client has joined. So has your panic.",
         "rule": "Wear a formal top or layer for +8. Otherwise +0. No hidden penalty.",
         "tag": "formal", "categories": ["top", "outer"]},
    ],
    2: [
        {"title": "The umbrella has resigned. Effective immediately.",
         "rule": "Wear a rain piece for +8. Otherwise +0. No hidden penalty.", "tag": "rain"},
    ],
    3: [
        {"title": "The birthday group chat says PINK. You muted it yesterday.",
         "rule": "Wear something pink for +8. Otherwise +0. No hidden penalty.", "colour": "pink"},
        {"title": "Surprise: you are in charge of the dance floor.",
         "rule": "Wear a party piece for +8. Otherwise +0. No hidden penalty.", "tag": "party"},
    ],
    4: [
        {"title": "Fine dining. Arctic air conditioning. Very small portions.",
         "rule": "Wear an outer layer for +8. Otherwise +0. No hidden penalty.", "category": "outer"},
    ],
    5: [
        {"title": "The group photo needs one more retro main character.",
         "rule": "Wear a retro piece for +8. Otherwise +0. No hidden penalty.", "tag": "retro"},
    ],
    6: [
        {"title": "Gate changed. Eight minutes. Your suitcase believes in you.",
         "rule": "Wear shoes with comfort at least 4 for +8. Otherwise +0. No hidden penalty.",
         "category": "shoes", "comfort": 4},
    ],
    7: [
        {"title": "The host says: please dress like your Wi-Fi just disconnected.",
         "rule": "Wear a high-chaos piece for +8. Otherwise +0. No hidden penalty.", "chaos": 4},
    ],
}


def event_points(chosen, event):
    """An announced event can only help; incomplete outfits never gain a bonus."""
    if not event or not {"top", "bottom", "shoes"}.issubset(item.category for item in chosen):
        return 0
    for item in chosen:
        if (item.category in event.get("categories", CATEGORIES)
                and ("category" not in event or item.category == event["category"])
                and ("tag" not in event or event["tag"] in item.tags)
                and ("colour" not in event or item.colour == event["colour"])
                and item.comfort >= event.get("comfort", 0)
                and item.chaos >= event.get("chaos", 0)):
            return 8
    return 0


def combinations(items):
    """Enumerate complete outfits, allowing the two optional slots to be empty."""
    groups = [[item for item in items if item.category == category]
              + ([None] if category in ("outer", "accessory") else [])
              for category in CATEGORIES]
    for combination in itertools.product(*groups):
        yield [item for item in combination if item]


def solvable(items, challenge):
    """Require alternatives, rather than a single prescribed correct outfit."""
    import progression
    passing = 0
    for chosen in combinations(items):
        if progression.score_look(chosen, challenge)["mission"]["passed"]:
            passing += 1
            if passing >= 3:
                return True
    return False


def deal(items, challenges):
    """Keep a witnessed passing look per scene, then randomise remaining space."""
    import progression
    # One everyday brief and one playful brief make a short, varied two-look show.
    scenes = [random.choice([0, 1, 2, 4, 6]), random.choice([3, 5, 7])]
    # Fixed show order: practical opening, playful finale for either funny suit.
    witnesses = {index: [] for index in scenes}
    for chosen in combinations(items):
        identifiers = frozenset(item.item_id for item in chosen)
        for index in scenes:
            result = progression.score_look(chosen, challenges[index])
            if result["mission"]["passed"]:
                witnesses[index].append((result["progress"]["stars"], result["total"], identifiers))
    packed = set()
    for index in scenes:
        if not witnesses[index]:
            raise ValueError("No solvable suitcase found. Please use free play.")
        random.shuffle(witnesses[index])
        choices = sorted(witnesses[index], key=lambda entry: (len(entry[2] - packed), -entry[0], -entry[1]))
        packed.update(choices[0][2])
    # Two scenes need fewer mandatory pieces; use the spare space to retain
    # alternative passing looks before adding random extras. Optional layers
    # count as distinct outfits, but no event/purchase is needed to pass.
    for index in scenes:
        while sum(entry[2] <= packed for entry in witnesses[index]) < 3:
            alternatives = [entry for entry in witnesses[index]
                            if not entry[2] <= packed and len(entry[2] | packed) <= 12]
            if not alternatives:
                raise ValueError("No solvable suitcase found. Please use free play.")
            best = min(alternatives, key=lambda entry: (len(entry[2] - packed), -entry[0], -entry[1]))
            packed.update(best[2])
    spare = [item.item_id for item in items if item.item_id not in packed]
    packed.update(random.sample(spare, min(12 - len(packed), len(spare))))
    events = {}
    suitcase = [item for item in items if item.item_id in packed]
    for index in scenes:
        useful = [event for event in EVENTS[index]
                  if any(event_points(chosen, event) for chosen in combinations(suitcase))]
        events[index] = random.choice(useful or EVENTS[index])
    return scenes, sorted(packed), events


def title(receipts):
    passed = sum(receipt["passed"] for receipt in receipts)
    total = sum(receipt["total"] for receipt in receipts)
    if passed == ROUND_COUNT and total >= 80 * ROUND_COUNT:
        return "Humanity's official outfit representative"
    if passed == ROUND_COUNT:
        return "Presentable, with a suspiciously dramatic suitcase"
    if passed >= 1:
        return "Rejected by HR. Welcomed by the runway."
    return "Two briefs. One spectacular misunderstanding."
