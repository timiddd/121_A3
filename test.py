from A3_index import Posting 
import pickle

def print_index(index):
    """
    Prints the inverted index with tokens and their postings.
    """
    for token, postings in index.items():
        print(f"{token}: {postings}")

if __name__ == "__main__":
    # Path to the serialized index file
    index_file_path = "/Users/joehoshina/Information-Retrieval/Assignment3/121_A3/index.pkl"

    # Load the index and document map from index.pkl
    try:
        with open(index_file_path, "rb") as f:
            index, doc_id_map = pickle.load(f)

        print(f"Loaded index with {len(index)} tokens.")
        print(f"Loaded document map with {len(doc_id_map)} documents.")

        # Print the inverted index
        print_index(index)

    except FileNotFoundError:
        print(f"Error: File '{index_file_path}' not found.")
    except Exception as e:
        print(f"Error loading index: {e}")