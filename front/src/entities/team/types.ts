export type BaseStats = {
  hp: number
  atk: number
  def: number
  spa: number
  spd: number
  spe: number
}

export type StatSpread = Partial<BaseStats>

export type StatPointSpread = Partial<BaseStats>

export type PokemonImageAssets = {
  primaryArtworkUrl?: string | null
  fallbackArtworkUrl?: string | null
  spriteUrl?: string | null
  sourceName?: string
  hotlinkPolicy?: string
}

export type PokemonMoveOption = {
  moveId: string
  nameEn: string
  nameKo: string
  type: string
  damageClass?: string | null
  power?: number | null
  accuracy?: number | null
}

export type TeamMember = {
  slot: number
  pokemonId: string
  pokemonName: string
  nationalDexNumber?: number | null
  imageAssets?: PokemonImageAssets | null
  baseStatsSnapshot: BaseStats
  speciesTypes?: string[]
  availableMoves?: PokemonMoveOption[]
  moves?: string[]
  level: number
  nature: string
  ability?: string | null
  item?: string | null
  evs: StatSpread
  statPoints?: StatPointSpread
  ivs: StatSpread
  speedStage?: number
  weather?: string | null
  status?: string | null
  tailwind?: boolean
  itemConsumed?: boolean
}

export type PokemonSpecies = {
  pokemonId: string
  nameEn: string
  nameKo: string
  speciesId: string
  speciesNameEn: string
  speciesNameKo: string
  nationalDexNumber: number
  pokemonChampionsCode: string
  baseStats: BaseStats
  imageAssets: PokemonImageAssets
  types: string[]
  availableMoves: PokemonMoveOption[]
}

export type UserTeam = {
  teamName: string
  format: string
  members: TeamMember[]
}
