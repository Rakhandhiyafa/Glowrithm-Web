"""Unit tests for the rule-based recommender (CD-5: kebenaran rekomendasi dan regulasi)."""
import copy

import pytest

from app.config import Settings
from app.recommender import Recommender

KB = Recommender.from_file(Settings().kb_path)
OILY = {"dry": 0.02, "normal": 0.03, "oily": 0.95}


def first_per_step(rec):
    return {step["key"]: step["ingredients"][0]["id"] for step in rec["steps"]}


def test_routines_follow_cd3_mapping():
    assert first_per_step(KB.recommend(OILY, "oily")) == {
        "cleanse": "salicylic_acid", "treat": "niacinamide", "protect": "sunscreen"}
    dry = KB.recommend({"dry": 0.9, "normal": 0.08, "oily": 0.02}, "dry")
    assert {i["id"] for s in dry["steps"] for i in s["ingredients"]} >= {"ceramide", "hyaluronic_acid", "glycerin"}


def test_steps_are_ordered_cleanse_treat_protect():
    assert [s["key"] for s in KB.recommend(OILY, "oily")["steps"]] == ["cleanse", "treat", "protect"]


def test_match_is_expected_suitability():
    rec = KB.recommend(OILY, "oily")
    bha = rec["steps"][0]["ingredients"][0]
    s = KB.kb["ingredients"]["salicylic_acid"]["suitability"]
    expected = sum(OILY[c] * s[c] for c in OILY)
    assert bha["match"] == pytest.approx(expected, abs=1e-4)
    assert all(0.0 <= i["match"] <= 1.0 for step in rec["steps"] for i in step["ingredients"])


def test_minor_rule_lowers_salicylic_acid_and_adds_note():
    adult = KB.recommend(OILY, "oily", age=25)["steps"][0]["ingredients"][0]
    minor = KB.recommend(OILY, "oily", age=16)["steps"][0]["ingredients"][0]
    assert adult["match"] - minor["match"] == pytest.approx(0.10, abs=1e-4)
    assert minor["personal_notes"] and not adult["personal_notes"]


def test_prohibited_ingredient_is_never_recommended():
    kb = copy.deepcopy(KB.kb)
    kb["ingredients"]["niacinamide"]["regulatory"]["status"] = "prohibited"
    rec = Recommender(kb).recommend(OILY, "oily")
    assert "niacinamide" not in {i["id"] for s in rec["steps"] for i in s["ingredients"]}


def test_bpom_prohibited_list_is_always_shown():
    names = " ".join(a["name"] for a in KB.recommend(OILY, "oily")["avoid"]).lower()
    assert "mercury" in names and "hydroquinone" in names


def test_unknown_ingredient_in_routine_is_rejected():
    kb = copy.deepcopy(KB.kb)
    kb["routines"]["oily"]["steps"]["treat"].append("does_not_exist")
    with pytest.raises(ValueError):
        Recommender(kb)
