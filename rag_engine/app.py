"""
app.py — The RAG Engine Interface

A minimal CLI interface that stitches together Phase 4:
User Query -> Guardrails -> Retriever -> Generator -> Output
"""

import os
import sys

# Ensure our local modules can be imported if running from root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag_engine.guardrails import check_intent
from rag_engine.retriever import Retriever
from rag_engine.generator import Generator

def main():
    print("="*60)
    print("  Mutual Fund FAQ Chatbot - Phase 4 Engine Test")
    print("  Type 'exit' or 'quit' to close.")
    print("="*60)

    # Initialize Phase 4 modules
    retriever = Retriever()
    generator = Generator()

    if not os.environ.get("OPENAI_API_KEY"):
        print("\n[WARNING] OPENAI_API_KEY environment variable is missing!")
        print("The generation layer will return mock data.\n")

    while True:
        try:
            user_input = input("\nYou: ")
        except (KeyboardInterrupt, EOFError):
            break
            
        if user_input.lower() in ["exit", "quit"]:
            print("Goodbye!")
            break
            
        if not user_input.strip():
            continue

        # ---------------------------------------------------------
        # STEP 1: Guardrails Intercept
        # ---------------------------------------------------------
        intent_status = check_intent(user_input)
        if intent_status["blocked"]:
            print(f"\n[INTERCEPTED - {intent_status['reason'].upper()}]")
            print(f"Chatbot: {intent_status['message']}")
            continue

        # ---------------------------------------------------------
        # STEP 2: Retrieval
        # ---------------------------------------------------------
        print("\n[Thinking...]")
        chunks = retriever.query(user_input)
        
        # ---------------------------------------------------------
        # STEP 3: Generation (Facts Only, Max 3 Sentences, Citation)
        # ---------------------------------------------------------
        answer = generator.generate_response(user_input, chunks)
        
        print("\nChatbot:")
        print(answer)

if __name__ == "__main__":
    main()
