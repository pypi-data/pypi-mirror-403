import random

def main():
    # List of common words to choose from
    word_pool = [
        "apple", "banana", "cherry", "dragon", "elephant",
        "forest", "garden", "harmony", "island", "jungle",
        "kitchen", "lantern", "mountain", "notebook", "ocean",
        "penguin", "quantum", "rainbow", "sunshine", "thunder",
        "umbrella", "village", "whisper", "xylophone", "yellow",
        "zebra", "adventure", "butterfly", "chocolate", "diamond",
        "energy", "freedom", "gravity", "horizon", "imagine",
        "journey", "knowledge", "library", "mystery", "nature",
        "opportunity", "paradise", "question", "reflection", "serenity",
        "treasure", "universe", "velocity", "wonder", "zenith"
    ]
    
    try:
        # Select 5 random words from the pool
        random_words = random.sample(word_pool, 5)
        
        result = {
            "description": "List of 5 randomly selected words",
            "count": 5,
            "words": random_words
        }
        
        return result
    except Exception as e:
        return {
            "error": str(e),
            "words": []
        }

# Execute and store result
result = main()