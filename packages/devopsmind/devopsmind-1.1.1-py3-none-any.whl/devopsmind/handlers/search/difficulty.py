# src/devopsmind/handlers/search/difficulty.py

DIFFICULTY_XP = {
    "Easy": 50,
    "Medium": 100,
    "Hard": 150,
    "Expert": 300,
    "Master": 500,
    "Architect": 750,
    "Principal": 1000,
    "Staff": 1300,
    "Distinguished": 1600,
    "Fellow": 2000,
}

VALID_DIFFICULTIES = set(DIFFICULTY_XP.keys())
