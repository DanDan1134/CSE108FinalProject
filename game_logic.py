VALID_WORDS = {"APPLE", "WATER", "SMILE", "POINT", "RAISE"}

def is_valid_word(word: str) -> bool:
    return word.upper() in VALID_WORDS

def evaluate_guess(target: str, guess: str):
    target = target.upper()
    guess = guess.upper()
    result = ["miss"] * len(target)

    target_counts = {}
    for i, (s, g) in enumerate(zip(target, guess)):
        if g == s:
            result[i] = "correct"
        else:
            target_counts[s] = target_counts.get(s, 0) + 1

    for i, (s, g) in enumerate(zip(target, guess)):
        if result[i] == "correct":
            continue
        if target_counts.get(g, 0) > 0:
            result[i] = "present"
            target_counts[g] -= 1

    return result
