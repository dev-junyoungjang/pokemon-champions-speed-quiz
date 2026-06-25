export type BaseStats = {
  hp: number
  atk: number
  def: number
  spa: number
  spd: number
  spe: number
}

export type StatSpread = Partial<BaseStats>

export type TeamMember = {
  slot: number
  pokemonId: string
  pokemonName: string
  baseStatsSnapshot: BaseStats
  level: number
  nature: string
  ability?: string | null
  item?: string | null
  evs: StatSpread
  ivs: StatSpread
  speedStage?: number
  weather?: string | null
  status?: string | null
}

export type UserTeam = {
  teamName: string
  format: string
  members: TeamMember[]
}
