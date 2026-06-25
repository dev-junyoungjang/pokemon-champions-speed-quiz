from app.core.speed import calculate_effective_speed, stage_modifier
from app.models.domain import BaseStats, PokemonBuild, StatSpread


def build_garchomp(**overrides):
    data = {
        "pokemonId": "garchomp",
        "pokemonName": "Garchomp",
        "baseStatsSnapshot": BaseStats.model_validate(
            {"hp": 108, "atk": 130, "def": 95, "spa": 80, "spd": 85, "spe": 102}
        ),
        "level": 50,
        "nature": "Jolly",
        "evs": StatSpread(atk=252, spd=4, spe=252),
    }
    data.update(overrides)
    return PokemonBuild(**data)


def test_level_50_jolly_max_speed_garchomp_is_169():
    result = calculate_effective_speed(build_garchomp(), include_modifiers=False)
    assert result.raw_speed == 169
    assert result.effective_speed == 169


def test_choice_scarf_applies_after_raw_speed():
    result = calculate_effective_speed(build_garchomp(item="Choice Scarf"), include_modifiers=True)
    assert result.raw_speed == 169
    assert result.effective_speed == 253


def test_speed_stage_modifier_values():
    assert stage_modifier(1).numerator == 3
    assert stage_modifier(1).denominator == 2
    assert stage_modifier(-1).numerator == 2
    assert stage_modifier(-1).denominator == 3
