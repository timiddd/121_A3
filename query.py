import pickle
from A3_index import InvertedIndex, Posting
import re
from nltk.stem.porter import PorterStemmer
STOPWORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", "aren't", "as", "at",
    "be", "because", "been", "before", "being", "below", "between", "both", "but", "by", "can", "can't", "cannot", "could",
    "couldn't", "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down", "during", "each", "few", "for",
    "from", "further", "get", "had", "hadn't", "has", "hasn't", "have", "haven't", "having", "he", "he'd", "he'll", "he's",
    "her", "here", "here's", "hers", "herself", "him", "himself", "his", "how", "how's", "i", "i'd", "i'll", "i'm",
    "i've", "if", "in", "into", "is", "isn't", "it", "it's", "its", "itself", "let's", "may", "me", "more", "most", "mustn't",
    "my", "myself", "next", "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought", "our", "ours",
    "ourselves", "out", "over", "own", "same", "shan't", "she", "she'd", "she'll", "she's", "should", "shouldn't", "so",
    "some", "such", "than", "that", "that's", "the", "their", "theirs", "them", "themselves", "then", "there", "there's",
    "these", "they", "they'd", "they'll", "they're", "they've", "this", "those", "through", "to", "too", "under",
    "until", "up", "very", "was", "wasn't", "we", "we'd", "we'll", "we're", "we've", "were", "weren't", "what", "what's",
    "when", "when's", "where", "where's", "which", "while", "who", "who's", "whom", "why", "why's", "with", "won't",
    "would", "wouldn't", "you", "you'd", "you'll", "you're", "you've", "your", "yours", "yourself", "yourselves"
}
"""
M2 ver
def load_index(index_path='index.pkl') -> InvertedIndex:
    # Load pickled (index, doc_id_map) into an InvertedIndex instance.
    with open(index_path, 'rb') as f:
        idx_data, doc_map = pickle.load(f)
    idx = InvertedIndex()
    idx.index = idx_data
    idx.doc_id_map = doc_map
    return idx
    """

stemmer = PorterStemmer()

def load_lexicon(lexicon_path='lexicon.pkl'):
    # Load index of index
    with open(lexicon_path, 'rb') as f:
        lexicon, doc_id_map = pickle.load(f)
    return lexicon, doc_id_map

def fetch_postings(term: str,
                   lexicon: dict,
                   postings_path='postings.dat') -> list:
    if term not in lexicon:
        return []
    offset, length = lexicon[term]

    with open(postings_path, 'rb') as pf:
        pf.seek(offset)
        blob = pf.read(length) # now holding the post we wanna search
    return pickle.loads(blob)



# def stem(word: str) -> str:
#     # (Porter stemmer steps as before)
#     if word.endswith("sses"):
#         word = word[:-2]
#     elif word.endswith("ies") or word.endswith("ied"):
#         if len(word) > 4:
#             word = word[:-3] + "i"
#         else:
#             word = word[:-3] + "ie"
#     elif word.endswith("s") and not word.endswith("us") and not word.endswith("ss"):
#         if re.search(r"[aeiou].+s$", word):
#             word = word[:-1]
#
#     if word.endswith("eed") or word.endswith("eedly"):
#         stem_part = word[:-3] if word.endswith("eed") else word[:-5]
#         if re.search(r"[aeiou][^aeiou]", stem_part):
#             word = word[:-1] if word.endswith("eed") else word[:-3]
#     elif any(word.endswith(suffix) for suffix in ["ed", "edly", "ing", "ingly"]):
#         suffixes = {"ed": 2, "edly": 4, "ing": 3, "ingly": 5}
#         for suffix, length in suffixes.items():
#             if word.endswith(suffix):
#                 stem = word[:-length]
#                 if re.search(r"[aeiou]", stem):
#                     word = stem
#                     if word.endswith(("at", "bl", "iz")):
#                         word += "e"
#                     elif re.search(r"([^aeiou])\1$", word) and not word.endswith(("ll", "ss", "zz")):
#                         word = word[:-1]
#                     elif len(word) <= 3:
#                         word += "e"
#                 break
#     return word
def simple_search(query: str,
                  lexicon: dict,
                  doc_id_map: dict,
                  postings_path: str = 'postings.dat',
                  top_k: int = 5) -> list[str]:

    # tokenize and stem
    # tokens = [stem(tok) for tok in query.lower().split()]
    # if not tokens:
    #     return []

    # Extract only alphanumeric tokens (lowercased)
    raw_tokens = re.findall(r"[a-z0-9]+", query.lower())
    # Remove pure‐digit tokens and common stopwords
    filtered = [tok for tok in raw_tokens if not tok.isdigit() and tok not in STOPWORDS]
    # Stem
    tokens = [stemmer.stem(tok) for tok in filtered]

    # get each term’s postings from postings.dat
    postings_lists = [fetch_postings(tok, lexicon, postings_path)
                      for tok in tokens] # seek implement here so we only get the word we want
    if len(postings_lists) == 0:
        return []
    if any(len(pl) == 0 for pl in postings_lists):
        return []

    # AND
    common = set(p.doc_id for p in postings_lists[0])
    for pl in postings_lists[1:]:
        common &= {p.doc_id for p in pl}
    if not common:
        return []

    # rank
    results = []
    for p in postings_lists[0]:
        if p.doc_id in common:
            results.append(doc_id_map[p.doc_id])
            if len(results) >= top_k:
                break
    return results

if __name__ == '__main__':
    lexicon, doc_id_map = load_lexicon('lexicon.pkl')
    while True:
        q = input("Search> ").strip()
        if not q:
            continue
        res = simple_search(q, lexicon, doc_id_map, 'postings.dat')
        if res:
            print("Top results:")
            for url in res:
                print("-", url)
        else:
            print("No documents found.")
