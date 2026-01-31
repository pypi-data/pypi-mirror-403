import random

def main():
    # Word list to choose from
    word_pool = [
        "apple", "banana", "cherry", "dragon", "elephant",
        "forest", "garden", "harmony", "island", "jungle",
        "kingdom", "lantern", "mountain", "nebula", "ocean",
        "phoenix", "quantum", "rainbow", "sunset", "thunder",
        "umbrella", "volcano", "whisper", "xylophone", "yellow",
        "zephyr", "adventure", "brilliant", "cascade", "diamond"
    ]
    
    # Select 5 random words
    random_words = random.sample(word_pool, 5)
    
    result = {
        "random_words": random_words,
        "count": len(random_words),
        "description": "A list of 5 randomly selected words"
    }
    
    return result

result = main()