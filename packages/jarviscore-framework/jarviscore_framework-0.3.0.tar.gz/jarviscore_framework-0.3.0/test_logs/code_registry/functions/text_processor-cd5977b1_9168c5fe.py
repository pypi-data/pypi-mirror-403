async def main():
    words = ["apple", "banana", "cherry", "date", "elderberry"]
    
    word_lengths = {word: len(word) for word in words}
    total_characters = sum(word_lengths.values())
    
    result = {
        "words": words,
        "individual_lengths": word_lengths,
        "total_characters": total_characters
    }
    
    return result