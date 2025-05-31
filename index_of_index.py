import pickle
from A3_index import InvertedIndex, Posting

def build_secondary_index(index_path='index.pkl',
                          lexicon_path='lexicon.pkl',
                          postings_path='postings.dat'):

    # lexicon.pkl include dict { term: (offset, length) } and doc_id_map
    # postings.dat all postings
    # load the full index
    with open(index_path, 'rb') as f:
        full_index, doc_id_map = pickle.load(f)

    lexicon = {}

    with open(postings_path, 'wb') as pf:
        for term, postings in full_index.items():
            offset = pf.tell() # tell where the posting start
            data = pickle.dumps(postings)
            pf.write(data) # now pf holding all index info
            lexicon[term] = (offset, len(data)) # length represent how much to read

    # 2) persist the lexicon and the doc_id_map
    with open(lexicon_path, 'wb') as lf:
        pickle.dump((lexicon, doc_id_map), lf)

if __name__ == '__main__':
    build_secondary_index()