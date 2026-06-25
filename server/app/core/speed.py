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


def calculate_raw_speed(build: PokemonBuild) -> int:
    base = build.base_stats_snapshot.spe
    iv = build.ivs.spe
    ev = build.evs.spe
    level = build.level
    nature = NATURE_SPEED_MODIFIERS.get(build.nature, Fraction(1, 1))
    before_nature = ((2 * base + iv + ev // 4) * level) // 100 + 5
    return int(before_nature * nature)


def stage_modifier(stage: int) -> Fraction:
    if stage >= 0:
        return Fraction(2 + stage, 2)
    return Fraction(2, 2 - stage)


def calculate_effective_speed(build: PokemonBuild, include_modifiers: bool = True) -> SpeedComputation:
    raw = calculate_raw_speed(build)
    speed = Fraction(raw, 1)
    modifiers: list[str] = [f"raw={raw}"]

    if include_modifiers:
        if build.speed_stage:
            mod = stage_modifier(build.speed_stage)
            speed *= mod
            modifiers.append(f"stage {build.speed_stage}: x{float(mod):.2f}")

        if build.item in ITEM_SPEED_MODIFIERS:
            mod = ITEM_SPEED_MODIFIERS[build.item]
            speed *= mod
            modifiers.append(f"item {build.item}: x{float(mod):.2f}")

        if build.ability and build.weather:
            key = (build.ability, build.weather.lower())
            if key in WEATHER_SPEED_ABILITIES:
                mod = WEATHER_SPEED_ABILITIES[key]
                speed *= mod
                modifiers.append(f"ability {build.ability} in {build.weather}: x{float(mod):.2f}")

        if build.status and build.status.lower() == "paralysis":
            mod = Fraction(1, 2)
            speed *= mod
            modifiers.append("status paralysis: x0.50")

    return SpeedComputation(rawSpeed=raw, effectiveSpeed=int(speed), modifiers=modifiers)


def base_speed_of(build: PokemonBuild) -> int:
    return build.base_stats_snapshot.spe
