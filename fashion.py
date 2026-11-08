"""Capsule shop and transparent, deterministic studio scoring rules."""

import main as game


SHOP_THRESHOLD = 100
PREMIUM_POINTS = 4
PREMIUM_CAP = 20
SHOP = {
    "top_ribbon_cardigan": 90,
    "bottom_pleated_mini": 95,
    "outer_leather": 150,
    "outer_bomber": 130,
    "shoes_maryjanes": 105,
    "shoes_moto": 110,
    "accessory_chrome": 70,
    "accessory_headphones": 75,
}


def shop_status(profile):
    """Lifetime progress never falls when spending; preserve legacy purchases."""
    progress = max(profile.coins, 60 + profile.earned_coins)
    unlocked = (profile.shop_unlocked or progress >= SHOP_THRESHOLD
                or any(identifier in SHOP for identifier in profile.unlocked_ids))
    return {"unlocked": unlocked, "threshold": SHOP_THRESHOLD,
            "progress": min(SHOP_THRESHOLD, progress),
            "remaining": 0 if unlocked else max(0, SHOP_THRESHOLD - progress),
            "bonus_per_piece": PREMIUM_POINTS, "bonus_cap": PREMIUM_CAP}


def premium_bonus(chosen):
    """Only a complete outfit earns premium points; the normal 100 cap remains."""
    if not {"top", "bottom", "shoes"}.issubset(item.category for item in chosen):
        return 0
    return min(PREMIUM_CAP, PREMIUM_POINTS * sum(item.item_id in SHOP for item in chosen))


def fashion_items():
    """Ten illustrated pieces; shop prices differ from fictional outfit values."""
    specifications = [
        ("top_ribbon_cardigan", "Ribbon Knit Cardigan", "top", "cream", 30, 3, 3, 5, 0, ["cute", "classic", "campus"], "🎀"),
        ("top_racing_knit", "Racing Stripe Knit", "top", "black", 32, 2, 2, 5, 1, ["street", "retro", "casual"], "🏁"),
        ("bottom_pleated_mini", "Cherry Pleated Mini", "bottom", "red", 35, 3, 1, 4, 1, ["cute", "classic", "party", "campus"], "🍒"),
        ("bottom_cargo", "Parachute Cargo Pants", "bottom", "brown", 38, 1, 3, 5, 1, ["street", "casual", "practical"], "🪂"),
        ("outer_leather", "Cropped Moto Jacket", "outer", "black", 55, 3, 3, 3, 1, ["street", "glam", "retro"], "🖤"),
        ("outer_bomber", "Sage Varsity Bomber", "outer", "green", 48, 2, 4, 5, 1, ["street", "casual", "campus", "retro"], "🍵"),
        ("shoes_maryjanes", "Platform Mary Janes", "shoes", "black", 42, 4, 1, 4, 0, ["cute", "classic", "glam"], "🩰"),
        ("shoes_moto", "Silver Buckle Moto Boots", "shoes", "black", 45, 3, 4, 4, 1, ["street", "glam", "rain"], "🥾"),
        ("accessory_chrome", "Chrome Oval Shades", "accessory", "silver", 20, 3, 0, 3, 1, ["street", "glam", "retro"], "🕶️"),
        ("accessory_headphones", "Cherry Studio Headphones", "accessory", "red", 18, 1, 1, 5, 2, ["street", "cute", "campus"], "🎧"),
    ]
    keys = ("item_id", "name", "category", "colour", "price", "formality", "warmth", "comfort", "chaos", "tags", "emoji")
    items = [game.ClothingItem.from_dict(dict(zip(keys, values))) for values in specifications]
    for item in items:
        item.tags.append("capsule")
    return items


def visual_scores(chosen, costume=None):
    """Rate the outfit, never a character's body, gender or real-world beauty."""
    categories = {item.category for item in chosen}
    complete = {"top", "bottom", "shoes"}.issubset(categories)
    accents = {item.colour for item in chosen} - {"black", "white", "cream", "silver", "brown"}
    palette = 30 if len(accents) <= 1 else 24 if len(accents) == 2 else 12 if len(accents) == 3 else 4
    families = ("street", "cute", "classic", "glam", "retro", "cosy", "formal")
    coherence = min(20, max((sum(tag in item.tags for item in chosen) for tag in families), default=0) * 5)
    details = (8 if "accessory" in categories else 0) + (7 if "outer" in categories else 0)
    completeness = 35 if complete else 10 * len(categories & {"top", "bottom", "shoes"})
    playful = sum(item.chaos >= 4 for item in chosen)
    beauty = max(0, min(100, completeness + palette + coherence + details - playful * 7))
    if not complete:
        beauty = min(35, beauty)
    meme_count = sum("meme" in item.tags for item in chosen)
    contrast = 15 if playful and any(item.formality >= 4 for item in chosen) else 0
    chaos = min(100, 10 + sum(item.chaos for item in chosen) * 5
                + min(15, max(0, meme_count - 1) * 5) + contrast) if chosen else 0
    if costume:
        chaos = 100
    return beauty, chaos, {
        "Complete outfit": completeness, "Colour coordination": palette,
        "Style coherence": coherence, "Accessories and layers": details, "Playful-item trade-offs": -playful * 7,
    }


def reward_lines(result, first_scene=False, all_scenes=False):
    mission = result.get("mission", {})
    if not mission.get("passed", True):
        return []
    lines = [{"label": "Complete a new look", "coins": 10}]
    if result["chaos"] >= 80 and mission.get("fun_bonus_allowed", True):
        lines.append({"label": "Especially funny · Fun ≥ 80", "coins": 20})
    if result["beauty"] >= 80:
        lines.append({"label": "Especially stylish · Style ≥ 80", "coins": 20})
    return lines
