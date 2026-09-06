import re

from sklearn.feature_extraction.text import (
    TfidfVectorizer
)

from sklearn.metrics.pairwise import (
    cosine_similarity
)


# ==========================================
# Clean text
# ==========================================

def clean_text(text):

    text = text.lower()

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# ==========================================
# Search documents
# ==========================================

def search_documents(
    question,
    documents,
    top_k=3
):

    if not documents:

        return []


    # ======================================
    # Prepare text
    # ======================================

    corpus = [

        clean_text(
            document["text"]
        )

        for document in documents

    ]


    question = clean_text(
        question
    )


    # ======================================
    # TF-IDF
    # ======================================

    vectorizer = TfidfVectorizer(

        stop_words="english",

        ngram_range=(1, 2)

    )


    try:

        document_vectors = (
            vectorizer.fit_transform(
                corpus
            )
        )

        question_vector = (
            vectorizer.transform(
                [question]
            )
        )

    except ValueError:

        return []


    # ======================================
    # Similarity
    # ======================================

    similarities = cosine_similarity(

        question_vector,

        document_vectors

    )[0]


    # ======================================
    # Sort
    # ======================================

    ranked_indexes = similarities.argsort()[::-1]


    results = []


    for index in ranked_indexes[:top_k]:

        score = similarities[index]


        # Ignore completely unrelated results

        if score <= 0:

            continue


        document = documents[index]


        results.append({

    "type":
        document.get(
            "type",
            "unknown"
        ),

    "filename":
        document["filename"],

    "page":
        document["page"],

    "text":
        document["text"],

    "score":
        float(score)

})


    return results