from document_processor import (
    process_pdf,
    process_docx,
    process_image
)

from search_engine import search_documents
from ai_model import generate_answer

from flask import (
    Flask,
    render_template,
    request,
    jsonify
)

import os
import json
import time
import pytesseract


# ==========================================
# Flask application
# ==========================================

app = Flask(__name__)


# ==========================================
# Configuration
# ==========================================

DOCS_FOLDER = "docs"
UPLOAD_FOLDER = "uploads"
DATA_FOLDER = "data"

DATABASE_FILE = os.path.join(
    DATA_FOLDER,
    "documents.json"
)


# ==========================================
# Create required folders
# ==========================================

os.makedirs(
    DOCS_FOLDER,
    exist_ok=True
)

os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)

os.makedirs(
    DATA_FOLDER,
    exist_ok=True
)


# ==========================================
# Tesseract configuration
# ==========================================


TESSERACT_PATH = os.getenv(
    "TESSERACT_PATH"
)

if TESSERACT_PATH:
    pytesseract.pytesseract.tesseract_cmd = (
        TESSERACT_PATH
    )


# ==========================================
# Load document database
# ==========================================

def load_documents():

    if not os.path.exists(
        DATABASE_FILE
    ):

        return []

    try:

        with open(
            DATABASE_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(file)

    except Exception as e:

        print(
            f"Error loading document database: {e}"
        )

        return []


# ==========================================
# Save document database
# ==========================================

def save_documents(documents):

    try:

        with open(
            DATABASE_FILE,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                documents,
                file,
                ensure_ascii=False,
                indent=2
            )

    except Exception as e:

        print(
            f"Error saving document database: {e}"
        )


# ==========================================
# Index PDF and Word Documents
# ==========================================

def index_documents():

    documents = []

    print(
        "\n==================================="
    )

    print(
        "Indexing documents"
    )

    print(
        "==================================="
    )


    # ======================================
    # Scan docs folder
    # ======================================

    try:

        filenames = os.listdir(
            DOCS_FOLDER
        )

    except Exception as e:

        print(
            f"Unable to read docs folder: {e}"
        )

        return []


    # ======================================
    # Process files
    # ======================================

    for filename in filenames:

        filepath = os.path.join(
            DOCS_FOLDER,
            filename
        )


        # ==================================
        # Skip folders
        # ==================================

        if not os.path.isfile(filepath):

            continue


        # ==================================
        # Get extension
        # ==================================

        extension = os.path.splitext(
            filename
        )[1].lower()


        # ==================================
        # PDF
        # ==================================

        if extension == ".pdf":

            print(
                f"\nReading PDF: {filename}"
            )

            try:

                pages = process_pdf(
                    filepath
                )


                for page in pages:

                    documents.append({

                        "type":
                            "pdf",

                        "filename":
                            filename,

                        "page":
                            page["page"],

                        "text":
                            page["text"]

                    })


                print(
                    f"  Added {len(pages)} PDF pages."
                )


            except Exception as e:

                print(
                    f"Error reading PDF "
                    f"{filename}: {e}"
                )


        # ==================================
        # Word DOCX
        # ==================================

        elif extension == ".docx":

            print(
                f"\nReading Word document: "
                f"{filename}"
            )

            try:

                sections = process_docx(
                    filepath
                )


                for section in sections:

                    documents.append({

                        "type":
                            "docx",

                        "filename":
                            filename,

                        "page":
                            section["page"],

                        "text":
                            section["text"]

                    })


                print(
                    f"  Added "
                    f"{len(sections)} Word sections."
                )


            except Exception as e:

                print(
                    f"Error reading DOCX "
                    f"{filename}: {e}"
                )


        # ==================================
        # Unsupported file
        # ==================================

        else:

            print(
                f"Skipping unsupported file: "
                f"{filename}"
            )


    # ======================================
    # Save index
    # ======================================

    save_documents(
        documents
    )


    print(
        "\n==================================="
    )

    print(
        f"Indexed "
        f"{len(documents)} document sections."
    )

    print(
        "===================================\n"
    )


    return documents


# ==========================================
# Home page
# ==========================================

@app.route("/")
def index():

    return render_template(
        "index.html"
    )


# ==========================================
# Ask AI about documents
# ==========================================

@app.route(
    "/ask",
    methods=["POST"]
)
def ask():
   # ==========================================
    # Start total timer
    # ==========================================

    total_start_time = time.perf_counter()

    try:

        data = request.get_json(
            silent=True
        )


        # ==================================
        # Validate request
        # ==================================

        if not data:

            return jsonify({

                "response":
                    "Invalid request.",

                "sources":
                    []

            }), 400


        question = data.get(
            "question",
            ""
        ).strip()


        # ==================================
        # Empty question
        # ==================================

        if not question:

            return jsonify({

                "response":
                    "Please enter a question.",

                "sources":
                    []

            }), 400


        # ==================================
        # Load documents
        # ==================================
        load_start_time = time.perf_counter()

        documents = load_documents()

        load_time = (
            time.perf_counter()
            - load_start_time
        )

        print(
            f"Document load time: "
            f"{load_time:.3f} seconds"
        )

        if not documents:

            return jsonify({

                "response":
                    "No PDF or Word documents "
                    "have been indexed yet.",

                "sources":
                    []

            })


        # ==================================
        # Search relevant documents
        # ==================================
        search_start_time = time.perf_counter()

        results = search_documents(

            question,

            documents,

            top_k=3

        )

        search_time = (
            time.perf_counter()
            - search_start_time
        )


        print(
            f"Search time: "
            f"{search_time:.3f} seconds"
        )

        # ==================================
        # No relevant results
        # ==================================

        if not results:

            total_time = (
                time.perf_counter()
                - total_start_time
            )

            print(
                f"Total request time: "
                f"{total_time:.3f} seconds"
            )

            return jsonify({

                "response":
                    "I couldn't find relevant "
                    "information in the available "
                    "documents.",

                "sources":
                    []

            })


        # ==================================
        # Generate AI answer
        # ==================================
 
        print(
            "Calling Gemini..."
        )


        ai_start_time = time.perf_counter()

        try:

            ai_response = generate_answer(

                question,

                results

            )

        except Exception as e:

            ai_time = (
                time.perf_counter()
                - ai_start_time
            )

            total_time = (
                time.perf_counter()
                - total_start_time
            )
            print(
                f"AI time before error: "
                f"{ai_time:.3f} seconds"
            )

            print(
                f"Total request time: "
                f"{total_time:.3f} seconds"
            )

            print(
                "\n================================="
            )

            print(
                "AI ERROR:"
             )

            print(
                  repr(e)
            )

            print(
                 "=================================\n"
            )
             

            return jsonify({

               "response":
                     f"AI error: {str(e)}",

                "sources":
                    []

            }), 500

        ai_time = (
            time.perf_counter()
            - ai_start_time
        )


        print(
            f"AI generation time: "
            f"{ai_time:.3f} seconds"
        )


        # ==================================
        # Build source information
        # ==================================
        source_start_time = time.perf_counter()

        sources = []


        for result in results:

            sources.append({

                "filename":
                    result.get(
                        "filename",
                        "Unknown"
                    ),

                "type":
                    result.get(
                        "type",
                        "unknown"
                    ),

                "page":
                    result.get(
                        "page",
                        ""
                    ),

                "score":
                    round(

                        float(
                            result.get(
                                "score",
                                0
                            )
                        ),

                        3

                    )

            })

        source_time = (
            time.perf_counter()
            - source_start_time
        )


        print(
            f"Source processing time: "
            f"{source_time:.3f} seconds"
        )

        # ==========================================
        # Calculate total time
        # ==========================================

        total_time = (
            time.perf_counter()
            - total_start_time
        )

        # ==========================================
        # Runtime summary
        # ==========================================

        print(
            "\n==================================="
        )

        print(
            "RUNTIME SUMMARY"
        )

        print(
            "==================================="
        )

        print(
            f"Document load : "
            f"{load_time:.3f} sec"
        )

        print(
            f"Document search: "
            f"{search_time:.3f} sec"
        )

        print(
            f"AI generation : "
            f"{ai_time:.3f} sec"
        )

        print(
            f"Source process: "
            f"{source_time:.3f} sec"
        )

        print(
            "-----------------------------------"
        )

        print(
            f"TOTAL         : "
            f"{total_time:.3f} sec"
        )

        print(
            "===================================\n"
        )


        # ==================================
        # Return AI answer
        # ==================================

        # ==========================================
        # Return answer
        # ==========================================

        return jsonify({

            "response":
                ai_response,

            "sources":
                sources,

            "timing": {

                "document_load":
                    round(
                        load_time,
                        3
                    ),

                "search":
                    round(
                        search_time,
                        3
                    ),

                "ai":
                    round(
                        ai_time,
                        3
                    ),

                "source_processing":
                    round(
                        source_time,
                        3
                    ),

                "total":
                    round(
                        total_time,
                        3
                    )

            }

        })


    except Exception as e:

        total_time = (
            time.perf_counter()
            - total_start_time
        )


        print(
            "\n================================="
        )

        print(
            "ASK ERROR:"
        )

        print(
            repr(e)
        )

        print(
            f"Total request time: "
            f"{total_time:.3f} seconds"
        )

        print(
            "=================================\n"
        )


        return jsonify({

            "response":
                f"An error occurred: {str(e)}",

            "sources":
                []

        }), 500


# ==========================================
# Analyze screenshot
# ==========================================

@app.route(
    "/analyze-image",
    methods=["POST"]
)
def analyze_image():

    try:

        # ==================================
        # Check image
        # ==================================

        if "image" not in request.files:

            return jsonify({

                "response":
                    "No screenshot was uploaded."

            }), 400


        image_file = request.files[
            "image"
        ]


        if image_file.filename == "":

            return jsonify({

                "response":
                    "Please select an image."

            }), 400


        # ==================================
        # Save image
        # ==================================

        filename = image_file.filename

        filepath = os.path.join(
            UPLOAD_FOLDER,
            filename
        )


        image_file.save(
            filepath
        )


        # ==================================
        # OCR
        # ==================================

        text = process_image(
            filepath
        )


        if not text.strip():

            return jsonify({

                "response":
                    "I could not detect "
                    "readable text in this "
                    "screenshot."

            })


        # ==================================
        # Return extracted text
        # ==================================

        response = (

            "Text detected in the "
            "screenshot:\n\n"

            + text

        )


        return jsonify({

            "response":
                response,

            "text":
                text

        })


    except Exception as e:

        print(
            "IMAGE ERROR:",
            e
        )


        return jsonify({

            "response":
                f"Unable to analyse screenshot: "
                f"{str(e)}"

        }), 500


# ==========================================
# Re-index documents
# ==========================================

@app.route(
    "/reindex",
    methods=["POST"]
)
def reindex():

    try:

        documents = index_documents()


        return jsonify({

            "success":
                True,

            "message":
                f"Successfully indexed "
                f"{len(documents)} document sections."

        })


    except Exception as e:

        print(
            "REINDEX ERROR:",
            e
        )


        return jsonify({

            "success":
                False,

            "message":
                str(e)

        }), 500


# ==========================================
# Run application
# ==========================================


if __name__ == "__main__":

    print(
        "\n==================================="
    )

    print(
        "Document Chatbot"
    )

    print(
        "==================================="
    )

    index_documents()

    print(
        "\nServer starting..."
    )


    # ======================================
    # Index PDFs and Word documents
    # ======================================

    app.run(
        host="0.0.0.0",
        port=int(
            os.environ.get(
                "PORT",
                5000
            )
        ),
        debug=False
    )
