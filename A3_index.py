import os
from typing import Dict, List, Set
import re
import json
from collections import defaultdict
import pickle


class Posting:
    def __init__(self, doc_id: int, term_freq: int): # doc_id is integer adding 1 when one more file is read, term_frequency is integer
        self.doc_id = doc_id
        self.term_freq = term_freq

    def __repr__(self):
        return f"Posting(doc_id={self.doc_id}, tf={self.term_freq})"

class InvertedIndex:
    def __init__(self):
        self.index: Dict[str, List[Posting]] = defaultdict(list) # string is token, list posting is the entity posting contain id and tf
        self.doc_id_map = {} # map doc_id(int) to url(str)
        self.doc_id_counter = 0
    
    def tokenize(self, text: str) -> List[str]:
        stop_words = {
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
        tokens = re.findall(r'\b[a-zA-Z0-9]{2,}\b', text.lower())
        filtered_tokens = [token for token in tokens if token not in stop_words]
        return filtered_tokens


    def add_document(self, content: str, url: str):
        doc_id = self.doc_id_counter
        self.doc_id_counter += 1
        self.doc_id_map[doc_id] = url
        tokens = self.tokenize(content) #list of tokens
        term_counts = defaultdict(int)
        for token in tokens:
            term_counts[token] += 1

        for token, freq in term_counts.items():
            self.index[token].append(Posting(doc_id, freq))
    
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
    # root_dir = "/Users/jiananhong/Desktop/cs121/xtune_ics_uci_edu" 

    root_dir = "/Users/jiananhong/Desktop/cs121/"

    for dirpath, dirnames, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.endswith(".json"):
                filepath = os.path.join(dirpath, filename)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        content = data.get("content", "")
                        url = data.get("url", filepath)  # fallback to file path if no URL
                        index.add_document(content, url)
                except Exception as e:
                    print(f"Error reading {filepath}: {e}")
    #index.print_index()
    index.show_index_stats("index.pkl")

