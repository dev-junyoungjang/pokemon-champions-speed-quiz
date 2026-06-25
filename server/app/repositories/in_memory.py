from __future__ import annotations

from copy import deepcopy

from app.models.domain import BaseStats, IvSpread, MetaSample, StatSpread, TeamMember, UserTeam


def _stats(hp: int, atk: int, defense: int, spa: int, spd: int, spe: int) -> BaseStats:
    return BaseStats.model_validate({"hp": hp, "atk": atk, "def": defense, "spa": spa, "spd": spd, "spe": spe})


DEFAULT_TEAM = UserTeam(
    teamName="main",
    members=[
        TeamMember(
            slot=1,
            pokemonId="garchomp",
            pokemonName="Garchomp",
            baseStatsSnapshot=_stats(108, 130, 95, 80, 85, 102),
            nature="Jolly",
            ability="Rough Skin",
            item="Choice Scarf",
            evs=StatSpread(atk=252, spd=4, spe=252),
            ivs=IvSpread(),
        ),
        TeamMember(
            slot=2,
            pokemonId="dragonite",
            pokemonName="Dragonite",
            baseStatsSnapshot=_stats(91, 134, 95, 100, 100, 80),
            nature="Jolly",
            ability="Multiscale",
            item="Loaded Dice",
            evs=StatSpread(atk=252, spd=4, spe=252),
            ivs=IvSpread(),
        ),
    ],
)

DEFAULT_META = [
    MetaSample(
        pokemonId="flutter-mane",
        pokemonName="Flutter Mane",
        baseStatsSnapshot=_stats(55, 55, 55, 135, 135, 135),
        nature="Timid",
        ability="Protosynthesis",
        item="Booster Energy",
        evs=StatSpread(spa=252, spd=4, spe=252),
        ivs=IvSpread(atk=0),
        usageRank=1,
    ),
    MetaSample(
        pokemonId="chien-pao",
        pokemonName="Chien-Pao",
        baseStatsSnapshot=_stats(80, 120, 80, 90, 65, 135),
        nature="Jolly",
        ability="Sword of Ruin",
        item="Focus Sash",
        evs=StatSpread(atk=252, spd=4, spe=252),
        usageRank=2,
    ),
    MetaSample(
        pokemonId="landorus-therian",
        pokemonName="Landorus-Therian",
        baseStatsSnapshot=_stats(89, 145, 90, 105, 80, 91),
        nature="Jolly",
        ability="Intimidate",
        item="Choice Scarf",
        evs=StatSpread(atk=252, spd=4, spe=252),
        usageRank=3,
    ),
    MetaSample(
        pokemonId="palafin-hero",
        pokemonName="Palafin-Hero",
        baseStatsSnapshot=_stats(100, 160, 97, 106, 87, 100),
        nature="Jolly",
        ability="Zero to Hero",
        item="Mystic Water",
        evs=StatSpread(atk=252, spd=4, spe=252),
        usageRank=4,
    ),
]


class InMemoryRepository:
    def __init__(self) -> None:
        self._teams: dict[str, UserTeam] = {"main": deepcopy(DEFAULT_TEAM)}
        self._meta_samples: list[MetaSample] = deepcopy(DEFAULT_META)

    def get_team(self, team_name: str = "main") -> UserTeam:
        return deepcopy(self._teams.get(team_name, DEFAULT_TEAM))

    def save_team(self, team: UserTeam) -> UserTeam:
        ordered = sorted(team.members, key=lambda member: member.slot)
        saved = team.model_copy(update={"members": ordered})
        self._teams[saved.team_name] = deepcopy(saved)
        return deepcopy(saved)

    def list_active_meta_samples(self) -> list[MetaSample]:
        return [deepcopy(sample) for sample in self._meta_samples if sample.active]
