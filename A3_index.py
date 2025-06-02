import os
from typing import Dict, List, Optional
import re
import json
from collections import defaultdict
import pickle
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
import warnings
import math

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)


class Posting:
    def __init__(self, doc_id: int, term_freq: int, importance: int = 4, tf_idf: float = 0.0):

        self.doc_id = doc_id
        self.term_freq = term_freq
        self.importance = importance # importance: 1 for h1, 2 for h2, 3 for h3, 4 for normal text or no heading
        self.tf_idf = tf_idf

    def __repr__(self):
        return f"Posting(doc_id={self.doc_id}, tf={self.term_freq}, imp={self.importance}, tf_idf={self.tf_idf:.2f})"


class InvertedIndex:
    def __init__(self):
        self.index: Dict[str, List[Posting]] = defaultdict(list)
        self.doc_id_map: Dict[int, str] = {}
        self.doc_id_counter: int = 0
        self.default_importance: int = 4  # normal text
        self.doc_freq: Dict[str, int] = defaultdict(int)  # Document frequency for each token, for tf-idf calculations

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
        tokens = re.findall(r'\b[a-zA-Z0-9]{2,}\b', text.lower())
        filtered_tokens = [self.stem(token) for token in tokens]
        return filtered_tokens
    # plus 1 point for the three gram
    def three_gram(self, text: str) -> List[str]:
        words = self.tokenize(text)
        three_grams = []

        for i in range(len(words) - 2):
            three_grams.append(''.join(words[i:i + 3]))

        return three_grams

    def hash_value(self, three_gram: str) -> int:
        import hashlib
        return int(hashlib.md5(three_gram.encode('utf-8')).hexdigest(), 16)

    def select_hash(self, hashes: List[int], k: int = 50) -> List[int]:
        return sorted(hashes)[:k]

    # plus 2 for fingerprint since this finds near dupes
    def get_fp(self, text: str) -> List[int]:
        three_grams = self.three_gram(text)
        hashes = [self.hash_value(g) for g in three_grams]
        fingerprint = self.select_hash(hashes)
        return fingerprint

    def add_document(self, content: str, url: str, importance_map: Optional[Dict[str, int]] = None):
        """
        content: cleaned text of document
        importance_map: token->importance level (1-4)
        """
        # Compute fingerprint for the document
        fingerprint = self.get_fp(content)

        # Check for near-duplicates
        for doc_id, metadata in self.doc_id_map.items():
            existing_fp = metadata.get("fingerprint")
            if existing_fp and len(set(fingerprint) & set(existing_fp)) > 0:  # Adjust threshold as needed
                print(f"Skipping {url} — near-duplicate of document ID {doc_id}.")
                return  # Skip indexing this document

        # Assign a new document ID
        doc_id = self.doc_id_counter
        self.doc_id_counter += 1

        # Store document metadata (URL and fingerprint)
        self.doc_id_map[doc_id] = {"url": url, "fingerprint": fingerprint}

        if importance_map is None:
            importance_map = {}

        # Tokenize content and count term frequencies
        tokens = self.tokenize(content)
        term_counts = defaultdict(int)
        for token in tokens:
            term_counts[token] += 1

        # Track document frequency for each token
        unique_tokens = set(tokens)
        for token in unique_tokens:
            self.doc_freq[token] += 1

        # Add tokens to the index
        for token, freq in term_counts.items():
            imp = importance_map.get(token, self.default_importance)
            self.index[token].append(Posting(doc_id, freq, imp))

    def find_near_duplicates(self, content: str) -> List[int]:
        fingerprint = self.get_fp(content)
        near_duplicates = []

        for doc_id, metadata in self.doc_id_map.items():
            existing_fp = metadata["fingerprint"]
            # Compare fingerprints (e.g., using set intersection)
            if len(set(fingerprint) & set(existing_fp)) > 0:  # Adjust threshold as needed
                near_duplicates.append(doc_id)

        return near_duplicates

    def compute_tf_idf(self):
        num_docs = len(self.doc_id_map)
        for token, postings in self.index.items():
            idf = math.log(num_docs / (1 + self.doc_freq[token]))  # 1 so we dont divide by zero
            for posting in postings:
                tf = posting.term_freq
                posting.tf_idf = tf * idf  # Add tf_idf attribute to Posting class

    def sort_postings(self):
        for token, postings in self.index.items():
            postings.sort(key=lambda p: (-p.tf_idf, p.importance))

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
    root_dir = "/Users/joehoshina/Information-Retrieval/Assignment3/search"

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

    # Compute TF-IDF
    index.compute_tf_idf()

    # Sort postings before saving or printing
    index.sort_postings()

    # Print the index to verify TF-IDF scores
    index.print_index()

    # index.print_index()
    index.show_index_stats("index.pkl")