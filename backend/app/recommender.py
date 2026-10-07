"""Rule-based ingredient recommender driven by data/knowledge_base.json.

    match_i = sum_c p(c) * s_i(c)  +  sum_rules delta_i     (clipped to [0, 1])

p(c): model probability of skin type c; s_i(c): curated suitability of ingredient i for type c;
delta_i: transparent age/sex adjustments listed in `personalization_rules`.
Ingredients whose BPOM status is 'prohibited' are never recommended (regulatory filter).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

STATUS_LABELS = {"permitted": "Permitted", "restricted": "Restricted - limits apply", "prohibited": "Prohibited"}


class Recommender:
    def __init__(self, kb: dict[str, Any]):
        self.kb = kb
        self._validate()

    @classmethod
    def from_file(cls, path: str | Path) -> "Recommender":
        return cls(json.loads(Path(path).read_text(encoding="utf-8")))

    def _validate(self) -> None:
        for skin_type, routine in self.kb["routines"].items():
            if skin_type not in self.kb["skin_types"]:
                raise ValueError(f"Routine for unknown skin type '{skin_type}'")
            for step, ids in routine["steps"].items():
                if step not in self.kb["steps"]:
                    raise ValueError(f"Routine '{skin_type}' uses unknown step '{step}'")
                missing = [i for i in ids if i not in self.kb["ingredients"]]
                if missing:
                    raise ValueError(f"Routine '{skin_type}' references unknown ingredients {missing}")

    @property
    def disclaimer(self) -> str:
        return self.kb["disclaimer"]

    def skin_types(self) -> list[dict]:
        return [{"key": key, **info} for key, info in self.kb["skin_types"].items()]

    def skin_type_info(self, key: str) -> dict:
        return {"key": key, **self.kb["skin_types"][key]}

    def ingredients(self, skin_type: str | None = None) -> list[dict]:
        items = [self._public(iid, ing) for iid, ing in self.kb["ingredients"].items()]
        if skin_type:
            items = [i for i in items if i["suitability"].get(skin_type, 0.0) >= 0.5]
            items.sort(key=lambda i: -i["suitability"][skin_type])
        return items

    @staticmethod
    def _applies(when: dict, age: int | None, sex: str | None) -> bool:
        if "age_lt" in when and (age is None or age >= when["age_lt"]):
            return False
        if "age_gte" in when and (age is None or age < when["age_gte"]):
            return False
        if "sex" in when and sex != when["sex"]:
            return False
        return True

    def _personalise(self, ingredient_id: str, age: int | None, sex: str | None) -> tuple[float, list[str]]:
        delta, notes = 0.0, []
        for rule in self.kb.get("personalization_rules", []):
            if rule["ingredient"] == ingredient_id and self._applies(rule["when"], age, sex):
                delta += float(rule["adjust"])
                if rule.get("note"):
                    notes.append(rule["note"])
        return delta, notes

    def recommend(self, probabilities: dict[str, float], skin_type: str,
                  age: int | None = None, sex: str | None = None) -> dict:
        routine = self.kb["routines"][skin_type]
        steps = []
        for step_key, ingredient_ids in routine["steps"].items():
            ranked = []
            for iid in ingredient_ids:
                ingredient = self.kb["ingredients"][iid]
                if ingredient["regulatory"]["status"] == "prohibited":  # BPOM filter
                    continue
                expected = sum(float(p) * ingredient["suitability"].get(c, 0.0) for c, p in probabilities.items())
                delta, notes = self._personalise(iid, age, sex)
                match = min(1.0, max(0.0, expected + delta))
                ranked.append({**self._public(iid, ingredient), "match": round(match, 4),
                               "match_percent": int(round(match * 100)), "personal_notes": notes})
            ranked.sort(key=lambda r: r["match"], reverse=True)
            step = self.kb["steps"][step_key]
            steps.append({"order": step["order"], "key": step_key, "title": step["title"],
                          "goal": step["goal"], "ingredients": ranked})
        steps.sort(key=lambda s: s["order"])
        avoid = list(routine.get("avoid", [])) + [
            {"name": p["name"], "reason": p["reason"]} for p in self.kb.get("prohibited", [])]
        return {"skin_type": skin_type, "headline": routine["headline"], "summary": routine["summary"],
                "steps": steps, "avoid": avoid, "notes": list(self.kb.get("general_notes", []))}

    @staticmethod
    def _public(iid: str, ing: dict) -> dict:
        reg = ing["regulatory"]
        return {"id": iid, "name": ing["name"], "alias": ing.get("alias"), "inci": ing.get("inci"),
                "function": ing["function"], "benefits": ing.get("benefits", []),
                "how_to_use": ing.get("how_to_use", ""), "caution": ing.get("caution"),
                "evidence": ing.get("evidence", []), "suitability": ing["suitability"],
                "regulatory": {"status": reg["status"], "label": STATUS_LABELS.get(reg["status"], reg["status"]),
                               "note": reg.get("note", ""), "reference": reg.get("reference", ""),
                               "verified": bool(reg.get("verified", False))}}
