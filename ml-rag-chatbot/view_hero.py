"""
view_hero.py - Fungsi untuk menampilkan gambar hero
"""

import os
from PIL import Image
import matplotlib.pyplot as plt
from ingest import load_knowledge_base, retrieve


def show_hero_image(hero_name, knowledge_base=None):
    """
    Tampilkan gambar hero berdasarkan nama
    """
    # Load KB jika belum ada
    if knowledge_base is None:
        knowledge_base = load_knowledge_base()
    
    # Cari hero
    results = retrieve(f"hero {hero_name}", knowledge_base, top_k=1)
    
    if not results:
        print(f"❌ Hero '{hero_name}' tidak ditemukan!")
        return False
    
    doc = results[0]['document']
    hero_name = doc.get('name', '')
    image_path = doc.get('image_path', '')
    
    # Cek apakah path gambar ada
    if not image_path:
        print(f"⚠️  Hero '{hero_name}' tidak memiliki image_path")
        return False
    
    if not os.path.exists(image_path):
        print(f"⚠️  File gambar tidak ditemukan: {image_path}")
        print(f"💡 Tips: Pastikan file gambar sudah didownload ke folder yang benar")
        return False
    
    # Tampilkan gambar
    try:
        img = Image.open(image_path)
        
        # Dapatkan info role dan lane
        raw_data = doc.get('raw', {})
        role = raw_data.get('role', ['N/A'])[0]
        lane = raw_data.get('lane', 'N/A')
        
        # Buat figure
        fig, ax = plt.figure(figsize=(6, 8)), plt.gca()
        plt.imshow(img)
        plt.axis('off')
        
        # Title dengan info hero
        title = f"🎮 {hero_name}\n{role} | Lane: {lane}"
        plt.title(title, fontsize=14, fontweight='bold', pad=20, 
                  bbox={'facecolor': 'white', 'alpha': 0.8, 'pad': 10})
        
        plt.tight_layout()
        plt.show()
        
        print(f"✅ Menampilkan gambar: {hero_name}")
        print(f"📁 Path: {image_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Gagal memuat gambar: {e}")
        return False


def list_heroes_with_images(knowledge_base=None):
    """
    List semua hero dan status gambarnya
    """
    if knowledge_base is None:
        knowledge_base = load_knowledge_base()
    
    heroes = [doc for doc in knowledge_base['documents'] if doc['type'] == 'hero']
    
    print(f"\n📋 Daftar Hero ({len(heroes)} total):")
    print("=" * 70)
    print(f"{'No':<4} {'Nama':<20} {'Role':<15} {'Gambar':<10}")
    print("-" * 70)
    
    for i, hero in enumerate(heroes, 1):
        name = hero.get('name', 'Unknown')
        role = hero.get('raw', {}).get('role', ['N/A'])[0]
        image_path = hero.get('image_path', '')
        
        # Cek status gambar
        if image_path and os.path.exists(image_path):
            status = "✅ Ada"
        else:
            status = "❌ Tidak"
        
        print(f"{i:<4} {name:<20} {role:<15} {status:<10}")
    
    print("=" * 70)


# Contoh penggunaan
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Jika ada argument, tampilkan gambar hero tersebut
        hero_name = " ".join(sys.argv[1:])
        show_hero_image(hero_name)
    else:
        # Jika tidak ada argument, list semua hero
        kb = load_knowledge_base()
        list_heroes_with_images(kb)
        
        print("\n💡 Cara pakai:")
        print("   python view_hero.py Balmond     # Tampilkan gambar Balmond")
        print("   python view_hero.py Layla       # Tampilkan gambar Layla")