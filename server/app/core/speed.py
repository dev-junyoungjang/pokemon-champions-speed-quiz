from __future__ import annotations

from fractions import Fraction

from app.models.domain import PokemonBuild, SpeedComputation

NATURE_SPEED_MODIFIERS: dict[str, Fraction] = {
    "Timid": Fraction(11, 10),
    "Jolly": Fraction(11, 10),
    "Hasty": Fraction(11, 10),
    "Naive": Fraction(11, 10),
    "Brave": Fraction(9, 10),
    "Quiet": Fraction(9, 10),
    "Relaxed": Fraction(9, 10),
    "Sassy": Fraction(9, 10),
    "Neutral": Fraction(1, 1),
}

ITEM_SPEED_MODIFIERS: dict[str, Fraction] = {
    "Choice Scarf": Fraction(3, 2),
    "Iron Ball": Fraction(1, 2),
    "Macho Brace": Fraction(1, 2),
}

WEATHER_SPEED_ABILITIES: dict[tuple[str, str], Fraction] = {
    ("Swift Swim", "rain"): Fraction(2, 1),
    ("Chlorophyll", "sun"): Fraction(2, 1),
    ("Sand Rush", "sand"): Fraction(2, 1),
    ("Slush Rush", "snow"): Fraction(2, 1),
}

STATUS_SPEED_ABILITIES: dict[str, Fraction] = {
    "Quick Feet": Fraction(3, 2),
}

STATE_SPEED_ABILITIES: dict[tuple[str, str], Fraction] = {
    ("Unburden", "item_consumed"): Fraction(2, 1),
}


def evs_to_stat_points(evs: int) -> int:
    """Convert legacy EV-like values to Pokémon Champions stat points.

    Community Champions calculators expose this compatibility mapping:
    0-3 EV => 0 SP, then 4 EV => 1 SP and every +8 EV adds one SP,
    capped at 32 SP.
    """
    if evs < 4:
        return 0
    return min(1 + (evs - 4) // 8, 32)


def stat_points_to_evs(stat_points: int) -> int:
    if stat_points <= 0:
        return 0
    return 4 + (min(stat_points, 32) - 1) * 8


def speed_stat_points(build: PokemonBuild) -> int:
    explicit = build.stat_points.spe
    if explicit > 0:
        return explicit
    return evs_to_stat_points(build.evs.spe)


def calculate_raw_speed(build: PokemonBuild) -> int:
    base = build.base_stats_snapshot.spe
    iv = build.ivs.spe
    stat_points = speed_stat_points(build)
    level = build.level
    nature = NATURE_SPEED_MODIFIERS.get(build.nature, Fraction(1, 1))
    before_nature = ((2 * base + iv + 2 * stat_points) * level) // 100 + 5
    return int(before_nature * nature)


def stage_modifier(stage: int) -> Fraction:
    bounded = max(-6, min(6, stage))
    if bounded >= 0:
        return Fraction(2 + bounded, 2)
    return Fraction(2, 2 - bounded)


def apply_floor_modifier(speed: int, modifier: Fraction) -> int:
    return int(Fraction(speed, 1) * modifier)


def calculate_effective_speed(build: PokemonBuild, include_modifiers: bool = True) -> SpeedComputation:
    raw = calculate_raw_speed(build)
    speed = raw
    stat_points = speed_stat_points(build)
    modifiers: list[str] = [f"raw={raw}", f"stat points={stat_points}"]

    if include_modifiers:
        if build.speed_stage:
            mod = stage_modifier(build.speed_stage)
            speed = apply_floor_modifier(speed, mod)
            modifiers.append(f"stage {build.speed_stage}: x{float(mod):.2f}")

        if build.ability and build.weather:
            key = (build.ability, build.weather.lower())
            if key in WEATHER_SPEED_ABILITIES:
                mod = WEATHER_SPEED_ABILITIES[key]
                speed = apply_floor_modifier(speed, mod)
                modifiers.append(f"ability {build.ability} in {build.weather}: x{float(mod):.2f}")

        if build.ability and build.item_consumed:
            key = (build.ability, "item_consumed")
            if key in STATE_SPEED_ABILITIES:
                mod = STATE_SPEED_ABILITIES[key]
                speed = apply_floor_modifier(speed, mod)
                modifiers.append(f"ability {build.ability} after item consumed: x{float(mod):.2f}")

        if build.ability and build.status and build.ability in STATUS_SPEED_ABILITIES:
            mod = STATUS_SPEED_ABILITIES[build.ability]
            speed = apply_floor_modifier(speed, mod)
            modifiers.append(f"ability {build.ability} while statused: x{float(mod):.2f}")

        if build.tailwind:
            mod = Fraction(2, 1)
            speed = apply_floor_modifier(speed, mod)
            modifiers.append("field Tailwind: x2.00")

        if build.item in ITEM_SPEED_MODIFIERS:
            mod = ITEM_SPEED_MODIFIERS[build.item]
            speed = apply_floor_modifier(speed, mod)
            modifiers.append(f"item {build.item}: x{float(mod):.2f}")

        if build.status and build.status.lower() == "paralysis":
            mod = Fraction(1, 2)
            speed = apply_floor_modifier(speed, mod)
            modifiers.append("status paralysis: x0.50")

    return SpeedComputation(rawSpeed=raw, effectiveSpeed=speed, modifiers=modifiers)


def base_speed_of(build: PokemonBuild) -> int:
    return build.base_stats_snapshot.spe
