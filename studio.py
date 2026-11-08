"""Local browser studio. Python owns wardrobe data, scoring and saved progress."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import secrets
import threading
import time
import webbrowser
from dataclasses import asdict
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

import main as game
import fashion
import progression
import cup


WEB_DIR = Path(__file__).resolve().parent / "web"
CATEGORIES = ("top", "bottom", "outer", "shoes", "accessory")
SPRINT_SECONDS = 120
API_VERSION = "sunny-audio-4"
COSTUMES = {
    "pig": {"label": "Pig Hero", "colour": "red", "price": 12, "emoji": "🐽"},
    "roach": {"label": "Roach Survivor", "colour": "brown", "price": 8, "emoji": "🪳"},
}


def costume_items():
    """Each costume has five real wardrobe items, linked by a shared tag."""
    return [game.ClothingItem.from_dict({
        "item_id": f"costume_{costume}_{category}",
        "name": f"{details['label']} / {category}", "category": category,
        "colour": details["colour"], "price": details["price"],
        "formality": 0, "warmth": 3, "comfort": 2, "chaos": 5,
        "tags": [f"costume:{costume}", "meme", "chaos", "party"],
        "emoji": details["emoji"],
    }) for costume, details in COSTUMES.items() for category in CATEGORIES]


def selected_costume(chosen):
    """Find a costume tag, rejecting accidental mixtures of two sets."""
    costumes = {tag.split(":", 1)[1] for item in chosen for tag in item.tags
                if tag.startswith("costume:")}
    if len(costumes) > 1:
        raise ValueError("Special suits cannot be mixed. Start a new round.")
    return next(iter(costumes), None)


def outfit_mood(chosen):
    """Pick a performance from the whole outfit, not the player's gender."""
    costume = selected_costume(chosen)
    if costume:
        return costume
    tags = [tag for item in chosen for tag in item.tags]
    funny_items = sum(item.chaos >= 4 for item in chosen)
    if funny_items >= 2 or any(item.item_id == "accessory_duck_hat" for item in chosen):
        return "chaos"
    cute = tags.count("cute") * 2 + tags.count("glam")
    cute += sum(item.colour in {"pink", "silver", "purple"} for item in chosen)
    cool = tags.count("street") + tags.count("formal")
    cool += sum(item.colour == "black" for item in chosen)
    return "cute" if cute > cool else "cool"


class StudioServer(ThreadingHTTPServer):
    """Serve one local game; a token protects writes from unrelated websites."""

    daemon_threads = True

    def __init__(self, address, profile_path=None):
        super().__init__(address, StudioHandler)
        self.token = secrets.token_urlsafe(32)
        self.items = game.load_wardrobe()
        self.items.extend(costume_items())
        self.items.extend(fashion.fashion_items())
        with game.STUDIO_FILE.open("r", encoding="utf-8") as file:
            self.content = json.load(file)
        for item in self.items:
            item.name = self.content["items"][item.item_id]["name"]
        self.challenges = game.challenge_pool()
        self.profile_path = Path(profile_path) if profile_path else game.PLAYER_FILE
        self.profile = game.PlayerProfile()
        try:
            self.profile = game.PlayerProfile.from_dict(
                json.loads(self.profile_path.read_text(encoding="utf-8"))
            )
        except (OSError, ValueError, TypeError):
            pass
        self.lock = threading.RLock()
        self.submissions = {}
        self.rounds = {}
        self.cups = {}

    @property
    def origin(self):
        return f"http://127.0.0.1:{self.server_port}"

    def round_state(self, round_id):
        if not isinstance(round_id, str) or round_id not in self.rounds:
            raise ValueError("This round has expired. Refresh to start again.")
        current = self.rounds[round_id]
        return {"round_id": round_id, **{key: current[key] for key in
                ("selected", "challenge", "locked_costume", "settled")},
                "cup": self.cup_state(current)}

    def cup_state(self, current):
        """Return only public cup state; do not leak the unrevealed event."""
        if not current.get("cup_id"):
            return None
        competition = self.cups[current["cup_id"]]
        receipts = competition["receipts"]
        remaining = max(0, competition["deadline"] - competition.get("finished_at", time.monotonic()))
        round_count = len(competition["scenes"])
        complete = len(receipts) == round_count
        expired = remaining <= 0 and not complete
        return {"scenes": competition["scenes"], "index": current["cup_index"],
                "suitcase": competition["suitcase"][:],
                "exchange_used": competition["exchange_used"],
                "event": competition["events"][current["challenge"]] if current["event_revealed"] else None,
                "receipts": [dict(receipt) for receipt in receipts],
                "total": sum(receipt["total"] for receipt in receipts),
                "round_count": round_count, "complete": complete,
                "duration": SPRINT_SECONDS, "remaining": remaining,
                "expired": expired, "finished": expired or complete,
                "title": cup.title(receipts) if complete else ""}

    def require_time(self, current):
        """Enforce the shared clock on the server, not the browser's display."""
        if current.get("cup_id"):
            competition = self.cups[current["cup_id"]]
            if time.monotonic() >= competition["deadline"]:
                raise ValueError("Time is up! Submitted looks are kept. Start a new sprint or practise without a timer.")

    def allowed(self, current, identifier):
        if not current.get("cup_id"):
            return self.owned(identifier)
        return (identifier in self.cups[current["cup_id"]]["suitcase"] or identifier in fashion.SHOP
                    or identifier.startswith("costume_")) and self.owned(identifier)

    def cup_round(self, competition):
        index = len(competition["receipts"])
        round_id = secrets.token_urlsafe(24)
        lookup = game.item_lookup(self.items)
        self.rounds[round_id] = {
            "selected": [random.choice([identifier for identifier in competition["suitcase"]
                                         if lookup[identifier].category == category])
                         for category in ("top", "bottom", "shoes")],
            "challenge": competition["scenes"][index], "locked_costume": None,
            "settled": False, "cup_id": competition["id"], "cup_index": index,
            "event_revealed": True,
        }
        competition["round_id"] = round_id
        return self.round_state(round_id)

    def cup_action(self, payload):
        round_id = payload.get("round_id")
        self.round_state(round_id)
        current = self.rounds[round_id]
        if not current.get("cup_id"):
            raise ValueError("Start a two-round cup first.")
        competition = self.cups[current["cup_id"]]
        action = payload.get("action")
        if action == "status":
            return self.round_state(competition["round_id"])
        if len(competition["receipts"]) < len(competition["scenes"]):
            self.require_time(current)
        if action == "next":
            if round_id != competition["round_id"]:
                return self.round_state(competition["round_id"])
            if not current["settled"]:
                raise ValueError("Submit this round before continuing the cup.")
            if len(competition["receipts"]) == len(competition["scenes"]):
                return self.round_state(round_id)
            return self.cup_round(competition)
        if current["settled"] or round_id != competition["round_id"]:
            raise ValueError("This round is settled. Continue the cup.")
        if action == "reveal":
            current["event_revealed"] = True
        elif action == "exchange":
            if current["locked_costume"]:
                raise ValueError("Special suit locked! Continue the cup to change outfits.")
            if competition["exchange_used"]:
                raise ValueError("Your one suitcase exchange has already been used.")
            old, new = payload.get("old"), payload.get("new")
            lookup = game.item_lookup(self.items)
            if (not isinstance(old, str) or not isinstance(new, str)
                    or old not in competition["suitcase"] or new not in lookup
                    or new in competition["suitcase"] or not self.owned(new)
                    or new.startswith("costume_") or new in fashion.SHOP
                    or lookup[old].category != lookup[new].category):
                raise ValueError("Exchange one suitcase piece for an owned piece of the same category.")
            replacement = [new if identifier == old else identifier for identifier in competition["suitcase"]]
            if not all(cup.solvable([lookup[identifier] for identifier in replacement], self.challenges[index])
                       for index in competition["scenes"]):
                raise ValueError("That exchange would make a mission impossible. Your exchange was not used.")
            competition["suitcase"] = replacement
            competition["exchange_used"] = True
            current["selected"] = [identifier for identifier in current["selected"] if identifier != old]
        else:
            raise ValueError("Cup action not found.")
        return self.round_state(round_id)

    def owned(self, identifier):
        return identifier not in fashion.SHOP or identifier in self.profile.unlocked_ids

    def save_profile(self, profile):
        temporary = self.profile_path.with_suffix(".tmp")
        try:
            temporary.write_text(json.dumps(asdict(profile), indent=2), encoding="utf-8")
            temporary.replace(self.profile_path)
        except OSError as error:
            raise ValueError("Could not save. This transaction was not applied; check folder permissions.") from error
        self.profile = profile

    def purchase(self, payload):
        identifier = payload.get("item_id")
        if not isinstance(identifier, str) or identifier not in fashion.SHOP:
            raise ValueError("This item is not in the style shop.")
        if self.owned(identifier):
            return {"profile": asdict(self.profile), "shop_status": fashion.shop_status(self.profile), "already_owned": True}
        if not fashion.shop_status(self.profile)["unlocked"]:
            raise ValueError("Style Shop locked. Reach 100 lifetime coins: starter 60 plus 40 earned. Unlocking is permanent.")
        cost = fashion.SHOP[identifier]
        if self.profile.coins < cost:
            raise ValueError(f"Not enough coins. You need {cost - self.profile.coins} more. Complete a challenge to earn them.")
        profile = game.PlayerProfile.from_dict(asdict(self.profile))
        profile.coins -= cost
        profile.shop_unlocked = True
        profile.unlocked_ids.append(identifier)
        self.save_profile(profile)
        return {"profile": asdict(profile), "shop_status": fashion.shop_status(profile), "already_owned": False}

    def save_look(self, payload):
        """Only a server-settled receipt can become a persistent favourite."""
        current = self.round_state(payload.get("round_id"))
        if not current["settled"]:
            raise ValueError("Submit this look first, then save it to your Lookbook.")
        name = payload.get("name")
        if not isinstance(name, str) or not 1 <= len(name.strip()) <= 48 or any(ord(character) < 32 for character in name):
            raise ValueError("Give your look a name between 1 and 48 characters, without line breaks.")
        character = payload.get("character", "marge")
        if character not in ("marge", "homer"):
            raise ValueError("Choose Marge or Homer.")
        previous = next((look for look in self.profile.lookbook if look["round_id"] == current["round_id"]), None)
        if previous:
            return {"profile": asdict(self.profile), "already_saved": True}
        if len(self.profile.lookbook) >= 12:
            raise ValueError("Your 12-look album is full. Remove a saved look to make space.")
        receipt = self.rounds[current["round_id"]]["result"]
        profile = game.PlayerProfile.from_dict(asdict(self.profile))
        profile.lookbook.append({
            "look_id": secrets.token_urlsafe(16), "name": name.strip(),
            "round_id": current["round_id"], "selected": current["selected"][:],
            "challenge_id": self.challenges[current["challenge"]].challenge_id,
            "character": character, "created_at": datetime.now(timezone.utc).isoformat(),
            "scores": {key: receipt[key] for key in ("beauty", "style", "chaos", "total")},
            "stars": receipt["progress"]["stars"],
        })
        self.save_profile(profile)
        return {"profile": asdict(profile), "already_saved": False}

    def remove_look(self, payload):
        profile = game.PlayerProfile.from_dict(asdict(self.profile))
        profile.lookbook = [look for look in profile.lookbook if look["look_id"] != payload.get("look_id")]
        if len(profile.lookbook) == len(self.profile.lookbook):
            raise ValueError("This saved look was not found.")
        self.save_profile(profile)
        return {"profile": asdict(profile)}

    def restore_look(self, payload):
        current = self.round_state(payload.get("round_id"))
        if current["cup"]:
            raise ValueError("Saved looks are available in free play. Leave the cup to restore one.")
        if current["locked_costume"]:
            raise ValueError("Suit locked! Start a new round before loading a saved look.")
        look = next((look for look in self.profile.lookbook if look["look_id"] == payload.get("look_id")), None)
        if not look:
            raise ValueError("This saved look was not found.")
        challenge_index = next((index for index, challenge in enumerate(self.challenges)
                                if challenge.challenge_id == look["challenge_id"]), None)
        if challenge_index is None:
            raise ValueError("This saved scene is unavailable.")
        self.evaluate({"selected": look["selected"], "challenge": challenge_index})
        new_round = self.start_round({"challenge": challenge_index, "previous_round_id": current["round_id"]})
        updated = self.rounds[new_round["round_id"]]
        updated["selected"] = look["selected"][:]
        updated["locked_costume"] = selected_costume([
            game.item_lookup(self.items)[identifier] for identifier in look["selected"]
        ])
        return {**self.round_state(new_round["round_id"]), "character": look["character"]}

    def start_round(self, payload):
        """Refresh resumes the existing lock; only an explicit new round resets it."""
        round_id = payload.get("round_id")
        if isinstance(round_id, str) and round_id in self.rounds:
            return self.round_state(round_id)
        if payload.get("mode") == "cup":
            available = [item for item in self.items if self.owned(item.item_id)
                         and not item.item_id.startswith("costume_") and item.item_id not in fashion.SHOP]
            scenes, suitcase, events = cup.deal(available, self.challenges)
            identifier = secrets.token_urlsafe(24)
            if len(self.cups) >= 128:
                expired = next(iter(self.cups))
                self.rounds = {key: value for key, value in self.rounds.items() if value.get("cup_id") != expired}
                del self.cups[expired]
            competition = {"id": identifier, "scenes": scenes, "suitcase": suitcase,
                           "events": events, "receipts": [], "exchange_used": False,
                           "deadline": time.monotonic() + SPRINT_SECONDS}
            self.cups[identifier] = competition
            return self.cup_round(competition)
        previous = payload.get("previous_round_id")
        if "challenge" in payload:
            challenge = payload["challenge"]
        else:
            previous_challenge = self.rounds.get(previous, {}).get("challenge") if isinstance(previous, str) else None
            challenge = random.choice([index for index in range(len(self.challenges))
                                       if index != previous_challenge])
        if type(challenge) is not int or not 0 <= challenge < len(self.challenges):
            raise ValueError("Challenge not found.")
        if isinstance(previous, str) and not self.rounds.get(previous, {}).get("cup_id"):
            self.rounds.pop(previous, None)
        if len(self.rounds) >= 512:
            self.rounds.pop(next(iter(self.rounds)))
        round_id = secrets.token_urlsafe(24)
        self.rounds[round_id] = {
            "selected": ["top_racing_knit", "bottom_cargo", "shoes_sneakers", "accessory_sunglasses"],
            "challenge": challenge, "locked_costume": None, "settled": False,
        }
        return self.round_state(round_id)

    def equip(self, payload):
        round_id = payload.get("round_id")
        self.round_state(round_id)
        current = self.rounds[round_id]
        self.require_time(current)
        if current["settled"]:
            raise ValueError("This round is settled. Start a new round to change outfits.")
        if current["locked_costume"]:
            raise ValueError("Special suit locked! No removing, replacing or remixing this round. Start a new round.")
        lookup = game.item_lookup(self.items)
        remove = payload.get("remove_category")
        if remove is not None:
            if remove not in CATEGORIES:
                raise ValueError("Clothing category not found.")
            current["selected"] = [identifier for identifier in current["selected"]
                                   if lookup[identifier].category != remove]
        else:
            identifier = payload.get("item_id")
            if not isinstance(identifier, str) or identifier not in lookup:
                raise ValueError("This item is not in the wardrobe.")
            item = lookup[identifier]
            if not self.owned(identifier):
                raise ValueError("Unlock this item with game coins first.")
            if not self.allowed(current, identifier):
                raise ValueError("That piece is not in your suitcase. Use your one exchange or leave the cup.")
            costume = selected_costume([item])
            if costume:
                if current.get("cup_id") and not current["event_revealed"]:
                    raise ValueError("Reveal the event before locking a special suit.")
                current["selected"] = [f"costume_{costume}_{category}" for category in CATEGORIES]
                current["locked_costume"] = costume
            else:
                current["selected"] = [previous for previous in current["selected"]
                                       if lookup[previous].category != item.category] + [identifier]
        return self.round_state(round_id)

    def remix(self, payload):
        round_id = payload.get("round_id")
        self.round_state(round_id)
        self.require_time(self.rounds[round_id])
        if self.rounds[round_id]["settled"]:
            raise ValueError("Round settled. Start a new round.")
        if self.rounds[round_id]["locked_costume"]:
            raise ValueError("Suit locked. Even a remix cannot save you. Start a new round!")
        self.rounds[round_id]["selected"] = [random.choice([
            item.item_id for item in self.items if item.category == category
            and not any(tag.startswith("costume:") for tag in item.tags)
            and self.allowed(self.rounds[round_id], item.item_id)
        ]) for category in CATEGORIES]
        return self.round_state(round_id)

    def evaluate(self, payload):
        selected = payload.get("selected", [])
        challenge_index = payload.get("challenge", 0)
        if "round_id" in payload:
            current = self.round_state(payload["round_id"])
            if selected != current["selected"] or challenge_index != current["challenge"]:
                raise ValueError("Your outfit is out of sync. Refresh the page; locked suits cannot be edited.")
            if any(not self.allowed(self.rounds[payload["round_id"]], identifier) for identifier in selected):
                raise ValueError("That piece is not in your suitcase. Use your one exchange or leave the cup.")
        if not isinstance(selected, list) or not all(isinstance(item, str) for item in selected):
            raise ValueError("Choose clothes from the wardrobe.")
        if type(challenge_index) is not int or not 0 <= challenge_index < len(self.challenges):
            raise ValueError("Challenge not found. Refresh the page.")
        lookup = game.item_lookup(self.items)
        if any(item_id not in lookup for item_id in selected):
            raise ValueError("This item is not in the wardrobe.")
        if any(not self.owned(item_id) for item_id in selected):
            raise ValueError("Your outfit contains a locked shop item.")
        chosen = [lookup[item_id] for item_id in selected]
        costume = selected_costume(chosen)
        if costume and set(selected) != {f"costume_{costume}_{category}" for category in CATEGORIES}:
            raise ValueError("Special costumes must be worn as a complete suit.")
        categories = [item.category for item in chosen]
        if len(categories) != len(set(categories)):
            raise ValueError("Only one item per category is allowed.")
        challenge = self.challenges[challenge_index]
        event = current["cup"]["event"] if "round_id" in payload and current["cup"] else None
        result = progression.score_look(chosen, challenge, costume, event)
        result["mood"] = outfit_mood(chosen)
        result["judges"] = progression.judge_cards(
            chosen, challenge, result, [item for item in self.items if self.owned(item.item_id)
                and ("round_id" not in payload or self.allowed(self.rounds[payload["round_id"]], item.item_id))], event
        )
        challenge_id = challenge.challenge_id
        first_scene = challenge_id not in self.profile.completed_challenges
        reward_key = hashlib.sha256(json.dumps([challenge_index, sorted(selected)]).encode()).hexdigest()
        repeated = reward_key in self.profile.rewarded_outfits
        rewards = [] if repeated or result["missing"] else fashion.reward_lines(
            result, first_scene, first_scene and len(self.profile.completed_challenges) == len(self.challenges) - 1
        )
        result["reward_estimate"] = sum(line["coins"] for line in rewards)
        result["repeated"] = repeated
        return result

    def submit(self, payload):
        with self.lock:
            result = self.evaluate(payload)
            if result["missing"]:
                raise ValueError("Wear a top, bottoms and shoes before submitting!")
            request_id = payload.get("request_id")
            if not isinstance(request_id, str) or not 1 <= len(request_id) <= 100:
                raise ValueError("Invalid submission ID. Select Submit again.")
            current = self.rounds[payload["round_id"]]
            if current["settled"]:
                return {**current["result"], "profile": asdict(self.profile),
                        "shop_status": fashion.shop_status(self.profile), "already_settled": True}
            self.require_time(current)
            if current.get("cup_id") and not current["event_revealed"]:
                raise ValueError("Reveal the event and adjust your outfit before submitting.")
            fingerprint = (payload["round_id"], payload["challenge"], tuple(sorted(payload["selected"])))
            if request_id in self.submissions:
                previous_fingerprint, previous_result = self.submissions[request_id]
                if fingerprint != previous_fingerprint:
                    raise ValueError("The outfit changed. Please submit again.")
                return previous_result
            profile = game.PlayerProfile.from_dict(asdict(self.profile))
            reward_key = hashlib.sha256(json.dumps([payload["challenge"], sorted(payload["selected"])]).encode()).hexdigest()
            repeated = reward_key in profile.rewarded_outfits
            challenge = self.challenges[payload["challenge"]]
            challenge_name = challenge.challenge_id
            first_scene = challenge_name not in profile.completed_challenges
            all_scenes = first_scene and len(profile.completed_challenges) == len(self.challenges) - 1
            rewards = [] if repeated else fashion.reward_lines(result, first_scene, all_scenes)
            earned = sum(line["coins"] for line in rewards)
            profile.coins += earned
            profile.earned_coins += earned
            profile.shop_unlocked = fashion.shop_status(profile)["unlocked"]
            if not repeated and result["mission"]["passed"]:
                profile.rewarded_outfits.append(reward_key)
            profile.total_plays += 1
            profile.best_score = max(profile.best_score, result["total"])
            profile.best_style = max(profile.best_style, result["style"])
            profile.best_chaos = max(profile.best_chaos, result["chaos"])
            if result["mission"]["passed"] and challenge_name not in profile.completed_challenges:
                profile.completed_challenges.append(challenge_name)
            previous_stars = profile.scene_stars.get(challenge_name, 0)
            profile.scene_stars[challenge_name] = max(previous_stars, result["progress"]["stars"])
            result["progress"]["previous_best"] = previous_stars
            result["progress"]["best"] = profile.scene_stars[challenge_name]
            profile.history.append({
                "challenge": challenge.name, "challenge_id": challenge_name, "style_score": result["style"],
                "chaos_score": result["chaos"], "final_score": result["total"],
                "items": payload["selected"],
                "beauty_score": result["beauty"], "coins": earned, "stars": result["progress"]["stars"],
                "mission_passed": result["mission"]["passed"],
            })
            profile.history = profile.history[-10:]
            self.save_profile(profile)
            if current.get("cup_id"):
                competition = self.cups[current["cup_id"]]
                competition["receipts"].append({"challenge": current["challenge"],
                    "total": result["total"], "passed": result["mission"]["passed"],
                    "stars": result["progress"]["stars"], "coins": earned})
                if len(competition["receipts"]) == len(competition["scenes"]):
                    competition["finished_at"] = time.monotonic()
                result["cup"] = self.cup_state(current)
            result["reward"] = {"coins": earned, "lines": rewards, "repeated": repeated}
            result["profile"] = asdict(profile)
            result["shop_status"] = fashion.shop_status(profile)
            current["settled"] = True
            current["result"] = result
            self.submissions[request_id] = (fingerprint, result)
            if len(self.submissions) > 200:
                del self.submissions[next(iter(self.submissions))]
            return result


class StudioHandler(BaseHTTPRequestHandler):
    """Explicit route allowlist: never expose player files or arbitrary paths."""

    def log_message(self, format_string, *arguments):
        return

    def respond(self, status, content, content_type="application/json; charset=utf-8"):
        if not isinstance(content, bytes):
            content = json.dumps(content, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-MemeFit-Version", API_VERSION)
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' blob: data:; media-src 'self' blob:; connect-src 'self'; frame-src 'none'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(content)

    def valid_host(self):
        return self.headers.get("Host") == f"127.0.0.1:{self.server.server_port}"

    def do_GET(self):
        if not self.valid_host():
            self.respond(403, {"error": "Local access only."})
            return
        route = urlsplit(self.path).path
        if route == "/api/state":
            if self.headers.get("X-MemeFit-Token") != self.server.token:
                self.respond(403, {"error": "Please refresh the game page."})
                return
            with self.server.lock:
                self.respond(200, {
                    "items": [asdict(item) for item in self.server.items],
                    "challenges": [asdict(challenge) for challenge in self.server.challenges],
                    "profile": asdict(self.server.profile), "shop": fashion.SHOP,
                    "api_version": API_VERSION, "round_count": cup.ROUND_COUNT,
                    "shop_status": fashion.shop_status(self.server.profile),
                    "item_copy": self.server.content["items"],
                })
            return
        assets = {
            "/": ("index.html", "text/html; charset=utf-8"),
            "/style.css": ("style.css", "text/css; charset=utf-8"),
            "/cup.css": ("cup.css", "text/css; charset=utf-8"),
            "/playful.wav": ("playful.wav", "audio/wav"),
            "/avatar.js": ("avatar.js", "text/javascript; charset=utf-8"),
            "/app.js": ("app.js", "text/javascript; charset=utf-8"),
            "/i18n.js": ("i18n.js", "text/javascript; charset=utf-8"),
            "/zh.json": ("zh.json", "application/json; charset=utf-8"),
        }
        if route not in assets:
            self.respond(404, {"error": "Not found"})
            return
        filename, mime_type = assets[route]
        content = (WEB_DIR / filename).read_bytes()
        if route == "/":
            content = content.replace(b"__SESSION_TOKEN__", self.server.token.encode())
        self.respond(200, content, mime_type)

    def do_POST(self):
        if not self.valid_host() or self.headers.get("X-MemeFit-Token") != self.server.token:
            self.respond(403, {"error": "Please use the local game page."})
            return
        if self.headers.get("Origin") not in (None, self.server.origin):
            self.respond(403, {"error": "Local access only."})
            return
        payload = {}
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 16384:
                raise ValueError("Request is empty or too large.")
            payload = json.loads(self.rfile.read(length))
            if not isinstance(payload, dict):
                raise ValueError("Invalid request format.")
            route = urlsplit(self.path).path
            with self.server.lock:
                if route == "/api/round":
                    result = self.server.start_round(payload)
                elif route == "/api/cup":
                    result = self.server.cup_action(payload)
                elif route == "/api/equip":
                    result = self.server.equip(payload)
                elif route == "/api/preview":
                    self.server.round_state(payload.get("round_id"))
                    result = self.server.evaluate(payload)
                elif route == "/api/score":
                    self.server.round_state(payload.get("round_id"))
                    result = self.server.submit(payload)
                elif route == "/api/remix":
                    result = self.server.remix(payload)
                elif route == "/api/buy":
                    result = self.server.purchase(payload)
                elif route == "/api/lookbook/save":
                    result = self.server.save_look(payload)
                elif route == "/api/lookbook/remove":
                    result = self.server.remove_look(payload)
                elif route == "/api/lookbook/restore":
                    result = self.server.restore_look(payload)
                else:
                    self.respond(404, {"error": "Not found"})
                    return
            self.respond(200, result)
        except (ValueError, TypeError, KeyError) as error:
            result = {"error": str(error)}
            # Return authoritative expired state even if time ran out between clicks.
            current = self.server.rounds.get(payload.get("round_id")) if isinstance(payload, dict) and isinstance(payload.get("round_id"), str) else None
            if current and current.get("cup_id") and self.server.cup_state(current)["expired"]:
                result.update(code="SPRINT_EXPIRED", round=self.server.round_state(payload["round_id"]))
            self.respond(400, result)


def main():
    parser = argparse.ArgumentParser(description="MemeFit local dress-up studio")
    parser.add_argument("--no-browser", action="store_true", help="Print URL without opening a browser")
    parser.add_argument("--port", type=int, default=0, help="Local port; default chooses a free port")
    parser.add_argument("--lang", choices=("en", "zh"), default="en", help="Interface language")
    arguments = parser.parse_args()
    with StudioServer(("127.0.0.1", arguments.port)) as server:
        address = f"{server.origin}/?lang={arguments.lang}"
        print(f"\nMemeFit studio is running: {address}", flush=True)
        print("Keep this terminal open. Press Control+C to quit.\n", flush=True)
        if not arguments.no_browser:
            webbrowser.open(address)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nStudio closed. See you next time!")


if __name__ == "__main__":
    main()
