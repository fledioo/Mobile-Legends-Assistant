# 🏆 MLBB Hero Assistant — RAG Chatbot

Chatbot AI berbasis RAG (Retrieval-Augmented Generation) untuk Mobile Legends Bang Bang.
Menjawab pertanyaan tentang **hero, item, emblem, combo, counter, build, dan lore** dari 50 hero.

---

## 📁 Struktur Project

```
ML-RAG-CHATBOT/
├── data/
│   ├── heroes.json          # Data 50 hero (nama, role, lane, image_path)
│   ├── items.json           # Data item + fungsi
│   ├── emblems.json         # Data emblem + talent
│   ├── combos.json          # Combo skill 50 hero
│   ├── counters.json        # Counter info 50 hero
│   ├── recommendations.json # Rekomendasi item + emblem per hero
│   └── lores.json           # Lore / backstory 50 hero
│
├── images/
│   └── heroes/
│       ├── balmond.jpg
│       ├── layla.jpg
│       └── ... (gambar semua hero)
│
├── templates/
│   └── index.html           # UI chat frontend
│
├── app.py                   # Flask server
├── rag.py                   # RAG engine (intent + jawaban)
├── ingest.py                # Build knowledge_base.pkl
├── requirements.txt
└── README.md
```

---

## 🚀 Cara Menjalankan

### 1. Install dependensi
```bash
pip install -r requirements.txt
```

### 2. (Opsional) Build knowledge base
```bash
python ingest.py
```

### 3. Jalankan server
```bash
python app.py
```

### 4. Buka browser
```
http://localhost:5000
```

---

## 💬 Contoh Pertanyaan

| Pertanyaan | Intent |
|---|---|
| `Siapa itu Balmond?` | Info hero + gambar |
| `Ceritakan lore Fanny` | Backstory hero |
| `Combo terbaik Saber` | Skill combo |
| `Counter Layla siapa?` | Counter info |
| `Build item untuk Wanwan` | Item recommendation |
| `Informasi item Blade of Despair` | Detail item |
| `Assassin Emblem itu apa?` | Detail emblem |
| `Daftar semua hero` | List hero |

---

## 🖼️ Menambah Gambar Hero

Letakkan gambar di folder `images/heroes/` dengan nama **sesuai `image_path`** di `heroes.json`:

```
images/heroes/balmond.jpg   → "image_path": "images/heroes/balmond.jpg"
images/heroes/layla.jpg     → "image_path": "images/heroes/layla.jpg"
```

Format yang didukung: `.jpg`, `.jpeg`, `.png`, `.webp`

---

## ⚙️ Konfigurasi

Buat file `.env` jika diperlukan:
```env
FLASK_DEBUG=true
FLASK_PORT=5000
```
