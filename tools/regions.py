"""The Endless Ocean releases this patcher knows.

Each entry is one retail disc id.  `game` picks the feature set ('eo1' is the
first game, 'bw' is Blue World / Endless Ocean 2); `version` is the disc
revision byte.  Per-release addresses live in the generators under src/.
"""
REGIONS = {
    'RFBE01': dict(game='eo1', label='Endless Ocean (USA)', short='USA', version=0),
    'R4EE01': dict(game='bw', label='Endless Ocean: Blue World (USA)', short='USA', version=0),
}

GAMES = {
    'eo1': 'Endless Ocean',
    'bw': 'Endless Ocean: Blue World',
}
