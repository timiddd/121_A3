# simple_search.py

import pickle
from test import InvertedIndex, Posting
import re
def load_index(index_path='index.pkl') -> InvertedIndex:
    """Load pickled (index, doc_id_map) into an InvertedIndex instance."""
    with open(index_path, 'rb') as f:
        idx_data, doc_map = pickle.load(f)
    idx = InvertedIndex()
    idx.index = idx_data
    idx.doc_id_map = doc_map
    return idx

def stem(word: str) -> str:
    # (Porter stemmer steps as before)
    if word.endswith("sses"):
        word = word[:-2]
    elif word.endswith("ies") or word.endswith("ied"):
        if len(word) > 4:
            word = word[:-3] + "i"
        else:
            word = word[:-3] + "ie"
    elif word.endswith("s") and not word.endswith("us") and not word.endswith("ss"):
        if re.search(r"[aeiou].+s$", word):
            word = word[:-1]

    if word.endswith("eed") or word.endswith("eedly"):
        stem_part = word[:-3] if word.endswith("eed") else word[:-5]
        if re.search(r"[aeiou][^aeiou]", stem_part):
            word = word[:-1] if word.endswith("eed") else word[:-3]
    elif any(word.endswith(suffix) for suffix in ["ed", "edly", "ing", "ingly"]):
        suffixes = {"ed": 2, "edly": 4, "ing": 3, "ingly": 5}
        for suffix, length in suffixes.items():
            if word.endswith(suffix):
                stem = word[:-length]
                if re.search(r"[aeiou]", stem):
                    word = stem
                    if word.endswith(("at", "bl", "iz")):
                        word += "e"
                    elif re.search(r"([^aeiou])\1$", word) and not word.endswith(("ll", "ss", "zz")):
                        word = word[:-1]
                    elif len(word) <= 3:
                        word += "e"
                break
    return word
def simple_search(query: str, index: InvertedIndex, top_k: int = 5) -> list[str]:

    token = query.lower().split()
    tokens = []
    for tok in token:
        tok = stem(tok)
        tokens.append(tok)


    if not tokens:
        return []

    postings_lists = [index.index.get(tok, []) for tok in tokens]
    # empty = no documents can match
    if any(len(pl) == 0 for pl in postings_lists):
        return []
    # AND
    common_docs = set(post.doc_id for post in postings_lists[0])
    for pl in postings_lists[1:]:
        common_docs &= {post.doc_id for post in pl}
    if not common_docs:
        return []

    # Rank
    results = []
    for post in postings_lists[0]:
        if post.doc_id in common_docs:
            results.append(index.doc_id_map[post.doc_id])
            if len(results) >= top_k:
                break

    return results

if __name__ == '__main__':
    idx = load_index()
    while True:
        q = input("Search> ").strip()
        if not q:
            continue
        res = simple_search(q, idx)
        if res:
            print("Top results:")
            for url in res:
                print("-", url)
        else:
            print("No documents found.")
