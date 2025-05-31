import os
from typing import Dict, List, Optional
import re
import json
from collections import defaultdict
import pickle
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
import warnings

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)


class Posting:
    def __init__(self, doc_id: int, term_freq: int, importance: int = 4):

        self.doc_id = doc_id
        self.term_freq = term_freq
        self.importance = importance # importance: 1 for h1, 2 for h2, 3 for h3, 4 for normal text or no heading

    def __repr__(self):
        return f"Posting(doc_id={self.doc_id}, tf={self.term_freq}, imp={self.importance})"


class InvertedIndex:
    def __init__(self):
        self.index: Dict[str, List[Posting]] = defaultdict(list)
        self.doc_id_map: Dict[int, str] = {}
        self.doc_id_counter: int = 0
        self.default_importance: int = 4  # normal text

    def stem(self, word: str) -> str:
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

    def tokenize(self, text: str) -> List[str]:
        # stop_words = {
        #     "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", "aren't", "as",
        #     "at",
        #     "be", "because", "been", "before", "being", "below", "between", "both", "but", "by", "can", "can't",
        #     "cannot", "could",
        #     "couldn't", "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down", "during", "each", "few",
        #     "for",
        #     "from", "further", "get", "had", "hadn't", "has", "hasn't", "have", "haven't", "having", "he", "he'd",
        #     "he'll", "he's",
        #     "her", "here", "here's", "hers", "herself", "him", "himself", "his", "how", "how's", "i", "i'd", "i'll",
        #     "i'm",
        #     "i've", "if", "in", "into", "is", "isn't", "it", "it's", "its", "itself", "let's", "may", "me", "more",
        #     "most", "mustn't",
        #     "my", "myself", "next", "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought",
        #     "our", "ours",
        #     "ourselves", "out", "over", "own", "same", "shan't", "she", "she'd", "she'll", "she's", "should",
        #     "shouldn't", "so",
        #     "some", "such", "than", "that", "that's", "the", "their", "theirs", "them", "themselves", "then", "there",
        #     "there's",
        #     "these", "they", "they'd", "they'll", "they're", "they've", "this", "those", "through", "to", "too",
        #     "under",
        #     "until", "up", "very", "was", "wasn't", "we", "we'd", "we'll", "we're", "we've", "were", "weren't", "what",
        #     "what's",
        #     "when", "when's", "where", "where's", "which", "while", "who", "who's", "whom", "why", "why's", "with",
        #     "won't",
        #     "would", "wouldn't", "you", "you'd", "you'll", "you're", "you've", "your", "yours", "yourself", "yourselves"
        # }
        tokens = re.findall(r'\b[a-zA-Z0-9]{2,}\b', text.lower())
        filtered_tokens = [self.stem(token) for token in tokens]
        return filtered_tokens

    def add_document(self, content: str, url: str, importance_map: Optional[Dict[str, int]] = None):
        """
        content: cleaned text of document
        importance_map: token->importance level (1-4)
        """
        doc_id = self.doc_id_counter
        self.doc_id_counter += 1
        self.doc_id_map[doc_id] = url

        if importance_map is None:
            importance_map = {}

        tokens = self.tokenize(content)
        term_counts = defaultdict(int)
        for token in tokens:
            term_counts[token] += 1

        for token, freq in term_counts.items():
            imp = importance_map.get(token, self.default_importance)
            self.index[token].append(Posting(doc_id, freq, imp))

    def sort_postings(self):

        for token, postings in self.index.items():
            postings.sort(key=lambda p: (p.importance, -p.term_freq))

    def print_index(self):
        for token, postings in self.index.items():
            print(f"{token}: {postings}")

    def show_index_stats(self, index_file_path: str):
        num_docs = len(self.doc_id_map)
        num_tokens = len(self.index)

        with open(index_file_path, "wb") as f:
            pickle.dump((self.index, self.doc_id_map), f)

        size_kb = os.path.getsize(index_file_path) / 1024
        print(f"Number of documents indexed: {num_docs}")
        print(f"Number of unique tokens: {num_tokens}")
        print(f"Size of index on disk: {size_kb:.2f} KB")


if __name__ == "__main__":
    index = InvertedIndex()
    root_dir = "/Users/jiananhong/Desktop/cs121"

    for dirpath, dirnames, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.endswith(".json"):
                filepath = os.path.join(dirpath, filename)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        raw_content = data.get("content", "")
                        url = data.get("url", filepath)

                        # parse HTML/XML
                        if raw_content.strip().startswith("<?xml") or "BEGIN:VCALENDAR" in raw_content:
                            soup = BeautifulSoup(raw_content, "xml")
                        else:
                            soup = BeautifulSoup(raw_content, "html.parser")

                        clean_text = soup.get_text(separator=" ", strip=True)

                        # build importance map from headings
                        importance_map: Dict[str, int] = {}
                        for level in [1, 2, 3]:
                            for tag in soup.find_all(f"h{level}"):
                                heading_text = tag.get_text(separator=" ", strip=True)
                                for token in index.tokenize(heading_text):
                                    importance_map[token] = min(importance_map.get(token, index.default_importance),
                                                                level)

                        # skip short content
                        if len(clean_text.strip()) < 20:
                            print(f"Skipping {url} — content too short or invalid.")
                            continue

                        index.add_document(clean_text, url, importance_map)

                except Exception as e:
                    print(f"Error processing {filepath}: {e}")

    # sort postings before saving or printing
    index.sort_postings()
    # index.print_index()
    index.show_index_stats("index.pkl")
