import math
from whoosh.index import open_dir
from whoosh.qparser import QueryParser
from whoosh.scoring import BM25F

ix = open_dir("indexdir")


# ------------------------
# Helper functions
# ------------------------

def tokenize(text):
    return text.lower().split()


def count_words(text):
    return len(tokenize(text))


def compute_tf(term, text):
    tokens = tokenize(text)
    if not tokens:
        return 0.0
    return tokens.count(term) / len(tokens)


def compute_idf(term):
    with ix.searcher() as searcher:
        N = searcher.doc_count()
        df = searcher.reader().doc_frequency("content", term)
        return math.log((N + 1) / (df + 1)) + 1


def make_snippet(text, query, window=150):
    text_lower = text.lower()
    terms = [t for t in query.lower().split() if t not in ["and", "or", "not"]]

    for term in terms:
        pos = text_lower.find(term)
        if pos != -1:
            start = max(pos - window, 0)
            end = min(pos + window, len(text))
            return (
                ("..." if start > 0 else "") +
                text[start:end] +
                ("..." if end < len(text) else "")
            )

    return text[:300] + "..."


# ------------------------
# Main search function
# ------------------------

def search(query):
    results = {}

    parser = QueryParser("content", ix.schema)
    q = parser.parse(query)

    # extract meaningful query terms
    query_terms = [
        t for t in query.lower().split()
        if t not in ["and", "or", "not"]
    ]

    # global statistics
    with ix.searcher() as s:
        avgdl = sum(
            count_words(s.stored_fields(docnum)["content"])
            for docnum in range(s.doc_count())
        ) / s.doc_count()

    # ---------- Boolean + TF-IDF per term ----------
    with ix.searcher() as searcher:
        boolean_results = searcher.search(q, limit=10)

        for r in boolean_results:
            content = r["content"]
            dl = count_words(content)

            tfidf_terms = []
            for term in query_terms:
                tf = round(compute_tf(term, content), 4)
                idf = round(compute_idf(term), 4)
                tfidf = round(tf * idf, 4)

                tfidf_terms.append({
                    "term": term,
                    "tf": tf,
                    "idf": idf,
                    "tfidf": tfidf
                })

            results[r["title"]] = {
                "title": r["title"],
                "word_count": dl,
                "snippet": make_snippet(content, query),
                "tfidf_terms": tfidf_terms,
                "bm25": None,
                "bm25_components": {},
                "boolean": "Yes"
            }

    # ---------- BM25 components ----------
    with ix.searcher(weighting=BM25F()) as searcher:
        bm25_results = searcher.search(q, limit=10)

        for r in bm25_results:
            if r["title"] in results:
                dl = results[r["title"]]["word_count"]

                results[r["title"]]["bm25"] = round(r.score, 4)
                results[r["title"]]["bm25_components"] = {
                    "dl": dl,
                    "avgdl": round(avgdl, 2)
                }

    return list(results.values())