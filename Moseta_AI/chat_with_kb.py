"""Command-line chat. The logic lives in rag_engine.py (shared with the backend)."""
from rag_engine import generate_answer, kb_info, load


def main():
    print("\nLoading Moseta AI (first run takes a moment)...")
    load()
    print("Knowledge base chunks:", kb_info()["chunks"])
    print("Type 'exit' to stop.\n")
    while True:
        q = input("You: ").strip()
        if q.lower() in ("exit", "quit"):
            break
        if not q:
            continue
        try:
            answer, results, is_campaign, platforms = generate_answer(q)
            print("\n", answer, "\n")
            for r in results:
                print(f"- {r['source']} | chunk {r['chunk_number']} | sim {r['score']:.4f}")
            print()
        except Exception as e:
            print("Error:", e)


if __name__ == "__main__":
    main()
