import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_json(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_speed_formula_rules_data_matches_engine_contract():
    rules = load_json("data/rules/speed_formula_v1.json")
    assert rules["ruleset"] == "pokemon_champions"
    assert rules["formulaVersion"] == "speed:v1"
    assert rules["statPointSystem"]["maxPerStat"] == 32
    assert rules["statPointSystem"]["maxTotal"] == 66
    assert rules["rawSpeedFormula"]["formula"] == (
        "floor((floor(((2 * base + iv + 2 * statPoints) * level) / 100) + 5) * natureModifier)"
    )
    assert rules["itemModifiers"]["Choice Scarf"] == "3/2"
    assert rules["fieldModifiers"]["tailwind"] == "2/1"
    assert rules["statusModifiers"]["paralysis"] == "1/2"


def test_regulation_m_b_rules_reference_curated_roster_and_sources():
    rules = load_json("data/rules/regulation_m_b_rules.json")
    curated_path = ROOT.parent / rules["eligiblePokemon"]["curatedJsonl"]
    source_ids = {json.loads(line)["sourceId"] for line in (ROOT / "data/rules/rule_sources.jsonl").read_text(encoding="utf-8").splitlines()}
    assert rules["regulationSet"] == "M-B"
    assert curated_path.exists()
    assert rules["battleRules"]["duplicateHeldItemsAllowed"] is False
    assert rules["battleRules"]["megaEvolutionPerBattle"] == 1
    assert set(rules["sourceIds"]).issubset(source_ids)
