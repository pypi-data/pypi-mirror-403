import random

def main():
    # List of common words to choose from
    word_list = [
        "apple", "banana", "cherry", "dragon", "elephant",
        "forest", "garden", "harmony", "island", "jungle",
        "kingdom", "lantern", "mountain", "nebula", "ocean",
        "phoenix", "quantum", "rainbow", "sunset", "thunder",
        "umbrella", "volcano", "whisper", "xylophone", "yellow",
        "zenith", "adventure", "brilliant", "cascade", "diamond",
        "eclipse", "fountain", "glacier", "horizon", "infinity",
        "journey", "kaleidoscope", "lighthouse", "mystery", "northern",
        "orchestra", "paradise", "question", "reflection", "symphony",
        "treasure", "universe", "velocity", "wanderer", "yesterday"
    ]
    
    # Select 5 random words
    random_words = random.sample(word_list, 5)
    
    result = {
        "random_words": random_words,
        "count": len(random_words),
        "description": "A list of 5 randomly selected words"
    }
    
    return result

result = main()