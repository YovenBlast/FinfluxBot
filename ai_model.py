import os

from dotenv import load_dotenv
from google import genai


# ==========================================
# Load .env
# ==========================================

load_dotenv()


# ==========================================
# Get API key
# ==========================================

API_KEY = os.getenv(
    "GEMINI_API_KEY"
)


if not API_KEY:

    raise RuntimeError(
        "GEMINI_API_KEY was not found."
    )


# ==========================================
# Create Gemini client
# ==========================================

client = genai.Client(
    api_key=API_KEY
)


# ==========================================
# Generate AI answer
# ==========================================

def generate_answer(
    question,
    search_results
):

    if not search_results:

        return (
            "I could not find relevant "
            "information in the documents."
        )


    # ======================================
    # Build context
    # ======================================

    context_parts = []


    for result in search_results:

        filename = result.get(
            "filename",
            "Unknown document"
        )

        page = result.get(
            "page",
            ""
        )

        text = result.get(
            "text",
            ""
        )

        context_parts.append(

            f"""
DOCUMENT: {filename}
PAGE / SECTION: {page}

CONTENT:
{text}
"""

        )


    context = "\n\n".join(
        context_parts
    )


    # ======================================
    # AI prompt
    # ======================================

    prompt = f"""
You are an intelligent document assistant.

Answer the user's question using the
provided document information.

USER QUESTION:
{question}

DOCUMENT INFORMATION:
{context}

RULES:

1. Use the provided documents as your
   primary source.

2. Do not invent facts.

3. Answer the question directly.

4. Explain the answer clearly.

5. You may summarize the documents.

6. If appropriate, use bullet points.

7. If the documents don't contain enough
   information, say that clearly.

8. Do not simply copy large amounts of
   document text.
"""


    # ======================================
    # Call Gemini
    # ======================================

    print(
        "\nCalling Gemini 3.6 Flash..."
    )


    response = client.models.generate_content(

        model="gemini-3.6-flash",

        contents=prompt

    )


    # ======================================
    # Validate response
    # ======================================

    if not response:

        return (
            "Gemini returned no response."
        )


    if not response.text:

        return (
            "Gemini returned an empty answer."
        )


    print(
        "Gemini answer generated successfully."
    )


    return response.text.strip()