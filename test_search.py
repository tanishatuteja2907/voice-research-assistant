import assistant as core

chunks = core.load_chunks()
toks, idf = core.build_index(chunks)

while True:
    q = input("Question (press Enter alone to quit): ").strip()
    if not q:
        break
    passages = core.search(q, chunks, toks, idf)
    print("\nPASSAGES FOUND:")
    for src, txt in passages[:3]:
        print("-", src, "|", txt[:200], "\n")
    print("ANSWER:", core.ask_llm(q, passages, "en"), "\n")