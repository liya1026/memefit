"""Pure scoring, cumulative star objectives and explainable local judges."""

import main as game
import fashion
import cup


def objective_progress(chosen, challenge, scores):
    """All stars must be earned together in one complete outfit, in order."""
    tags = {tag for item in chosen for tag in item.tags}
    complete = {"top", "bottom", "shoes"}.issubset(item.category for item in chosen)
    goals = [{"label": "Wear a top, bottoms and shoes.", "met": complete}]
    previous = complete
    for objective in challenge.objectives or []:
        rules = objective["rules"]
        checks = []
        for key, field in (("fit_min", "style"), ("beauty_min", "beauty"), ("fun_min", "chaos")):
            if key in rules:
                checks.append(scores[field] >= rules[key])
        if rules.get("tags_any"):
            checks.append(bool(tags.intersection(rules["tags_any"])))
        for tag, minimum in rules.get("tag_counts", {}).items():
            checks.append(sum(tag in item.tags for item in chosen) >= minimum)
        if rules.get("within_budget"):
            checks.append(scores["price"] <= challenge.budget)
        if rules.get("playful"):
            checks.append(any(item.chaos >= 4 for item in chosen))
        if "max_playful" in rules:
            checks.append(sum(item.chaos >= 4 for item in chosen) <= rules["max_playful"])
        previous = previous and all(checks)
        goals.append({"label": objective["label"], "met": previous})
    stars = sum(goal["met"] for goal in goals)
    return {"stars": stars, "goals": goals, "title": (
        "Triple Threat" if stars == 3 else "Brief Nailed" if stars == 2
        else "Base Clear" if stars == 1 else "Getting Dressed"
    )}


def score_look(chosen, challenge, costume=None, event=None):
    """The server and the one-piece suggestion simulator share this scorer."""
    outfit = game.Outfit([item.item_id for item in chosen])
    fit, _, feedback = game.calculate_scores(outfit, chosen, challenge)
    beauty, fun, breakdown = fashion.visual_scores(chosen, costume)
    categories = {item.category for item in chosen}
    missing = [category for category in ("top", "bottom", "shoes") if category not in categories]
    if missing:
        fit = min(fit, 35)
    base_total = int(fit * 0.35 + beauty * 0.4 + fun * 0.25)
    playful = sum(item.chaos >= 4 for item in chosen)
    adjustment = -min(160, playful * challenge.chaos_penalty)
    if not missing:
        adjustment += min(18, playful * challenge.chaos_bonus)
    event_bonus = cup.event_points(chosen, event)
    premium_points = fashion.premium_bonus(chosen)
    total = max(-100, min(100, base_total + adjustment + event_bonus + premium_points))
    result = {
        "style": fit, "beauty": beauty, "chaos": fun, "total": total,
        "beauty_breakdown": breakdown, "price": sum(item.price for item in chosen),
        "budget": challenge.budget, "feedback": feedback, "missing": missing,
        "locked_costume": costume,
        "verdict": "Main character, confirmed." if total >= 80 else
        "Hard to explain. Harder to forget." if total >= 60 else "Great idea. Room for a remix.",
    }
    result["progress"] = objective_progress(chosen, challenge, result)
    passed = not missing and total >= 60
    result["mission"] = {
        "passed": passed, "base_total": base_total, "adjustment": adjustment,
        "event_bonus": event_bonus,
        "premium_bonus": premium_points,
        "premium_count": sum(item.item_id in fashion.SHOP for item in chosen),
        "playful_count": playful, "rule": challenge.mission_rule,
        "fun_bonus_allowed": challenge.fun_policy in {"balanced", "playful"},
        "reaction": challenge.success_line if passed else challenge.failure_line,
    }
    if total < 0:
        result["verdict"] = "Wrong outfit. Very memorable consequences."
    result["entrance_title"] = "Best Entrance · Fun 100" if costume else ""
    return result


def judge_cards(chosen, challenge, result, available, event=None):
    """Use real attributes and one-item simulations, not an online AI service."""
    accents = {item.colour for item in chosen} - {"black", "white", "cream", "silver", "brown"}
    stylist = {
        "name": "The Stylist", "quote": "The outfit has a group chat. Is everyone replying?",
        "reason": f"Style {result['beauty']}: {len(accents)} accent colour(s). "
                  + "; ".join(f"{label}: {points:+}" for label, points in result["beauty_breakdown"].items()) + ".",
        "tip": "Layers and accessories add detail; a shared style tag adds coherence. Style judges clothes, never bodies.",
    }
    next_goal = next((goal["label"] for goal in result["progress"]["goals"] if not goal["met"]), None)
    reviewer = {
        "name": "The Brief Checker",
        "quote": "You won the entrance. Not necessarily the interview." if result["locked_costume"]
                 else "An excellent entrance still needs to read the invitation.",
        "reason": f"Fit {result['style']}. Outfit value {result['price']} / {challenge.budget}; "
                  + ("over the scene limit, not a coin charge." if result["price"] > challenge.budget else "within the scene limit; no wearing fee."),
        "tip": challenge.mission_rule + " " + (f"Next star: {next_goal}" if next_goal else "All three goals met in this outfit. Star progress is recorded on submission."),
    }
    if result["locked_costume"]:
        tip = "Start a new round for a different outfit. Fun 100 does not waive the brief, value limit or star rules."
    else:
        baseline = (result["mission"]["passed"], result["progress"]["stars"], result["total"])
        best = baseline
        suggestion = None
        identifiers = {item.item_id for item in chosen}
        for candidate in available:
            if candidate.item_id in identifiers or any(tag.startswith("costume:") for tag in candidate.tags):
                continue
            replacement = [item for item in chosen if item.category != candidate.category] + [candidate]
            simulated = score_look(replacement, challenge, event=event)
            rank = (simulated["mission"]["passed"], simulated["progress"]["stars"], simulated["total"])
            if rank > best:
                best = rank
                suggestion = (candidate, simulated)
        if suggestion:
            candidate, simulated = suggestion
            tip = (f"Try {candidate.name}: one-piece simulation gives Style {result['beauty']} → {simulated['beauty']}, "
                   f"Fit {result['style']} → {simulated['style']}, Fun {result['chaos']} → {simulated['chaos']}; "
                   f"{simulated['progress']['stars']}/3 stars. Already owned; no purchase needed.")
        else:
            tip = "No better single-piece swap found among owned clothes. Try changing two pieces together or a new scene."
    playful = [item.name for item in chosen if item.chaos >= 4]
    audience = {
        "name": "The Comment Section",
        "quote": "This outfit needs its own emergency contact." if playful else "Suspiciously normal. We are watching the shoes.",
        "reason": f"Fun {result['chaos']}. " + ("Playful pieces: " + ", ".join(playful) + "." if playful else "No high-chaos piece equipped yet."),
        "tip": tip,
    }
    return [stylist, reviewer, audience]
