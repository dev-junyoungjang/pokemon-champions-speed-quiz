from app.core.speed import calculate_effective_speed, evs_to_stat_points, stage_modifier, stat_points_to_evs
from app.models.domain import BaseStats, PokemonBuild, StatPointSpread, StatSpread


def build_garchomp(**overrides):
    data = {
        "pokemonId": "garchomp",
        "pokemonName": "Garchomp",
        "baseStatsSnapshot": BaseStats.model_validate(
            {"hp": 108, "atk": 130, "def": 95, "spa": 80, "spd": 85, "spe": 102}
        ),
        "level": 50,
        "nature": "Jolly",
        "statPoints": StatPointSpread(spe=32),
    }
    data.update(overrides)
    return PokemonBuild(**data)


def test_level_50_jolly_max_stat_point_garchomp_is_169():
    result = calculate_effective_speed(build_garchomp(), include_modifiers=False)
    assert result.raw_speed == 169
    assert result.effective_speed == 169


def test_legacy_ev_252_converts_to_32_stat_points():
    result = calculate_effective_speed(
        build_garchomp(statPoints=StatPointSpread(), evs=StatSpread(atk=252, spd=4, spe=252)),
        include_modifiers=False,
    )
    assert evs_to_stat_points(252) == 32
    assert stat_points_to_evs(32) == 252
    assert result.raw_speed == 169


def test_choice_scarf_applies_after_raw_speed():
    result = calculate_effective_speed(build_garchomp(item="Choice Scarf"), include_modifiers=True)
    assert result.raw_speed == 169
    assert result.effective_speed == 253


def test_tailwind_and_paralysis_are_floored_stepwise():
    result = calculate_effective_speed(build_garchomp(tailwind=True, status="paralysis"), include_modifiers=True)
    assert result.raw_speed == 169
    assert result.effective_speed == 169
    assert "field Tailwind: x2.00" in result.modifiers
    assert "status paralysis: x0.50" in result.modifiers


def test_weather_speed_ability_and_quick_feet():
    swift_swim = calculate_effective_speed(build_garchomp(ability="Swift Swim", weather="rain"), include_modifiers=True)
    quick_feet = calculate_effective_speed(build_garchomp(ability="Quick Feet", status="burn"), include_modifiers=True)
    assert swift_swim.effective_speed == 338
    assert quick_feet.effective_speed == 253


def test_speed_stage_modifier_values():
    assert stage_modifier(1).numerator == 3
    assert stage_modifier(1).denominator == 2
    assert stage_modifier(-1).numerator == 2
    assert stage_modifier(-1).denominator == 3
