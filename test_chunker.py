import json
from pathlib import Path
from chunker.chunker_embedder import create_atomic_fact_chunk, create_contextual_chunks

def test_chunking():
    data_dir = Path("data/scraped")
    json_files = list(data_dir.glob("*.json"))
    
    if not json_files:
        print("No json files found for testing.")
        return
        
    # We will just test the first file (e.g. SBI Contra)
    test_file = json_files[0]
    with open(test_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    print(f"\n--- Testing Scheme: {data['scheme_name']} ---\n")
    
    # 1. Test Atomic Fact Chunk
    atomic_chunks = create_atomic_fact_chunk(data)
    print("OK: ATOMIC FACT CHUNK:")
    print("--------------------------------------------------")
    print(atomic_chunks[0]['text'])
    print("--------------------------------------------------")
    
    # 2. Test Contextual Text Splitting
    context_chunks = create_contextual_chunks(data)
    print(f"\nOK: CONTEXTUAL CHUNKS (Total: {len(context_chunks)})")
    if context_chunks:
        print("First Context Chunk sample:")
        print("--------------------------------------------------")
        print(context_chunks[0]['text'])
        print("--------------------------------------------------")

if __name__ == "__main__":
    test_chunking()
