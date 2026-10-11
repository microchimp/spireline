"""Spireline: honest search for the best play in Slay the Spire 2 (v0.107.1, build 23811903).

Target (docs/DECISIONS.md D11, D12): Ascension 10 with all ten modifiers on, Acts 1-3, Defect first.
"""

__version__ = "0.0.1"
GAME_BUILD = 23811903
GAME_VERSION = "0.107.1"
ASCENSION = 10  # the only ascension Spireline reports (D11)
ACTS = (1, 2, 3)
PRIMARY_CHARACTER = "DEFECT"  # STS2MCP character_id (D12)
EMULATOR_SHA = "b7452170ce1df91de29d3c94acb11d87c7efc708"  # r33hab/sts2, reviewed before any build
MOD_SHA = "5a63f924f7e9dcbde4a1f70664e6d301c72e47c4"  # r33hab/STS2MCP spire-coach branch
