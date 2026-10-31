//! `BombGameState.RoundResults` -- per-round winning team and outcome.

use vrf_bitio::BitReader;

use super::framing::{decode_elements, member_name, read_narrow_byte};
use super::{Result, StructBlobError};
use crate::decode::scalar::read_fname;

/// Names this blob in error messages.
const CONTEXT: &str = "RoundResults";

/// A byte enum with its wire values and the snake_case spelling exporters
/// write. An unusable width or an unknown value is an error, never `None`,
/// which means "not sent in this update".
macro_rules! wire_enum {
    ($(#[$doc:meta])* $name:ident { $($variant:ident = $value:literal => $text:literal,)+ }) => {
        $(#[$doc])*
        #[derive(Debug, Clone, Copy, PartialEq, Eq)]
        #[repr(u8)]
        pub enum $name {
            $($variant = $value,)+
        }

        impl $name {
            /// The snake_case spelling exporters write.
            #[must_use]
            pub const fn as_str(self) -> &'static str {
                match self {
                    $(Self::$variant => $text,)+
                }
            }

            fn read(sub: &mut BitReader<'_>, name: &str) -> Result<Self> {
                match read_narrow_byte(sub, name, CONTEXT)? {
                    $($value => Ok(Self::$variant),)+
                    value => Err(StructBlobError::UnknownEnumValue {
                        enum_name: stringify!($name),
                        value,
                        context: CONTEXT,
                    }),
                }
            }
        }
    };
}

wire_enum! {
    /// The role a team played during the round.
    AresTeamRole {
        None = 0 => "none",
        Attacker = 1 => "attacker",
        Defender = 2 => "defender",
        FreeForAll = 3 => "free_for_all",
        Any = 4 => "any",
        RoleCount = 5 => "role_count",
    }
}

wire_enum! {
    /// How the round ended.
    AresRoundOutcome {
        Elimination = 0 => "elimination",
        Defuse = 1 => "defuse",
        Detonate = 2 => "detonate",
        TimeExpired = 3 => "time_expired",
        Cheat = 4 => "cheat",
        Surrendered = 5 => "surrendered",
        RoundOutcomeCount = 6 => "round_outcome_count",
        Invalid = 7 => "invalid",
    }
}

/// A sparse per-team outcome from 13.09 RoundResults.TeamResults.
/// Names and handles are read from the replay; an absent field stays None.
#[derive(Debug, Clone, Default, PartialEq, Eq)]
pub struct TeamRoundResult {
    /// Zero-based index in TeamResults (not necessarily the numbered team).
    pub index: u32,
    pub team_name: Option<String>,
    pub team_number: Option<i32>,
    pub team_role: Option<AresTeamRole>,
    /// Raw enum byte; 1/2 have been observed, not assigned universal semantics.
    pub team_outcome: Option<u8>,
}

/// A single round result entry; a `None` member was not sent in this update.
#[derive(Debug, Clone, Default, PartialEq)]
pub struct RoundResult {
    /// Zero-based round number.
    pub round_number: u32,
    /// The team name that won (e.g. "Blue", "Red").
    pub winning_team: Option<String>,
    /// The role of the winning team.
    pub winning_team_role: Option<AresTeamRole>,
    /// How the round ended.
    pub round_result: Option<AresRoundOutcome>,
    /// Raw `WinningTeamMode` enum byte, declared from 13.09; its names are unknown.
    pub winning_team_mode: Option<u8>,
    /// Per-team outcome updates, available since 13.09; raw parent is retained.
    pub team_results: Option<Vec<TeamRoundResult>>,
}

/// Decode a `BombGameState.RoundResults` blob; see the module docs for
/// `reader`, `declared` and why members are selected by declared name.
pub fn decode_round_results(
    reader: &mut BitReader<'_>,
    declared: &[Option<&str>],
) -> Result<Vec<RoundResult>> {
    decode_elements(
        reader,
        CONTEXT,
        |handle| member_name(declared, handle, CONTEXT),
        |round_number| RoundResult {
            round_number,
            ..RoundResult::default()
        },
        |row, name, sub| {
            match name {
                "WinningTeam" => row.winning_team = Some(read_fname::<StructBlobError>(sub, 1024)?),
                "WinningTeamRole" => row.winning_team_role = Some(AresTeamRole::read(sub, name)?),
                "RoundResult" => row.round_result = Some(AresRoundOutcome::read(sub, name)?),
                "WinningTeamMode" => {
                    row.winning_team_mode = Some(read_narrow_byte(sub, name, CONTEXT)?);
                }
                "TeamResults" => {
                    row.team_results = Some(decode_team_results(sub, declared)?);
                }
                // Still opaque: preserve the whole parent blob, rather than
                // assert an unmeasured object-reference grammar.
                "EliminatedTeams" => sub.skip_remaining(),
                _ => return Ok(None),
            }
            // `read_fname` is self-delimiting, `read_narrow_byte` takes the
            // whole window.
            Ok(Some(name))
        },
    )
}

/// Decode nested per-team results with the same bounded RepLayout grammar
/// as the enclosing array. Each handle must resolve through the replay's
/// declared field table; no 13.09 numeric handle is guessed.
fn decode_team_results(
    reader: &mut BitReader<'_>,
    declared: &[Option<&str>],
) -> Result<Vec<TeamRoundResult>> {
    const TEAM_CONTEXT: &str = "TeamResults";
    decode_elements(
        reader,
        TEAM_CONTEXT,
        |handle| member_name(declared, handle, TEAM_CONTEXT),
        |index| TeamRoundResult {
            index,
            ..TeamRoundResult::default()
        },
        |team, name, sub| {
            match name {
                "TeamName" => team.team_name = Some(read_fname::<StructBlobError>(sub, 1024)?),
                "TeamNumber" => team.team_number = Some(sub.read_i32()?),
                "TeamRole" => team.team_role = Some(AresTeamRole::read(sub, name)?),
                "TeamOutcome" => {
                    team.team_outcome = Some(read_narrow_byte(sub, name, TEAM_CONTEXT)?);
                }
                _ => return Ok(None),
            }
            Ok(Some(name))
        },
    )
}
