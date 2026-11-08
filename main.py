"""MemeFit - Dress the Brief

Run this file with Python 3:
    python main.py

This project uses only Python's standard library.
"""

from __future__ import annotations

import json
import random
import textwrap
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
WARDROBE_FILE = DATA_DIR / "wardrobe.json"
PLAYER_FILE = BASE_DIR / "player_data.json"
STUDIO_FILE = DATA_DIR / "studio.json"
LEGACY_SCENES = [
    "9:00 AM Panic", "Corporate But Make It You", "Rain Has Entered the Chat",
    "Birthday Plot Twist", "Quiet Luxury, Loud Budget", "2016 Has Logged Back In",
    "Airport Celebrity (Economy Class)", "Comment Section Court",
]


# ---------- Terminal styling ----------
class Colour:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    CYAN = "\033[96m"
    MAGENTA = "\033[95m"
    YELLOW = "\033[93m"
    GREEN = "\033[92m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    DIM = "\033[2m"


def paint(text: str, colour: str) -> str:
    return f"{colour}{text}{Colour.RESET}"


def clear_line():
    print("-" * 72)


def header(title: str):
    print("\n" + paint("=" * 72, Colour.MAGENTA))
    print(paint(f"  {title}", Colour.BOLD + Colour.CYAN))
    print(paint("=" * 72, Colour.MAGENTA))


def wrapped(text: str, width: int = 68):
    print(textwrap.fill(text, width=width))


# ---------- Domain models ----------
@dataclass
class ClothingItem:
    item_id: str
    name: str
    category: str
    colour: str
    price: int
    formality: int
    warmth: int
    comfort: int
    chaos: int
    tags: List[str]
    emoji: str

    @classmethod
    def from_dict(cls, data: dict) -> "ClothingItem":
        return cls(**data)


@dataclass
class Challenge:
    name: str
    occasion: str
    weather: str
    budget: int
    formality_target: int
    warmth_target: int
    required_tags: List[str]
    forbidden_tags: List[str]
    twist: str
    twist_description: str
    challenge_id: str = ""
    description: str = ""
    weather_label: str = ""
    emoji: str = "✦"
    objectives: Optional[List[dict]] = None
    fun_policy: str = "balanced"
    chaos_penalty: int = 0
    chaos_bonus: int = 0
    mission_rule: str = ""
    success_line: str = ""
    failure_line: str = ""


@dataclass
class Outfit:
    selected_ids: List[str]

    def total_price(self, items: Sequence[ClothingItem]) -> int:
        by_id = {item.item_id: item for item in items}
        return sum(by_id[item_id].price for item_id in self.selected_ids)

    def categories(self, items: Sequence[ClothingItem]) -> List[str]:
        by_id = {item.item_id: item for item in items}
        return [by_id[item_id].category for item_id in self.selected_ids]


@dataclass
class PlayerProfile:
    name: str = "Fashion Icon"
    total_plays: int = 0
    best_score: int = 0
    best_style: int = 0
    best_chaos: int = 0
    completed_challenges: List[str] = None
    unlocked_ids: List[str] = None
    history: List[dict] = None
    coins: int = 60
    earned_coins: int = 0
    shop_unlocked: bool = False
    rewarded_outfits: List[str] = None
    scene_stars: Dict[str, int] = None
    lookbook: List[dict] = None

    def __post_init__(self):
        if self.completed_challenges is None:
            self.completed_challenges = []
        if self.unlocked_ids is None:
            self.unlocked_ids = []
        if self.history is None:
            self.history = []
        if self.rewarded_outfits is None:
            self.rewarded_outfits = []
        if self.scene_stars is None:
            self.scene_stars = {}
        if self.lookbook is None:
            self.lookbook = []

    @classmethod
    def from_dict(cls, data: dict) -> "PlayerProfile":
        data = dict(data)
        aliases = {name: f"scene_{index}" for index, name in enumerate(LEGACY_SCENES)}
        data["completed_challenges"] = list(dict.fromkeys(
            aliases.get(name, name) for name in data.get("completed_challenges", []) or []
        ))
        return cls(**data)


# ---------- Data loading and saving ----------
def default_wardrobe() -> List[ClothingItem]:
    """Fallback wardrobe so the game still works if the data file is missing."""
    raw_items = [
        {"item_id": "top_white_shirt", "name": "Crisp White Shirt", "category": "top", "colour": "white", "price": 35, "formality": 5, "warmth": 1, "comfort": 4, "chaos": 0, "tags": ["formal", "classic", "office"], "emoji": "👔"},
        {"item_id": "top_pink_sweater", "name": "Pink Cloud Sweater", "category": "top", "colour": "pink", "price": 28, "formality": 2, "warmth": 4, "comfort": 5, "chaos": 1, "tags": ["cute", "cosy"], "emoji": "🩷"},
        {"item_id": "top_graphic_tee", "name": "Dramatic Graphic Tee", "category": "top", "colour": "black", "price": 22, "formality": 1, "warmth": 1, "comfort": 5, "chaos": 3, "tags": ["street", "casual", "meme"], "emoji": "👕"},
        {"item_id": "top_retro_jersey", "name": "Retro Football Jersey", "category": "top", "colour": "blue", "price": 30, "formality": 1, "warmth": 2, "comfort": 4, "chaos": 2, "tags": ["retro", "street", "2016"], "emoji": "🏀"},
        {"item_id": "bottom_black_trousers", "name": "Black Tailored Trousers", "category": "bottom", "colour": "black", "price": 50, "formality": 5, "warmth": 2, "comfort": 3, "chaos": 0, "tags": ["formal", "classic", "office"], "emoji": "👖"},
        {"item_id": "bottom_jeans", "name": "Wide-Leg Jeans", "category": "bottom", "colour": "blue", "price": 45, "formality": 2, "warmth": 2, "comfort": 4, "chaos": 1, "tags": ["casual", "street"], "emoji": "👖"},
        {"item_id": "bottom_pajamas", "name": "Definitely-Not-Pyjamas Trousers", "category": "bottom", "colour": "purple", "price": 18, "formality": 0, "warmth": 3, "comfort": 5, "chaos": 5, "tags": ["meme", "cosy", "chaos"], "emoji": "🛌"},
        {"item_id": "bottom_sequin_skirt", "name": "Emergency Sequin Skirt", "category": "bottom", "colour": "silver", "price": 42, "formality": 4, "warmth": 1, "comfort": 2, "chaos": 3, "tags": ["party", "glam", "chaos"], "emoji": "✨"},
        {"item_id": "outer_blazer", "name": "Main Character Blazer", "category": "outer", "colour": "black", "price": 70, "formality": 5, "warmth": 3, "comfort": 3, "chaos": 1, "tags": ["formal", "office", "classic"], "emoji": "🧥"},
        {"item_id": "outer_raincoat", "name": "Bright Yellow Raincoat", "category": "outer", "colour": "yellow", "price": 45, "formality": 1, "warmth": 5, "comfort": 4, "chaos": 2, "tags": ["rain", "outdoor", "meme"], "emoji": "🌧️"},
        {"item_id": "outer_denim", "name": "Oversized Denim Jacket", "category": "outer", "colour": "blue", "price": 55, "formality": 2, "warmth": 3, "comfort": 4, "chaos": 1, "tags": ["street", "casual", "retro"], "emoji": "🧢"},
        {"item_id": "shoes_black", "name": "Reliable Black Loafers", "category": "shoes", "colour": "black", "price": 60, "formality": 5, "warmth": 1, "comfort": 3, "chaos": 0, "tags": ["formal", "office", "classic"], "emoji": "👞"},
        {"item_id": "shoes_sneakers", "name": "Chunky White Sneakers", "category": "shoes", "colour": "white", "price": 65, "formality": 2, "warmth": 1, "comfort": 5, "chaos": 1, "tags": ["street", "casual", "comfort"], "emoji": "👟"},
        {"item_id": "shoes_rainboots", "name": "Canary Yellow Rain Boots", "category": "shoes", "colour": "yellow", "price": 48, "formality": 1, "warmth": 4, "comfort": 3, "chaos": 4, "tags": ["rain", "meme", "wrong-shoe"], "emoji": "🥾"},
        {"item_id": "shoes_bunny", "name": "Pink Bunny Slippers", "category": "shoes", "colour": "pink", "price": 16, "formality": 0, "warmth": 3, "comfort": 5, "chaos": 5, "tags": ["meme", "cosy", "wrong-shoe"], "emoji": "🐰"},
        {"item_id": "accessory_tote", "name": "Overprepared Tote Bag", "category": "accessory", "colour": "cream", "price": 20, "formality": 1, "warmth": 0, "comfort": 4, "chaos": 1, "tags": ["campus", "practical"], "emoji": "👜"},
        {"item_id": "accessory_sunglasses", "name": "Tiny Celebrity Sunglasses", "category": "accessory", "colour": "black", "price": 25, "formality": 2, "warmth": 0, "comfort": 2, "chaos": 2, "tags": ["glam", "retro", "meme"], "emoji": "🕶️"},
        {"item_id": "accessory_bow", "name": "Massive Bow of Consequences", "category": "accessory", "colour": "pink", "price": 12, "formality": 1, "warmth": 0, "comfort": 2, "chaos": 5, "tags": ["cute", "meme", "chaos"], "emoji": "🎀"},
        {"item_id": "accessory_duck_hat", "name": "Duck Hat With Confidence", "category": "accessory", "colour": "yellow", "price": 14, "formality": 0, "warmth": 2, "comfort": 3, "chaos": 5, "tags": ["meme", "chaos", "cute"], "emoji": "🦆"},
        {"item_id": "accessory_flower_crocs", "name": "Flower Charm Shoe Clips", "category": "accessory", "colour": "multi", "price": 10, "formality": 0, "warmth": 0, "comfort": 4, "chaos": 4, "tags": ["meme", "wrong-shoe", "chaos"], "emoji": "🌼"},
    ]
    return [ClothingItem.from_dict(item) for item in raw_items]


def load_wardrobe() -> List[ClothingItem]:
    try:
        with WARDROBE_FILE.open("r", encoding="utf-8") as file:
            return [ClothingItem.from_dict(item) for item in json.load(file)]
    except (FileNotFoundError, json.JSONDecodeError, TypeError, KeyError):
        items = default_wardrobe()
        DATA_DIR.mkdir(exist_ok=True)
        with WARDROBE_FILE.open("w", encoding="utf-8") as file:
            json.dump([asdict(item) for item in items], file, indent=2)
        return items


def load_profile() -> PlayerProfile:
    try:
        with PLAYER_FILE.open("r", encoding="utf-8") as file:
            return PlayerProfile.from_dict(json.load(file))
    except (FileNotFoundError, json.JSONDecodeError, TypeError):
        return PlayerProfile()


def save_profile(profile: PlayerProfile):
    with PLAYER_FILE.open("w", encoding="utf-8") as file:
        json.dump(asdict(profile), file, indent=2)


# ---------- Challenges ----------
def challenge_pool() -> List[Challenge]:
    """Load the same named briefs, rules and objectives used by the browser."""
    with STUDIO_FILE.open("r", encoding="utf-8") as file:
        return [Challenge(**details) for details in json.load(file)["challenges"]]


def choose_challenge() -> Challenge:
    return random.choice(challenge_pool())


# ---------- Game logic ----------
def item_lookup(items: Sequence[ClothingItem]) -> Dict[str, ClothingItem]:
    return {item.item_id: item for item in items}


def display_item(item: ClothingItem, number: Optional[int] = None):
    prefix = f"{number}. " if number is not None else ""
    print(f"{prefix}{item.emoji} {item.name} | {item.category} | {item.colour} | ${item.price} | chaos {item.chaos}/5")


def choose_item_for_category(items: Sequence[ClothingItem], category: str, selected: List[str]) -> Optional[str]:
    choices = [item for item in items if item.category == category]
    if not choices:
        return None
    print(paint(f"\nChoose your {category}:", Colour.YELLOW))
    for index, item in enumerate(choices, start=1):
        display_item(item, index)
    print("0. Skip this category")
    while True:
        answer = input("Your choice: ").strip()
        try:
            choice = int(answer)
        except ValueError:
            print(paint("Please enter a number.", Colour.RED))
            continue
        if choice == 0:
            return None
        if 1 <= choice <= len(choices):
            chosen = choices[choice - 1]
            if chosen.item_id in selected:
                print(paint("You already selected that item.", Colour.RED))
                continue
            return chosen.item_id
        print(paint("That option is not available.", Colour.RED))


def choose_outfit(items: Sequence[ClothingItem], challenge: Challenge) -> Outfit:
    header("Build Your Outfit")
    print(paint(f"Brief: {challenge.name}", Colour.CYAN))
    wrapped(challenge.twist_description)
    print()
    selected: List[str] = []
    for category in ["top", "bottom", "outer", "shoes", "accessory"]:
        chosen_id = choose_item_for_category(items, category, selected)
        if chosen_id:
            selected.append(chosen_id)
    if not selected:
        print(paint("You selected nothing. Bold. Very conceptual.", Colour.MAGENTA))
    return Outfit(selected)


def random_outfit(items: Sequence[ClothingItem]) -> Outfit:
    selected = []
    for category in ["top", "bottom", "outer", "shoes", "accessory"]:
        choices = [item for item in items if item.category == category]
        if choices and random.random() > 0.15:
            selected.append(random.choice(choices).item_id)
    return Outfit(selected)


def selected_items(outfit: Outfit, items: Sequence[ClothingItem]) -> List[ClothingItem]:
    by_id = item_lookup(items)
    return [by_id[item_id] for item_id in outfit.selected_ids if item_id in by_id]


def calculate_scores(outfit: Outfit, items: Sequence[ClothingItem], challenge: Challenge) -> Tuple[int, int, List[str]]:
    chosen = selected_items(outfit, items)
    feedback: List[str] = []
    if not chosen:
        return 5, 10, ["There is no outfit yet. Your confidence is doing all the work."]

    total_price = sum(item.price for item in chosen)
    average_formality = sum(item.formality for item in chosen) / len(chosen)
    average_comfort = sum(item.comfort for item in chosen) / len(chosen)
    average_warmth = sum(item.warmth for item in chosen) / len(chosen)
    chaos = sum(item.chaos for item in chosen)
    tags = {tag for item in chosen for tag in item.tags}
    colours = {item.colour for item in chosen if item.colour != "multi"}

    occasion_score = max(0, 25 - abs(average_formality - challenge.formality_target) * 6)
    weather_score = max(0, 20 - abs(average_warmth - challenge.warmth_target) * 5)
    comfort_score = min(15, average_comfort * 3)
    budget_score = 15 if total_price <= challenge.budget else max(0, 15 - (total_price - challenge.budget) // 10)
    colour_score = 15 if len(colours) <= 3 else 9
    category_score = 10 if "top" in outfit.categories(items) and "bottom" in outfit.categories(items) and "shoes" in outfit.categories(items) else 4
    style_score = int(min(100, occasion_score + weather_score + comfort_score + budget_score + colour_score + category_score))

    chaos_score = min(100, 25 + chaos * 8)
    if challenge.twist in {"chaos", "wrong-shoe", "comments"}:
        chaos_score = min(100, chaos_score + 15)
    if challenge.twist == "budget" and total_price <= challenge.budget:
        chaos_score += 5

    missing_tags = [tag for tag in challenge.required_tags if tag not in tags]
    if missing_tags:
        style_score = max(0, style_score - 12 * len(missing_tags))
        feedback.append(f"The brief wanted {', '.join(missing_tags)}, but your wardrobe said 'maybe later'.")
    else:
        feedback.append("You understood the brief. The algorithm is cautiously impressed.")

    if total_price > challenge.budget:
        feedback.append(f"Budget alert: you spent ${total_price}, which is ${total_price - challenge.budget} over budget.")
    else:
        feedback.append(f"Budget handled: ${total_price} used out of ${challenge.budget}.")

    if "rain" in tags and "heavy rain" in challenge.weather:
        feedback.append("Rain protection detected. Your socks may live another day.")
    if average_formality > challenge.formality_target + 1:
        feedback.append("You may be overdressed, but at least the entrance will be dramatic.")
    if chaos >= 12:
        feedback.append("Chaos level: magnificent. Someone will ask for the link.")
    elif chaos <= 3:
        feedback.append("Chaos level: calm. The outfit has read the instructions carefully.")

    if challenge.twist == "wrong-shoe":
        if any("wrong-shoe" in item.tags for item in chosen):
            chaos_score = min(100, chaos_score + 12)
            feedback.append("Wrong-shoe bonus unlocked: confusing, but somehow intentional.")
        else:
            feedback.append("The brief asked for a surprise item. The surprise has not arrived.")
    elif challenge.twist == "retro":
        if "retro" in tags or "2016" in tags:
            style_score = min(100, style_score + 8)
            feedback.append("Nostalgia bonus: your outfit has returned from the archives.")
    elif challenge.twist == "starter-pack":
        if "campus" in tags or "comfort" in tags:
            chaos_score = min(100, chaos_score + 8)
            feedback.append("Starter-pack energy detected. You look ready for a montage.")
    elif challenge.twist == "comments":
        feedback.append([
            "Comment section: 'I hate that this works.'",
            "Comment section: 40% confused, 60% taking notes.",
            "Comment section: 'Please explain the shoes.'",
        ][chaos % 3])

    return max(0, style_score), max(0, min(100, chaos_score)), feedback


def verdict(style_score: int, chaos_score: int) -> str:
    total = int(style_score * 0.6 + chaos_score * 0.4)
    if total >= 90:
        return "FASHION ICON: the outfit has its own publicist."
    if total >= 75:
        return "SURPRISINGLY GOOD: suspiciously stylish and mildly unforgettable."
    if total >= 60:
        return "INTERESTING CHOICE: the outfit has a point, but it refuses to explain it."
    if total >= 40:
        return "BRAVE BUT CONCERNING: confidence is currently doing unpaid overtime."
    return "THE OUTFIT HAS LEFT THE CHAT. Please consult a mirror."


def show_outfit(outfit: Outfit, items: Sequence[ClothingItem]):
    chosen = selected_items(outfit, items)
    if not chosen:
        print(paint("(No items selected)", Colour.DIM))
        return
    for item in chosen:
        display_item(item)


def play_round(items: List[ClothingItem], profile: PlayerProfile):
    challenge = choose_challenge()
    header("New MemeFit Challenge")
    print(paint(f"🎯 {challenge.name}", Colour.YELLOW))
    print(f"Occasion: {challenge.occasion}")
    print(f"Weather: {challenge.weather}")
    print(f"Budget: ${challenge.budget}")
    print(f"Special rule: {challenge.twist_description}")
    clear_line()
    print("1. Build my outfit")
    print("2. Let the algorithm style me")
    mode = input("Choose mode: ").strip()
    outfit = random_outfit(items) if mode == "2" else choose_outfit(items, challenge)

    header("Your Final Look")
    show_outfit(outfit, items)
    style_score, chaos_score, feedback = calculate_scores(outfit, items, challenge)
    total_score = int(style_score * 0.6 + chaos_score * 0.4)
    print()
    print(paint(f"Style Score: {style_score}/100", Colour.BLUE))
    print(paint(f"Chaos Score: {chaos_score}/100", Colour.MAGENTA))
    print(paint(f"Final Score: {total_score}/100", Colour.GREEN if total_score >= 70 else Colour.YELLOW))
    print(paint(verdict(style_score, chaos_score), Colour.BOLD + Colour.CYAN))
    print()
    for line in feedback:
        print(f"• {line}")

    profile.total_plays += 1
    profile.best_score = max(profile.best_score, total_score)
    profile.best_style = max(profile.best_style, style_score)
    profile.best_chaos = max(profile.best_chaos, chaos_score)
    if challenge.challenge_id not in profile.completed_challenges:
        profile.completed_challenges.append(challenge.challenge_id)
    profile.history.append({
        "challenge": challenge.name,
        "style_score": style_score,
        "chaos_score": chaos_score,
        "final_score": total_score,
        "items": outfit.selected_ids,
    })
    profile.history = profile.history[-10:]
    save_profile(profile)
    print(paint("\nProgress saved to player_data.json.", Colour.DIM))
    input("Press Enter to return to the menu...")


def view_wardrobe(items: Sequence[ClothingItem]):
    header("Virtual Wardrobe")
    for category in ["top", "bottom", "outer", "shoes", "accessory"]:
        print(paint(f"\n{category.upper()}", Colour.YELLOW))
        for item in [item for item in items if item.category == category]:
            display_item(item)
    input("\nPress Enter to return to the menu...")


def view_profile(profile: PlayerProfile):
    header("Player Profile")
    print(f"Name: {profile.name}")
    print(f"Challenges played: {profile.total_plays}")
    print(f"Best final score: {profile.best_score}/100")
    print(f"Best style score: {profile.best_style}/100")
    print(f"Best chaos score: {profile.best_chaos}/100")
    print(f"Unique briefs completed: {len(profile.completed_challenges)}")
    if profile.history:
        print(paint("\nRecent looks:", Colour.YELLOW))
        for result in reversed(profile.history[-5:]):
            print(f"• {result['challenge']}: {result['final_score']}/100")
    input("\nPress Enter to return to the menu...")


def reset_profile(profile: PlayerProfile):
    answer = input("Reset all saved scores? Type RESET to confirm: ").strip()
    if answer == "RESET":
        profile.total_plays = 0
        profile.best_score = 0
        profile.best_style = 0
        profile.best_chaos = 0
        profile.completed_challenges = []
        profile.history = []
        save_profile(profile)
        print(paint("Profile reset. A new fashion era begins.", Colour.GREEN))
    else:
        print("No changes made.")
    input("Press Enter to return to the menu...")


def print_intro():
    print(paint(r"""
 __  __                 _____ _ _   
|  \/  | ___ _ __ ___  |  ___(_) |_ 
| |\/| |/ _ \ '_ ` _ \ | |_  | | __|
| |  | |  __/ | | | | ||  _| | | |_ 
|_|  |_|\___|_| |_| |_||_|   |_|\__|

        D R E S S   T H E   B R I E F
""", Colour.MAGENTA))
    wrapped("A gender-inclusive outfit challenge game where good taste, bad ideas and suspiciously confident accessories compete for the highest score.")


def main():
    items = load_wardrobe()
    profile = load_profile()
    print_intro()
    name = input(f"Enter your player name [{profile.name}]: ").strip()
    if name:
        profile.name = name
        save_profile(profile)

    while True:
        header("Main Menu")
        print("1. Start a new challenge")
        print("2. View wardrobe")
        print("3. View profile and high scores")
        print("4. Reset saved progress")
        print("5. Quit")
        choice = input("Choose an option: ").strip()
        if choice == "1":
            play_round(items, profile)
        elif choice == "2":
            view_wardrobe(items)
        elif choice == "3":
            view_profile(profile)
        elif choice == "4":
            reset_profile(profile)
        elif choice == "5":
            print(paint("Goodbye. May your outfit be intentional.", Colour.CYAN))
            break
        else:
            print(paint("That menu option is not serving a look. Try again.", Colour.RED))


if __name__ == "__main__":
    try:
        import sys

        if "--terminal" in sys.argv:
            main()
        else:
            import studio

            studio.main()
    except KeyboardInterrupt:
        print("\n" + paint("Game closed. The outfit remains mysterious.", Colour.YELLOW))
