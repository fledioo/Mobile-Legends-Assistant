from flask import Flask, render_template, request, jsonify, send_from_directory
import os
from rag import query_rag

app = Flask(__name__)

# ─── Routes ───────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index_new.html")


@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json()
    if not data or "question" not in data:
        return jsonify({"error": "Pertanyaan tidak ditemukan"}), 400

    question = data["question"].strip()
    if not question:
        return jsonify({"error": "Pertanyaan kosong"}), 400

    result = query_rag(question)

    image_url = None
    if result.get("image_path"):
        # Buat URL yang bisa diakses browser: /images/heroes/balmond.jpg
        image_url = "/" + result["image_path"].replace("\\", "/")

    return jsonify({
        "answer":    result.get("answer", "Maaf, saya tidak menemukan jawaban."),
        "image_url": image_url,
        "hero_name": result.get("hero_name"),
        "hero_data": result.get("hero_data")
    })


@app.route("/heroes", methods=["GET"])
def list_heroes():
    """Endpoint untuk mendapatkan daftar semua hero"""
    from rag import heroes_data
    return jsonify(heroes_data)


# ─── Static file serving ──────────────────────────────────────────────────────

@app.route("/images/<path:filename>")
def serve_image(filename):
    """Serve gambar dari folder images/"""
    images_dir = os.path.join(os.path.dirname(__file__), "images")
    return send_from_directory(images_dir, filename)


# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)