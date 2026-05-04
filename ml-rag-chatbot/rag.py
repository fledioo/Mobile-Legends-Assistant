"""
rag.py — RAG Engine untuk MLBB Chatbot
Mendukung: Hero, Item, Emblem, Combo, Counter, Build, Lore, Pro Player, Tim MPL, & M1 Championship
"""

import json
import os
import re
import pickle
from pathlib import Path

# ─── Load semua data JSON ─────────────────────────────────────────────────────
DATA_DIR = Path(__file__).parent / "data"

def load_json(filename: str) -> dict | list:
    path = DATA_DIR / filename
    if not path.exists():
        print(f"[WARNING] File tidak ditemukan: {path}")
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# Game Data
heroes_data        = load_json("heroes.json")
items_data         = load_json("items.json")
emblems_data       = load_json("emblems.json")
combos_data        = load_json("combos.json")
counters_data      = load_json("counters.json")
recommendations    = load_json("recommendations.json")
lores_data         = load_json("lores.json")

# Esports Data (BARU)
mpl_players_data   = load_json("mpl_players.json")
m1_championship_data = load_json("m1_world_championship.json")
mpl_teams_data     = load_json("mpl_teams.json")

# ─── Indexes untuk pencarian cepat ───────────────────────────────────────────
_hero_index: dict[str, dict] = {}
for hero in heroes_data.get("heroes", []):
    _hero_index[hero["name"].lower()] = hero

_player_index: dict[str, dict] = {}
for p in mpl_players_data.get("mpl_players", []):
    _player_index[p["nickname"].lower()] = p

_team_index: dict[str, dict] = {}
# Gabungkan tim M1 & MPL
for t in m1_championship_data.get("teams", []):
    _team_index[t["team_name"].lower()] = {**t, "source": "M1"}
for t in mpl_teams_data.get("mpl_teams", []):
    _team_index[t["team_name"].lower()] = {**t, "source": "MPL"}

# ─── Helper: Deteksi Nama ────────────────────────────────────────────────────
def detect_hero(text: str) -> dict | None:
    text_lower = text.lower()
    for name in sorted(_hero_index.keys(), key=len, reverse=True):
        if name in text_lower:
            return _hero_index[name]
    return None

def find_player(text: str) -> dict | None:
    """Cari player by nickname atau real name"""
    t = text.lower()
    
    # Direct match
    for nick in _player_index:
        if nick in t or t in nick:
            return _player_index[nick]
    
    # Cari di real_name juga
    for p in mpl_players_data.get("mpl_players", []):
        real_name = p.get("real_name", "").lower()
        if real_name and (real_name in t or t in real_name):
            return p
    
    return None

def find_team_by_player(player_name: str) -> dict | None:
    """Cari tim berdasarkan nama player"""
    player = find_player(player_name)
    if player:
        team_name = player.get("team", "").lower()
        return _team_index.get(team_name)
    return None

def find_team(text: str) -> dict | None:
    """Cari tim by nama tim ATAU by nama player"""
    t = text.lower()
    
    # 1. Direct team name match
    for name in _team_index:
        if name in t or t in name:
            return _team_index[name]
    
    # 2. Jika ada keyword "team" + player name (contoh: "team Vyn")
    if any(word in t for word in ["team", "tim", "klub"]):
        # Extract nama setelah keyword
        words = t.split()
        for i, word in enumerate(words):
            if word in ["team", "tim", "klub"] and i+1 < len(words):
                player_name = words[i+1]
                team = find_team_by_player(player_name)
                if team:
                    return team
    
    # 3. Cari player dulu, lalu ambil timnya
    player = find_player(text)
    if player:
        team_name = player.get("team", "").lower()
        if team_name in _team_index:
            return _team_index[team_name]
    
    return None

# ─── Deteksi Intent ──────────────────────────────────────────────────────────
def detect_intent(text: str) -> str:
    t = text.lower()
    
    # 1. Prioritas: Esports
    if any(w in t for w in ["pro player", "player", "pemain pro", "siapa saja di", "roster", "anggota tim"]):
        return "player"
    if any(w in t for w in ["tim", "team", "klub", "organisasi", "siapa tim"]):
        return "team"
    if any(w in t for w in ["m1", "mpl", "world championship", "turnamen", "juara", "champion", "runner up", "mvp", "prize", "hadiah", "statistik"]):
        return "tournament"

    # 2. Game Data
    if any(w in t for w in ["lore", "cerita", "kisah", "asal usul", "backstory", "sejarah"]): return "lore"
    if any(w in t for w in ["combo", "skill combo", "urutan skill", "cara main"]): return "combo"
    if any(w in t for w in ["counter", "kelemahan", "lemah terhadap", "countered", "melawan"]): return "counter"
    if any(w in t for w in ["build", "item apa", "rekomen item", "item terbaik", "emblem apa", "rekomendasi"]): return "item_build"
    if any(w in t for w in ["daftar hero", "list hero", "semua hero", "hero apa saja"]): return "hero_list"
    if any(w in t for w in ["item", "senjata", "equipment"]): return "item_info"
    if any(w in t for w in ["emblem", "talent"]): return "emblem_info"
    if any(w in t for w in ["siapa", "hero", "role", "lane", "specialty", "gambar", "foto", "lihat"]): return "hero_info"
    return "general"

# ─── Builder Jawaban ─────────────────────────────────────────────────────────
def build_player_answer(player: dict) -> str:
    return (
        f"👤 **Pro Player: {player['nickname']}**\n"
        f"- **Nama Asli:** {player.get('real_name', '-')}\n"
        f"- **Tim:** {player.get('team', '-')}\n"
        f"- **Role:** {player.get('role', '-')}\n"
        f"- **Hero Pool:** {', '.join(player.get('hero_pool', []))}\n"
        f"- **Signature Hero:** {player.get('signature_hero', '-')}\n"
        f"- **Achievements:** {', '.join(player.get('achievements', []))}\n"
        f"- **Win Rate:** {player.get('win_rate', 0)}% | **MVP Count:** {player.get('mvp_count', 0)}"
    )

def build_team_answer(team: dict, player_name: str = None) -> str:
    source = team.get("source", "ML")
    
    # Get players - handle both M1 and MPL format
    players_list = team.get("players", team.get("current_roster", []))
    players = ", ".join([f"{p['nickname']} ({p['role']})" for p in players_list])
    
    titles = ", ".join(team.get("championships", [])) or "Belum ada data championship"
    rank_info = f"\n- **Ranking M1:** #{team.get('final_rank', '-')}" if "final_rank" in team else ""
    prize = team.get('prize', team.get('achievements_summary', {}).get('total_prize_money', '-'))
    
    base_answer = (
        f"🏆 **Tim {team['team_name']}** ({source})\n"
        f"- **Coach:** {team.get('coach', '-')}\n"
        f"- **Roster:** {players}\n"
        f"- **Titles:** {titles}{rank_info}\n"
        f"- **Prize/Earnings:** {prize}"
    )
    
    # Jika user tanya via player name, tambahkan info player
    if player_name:
        player = find_player(player_name)
        if player:
            base_answer += f"\n\n👤 **{player_name}** adalah {player['role']} dari {team['team_name']}"
    
    return base_answer

def build_tournament_answer() -> str:
    info = m1_championship_data.get("tournament_info", {})
    awards = m1_championship_data.get("awards", {})
    mvp = awards.get("mvp_tournament", {})
    return (
        f"🌍 **{info.get('name', 'M1 World Championship')}**\n"
        f"- **Champion:** {info.get('champion', '-')}\n"
        f"- **Runner-up:** {info.get('runner_up', '-')}\n"
        f"- **Prize Pool:** {info.get('prize_pool', '-')}\n"
        f"- **MVP Tournament:** {mvp.get('player', '-')} ({mvp.get('team', '-')})\n"
        f"- **Total Tim:** {info.get('total_teams', '-')}\n"
        f"- **Lokasi:** {info.get('location', '-')}"
    )

# Game Data Builders
def get_hero_lore(hero_id: int) -> str | None:
    for item in lores_data.get("hero_lores", []):
        if item["hero_id"] == hero_id: return item.get("lore")
    return None

def get_hero_combo(hero_id: int) -> dict | None:
    for item in combos_data.get("hero_combos", []):
        if item["hero_id"] == hero_id: return item
    return None

def get_hero_counter(hero_id: int) -> dict | None:
    for item in counters_data.get("hero_counters", []):
        if item["hero_id"] == hero_id: return item
    return None

def get_hero_recommendation(hero_id: int) -> dict | None:
    for item in recommendations.get("hero_recommendations", []):
        if item["hero_id"] == hero_id: return item
    return None

def build_hero_info_answer(hero: dict) -> str:
    roles = ", ".join(hero.get("role", []))
    specialty = ", ".join(hero.get("specialty", []))
    lane = hero.get("lane", "-")
    return f"🦸 **{hero['name']}**\n- **Role:** {roles}\n- **Specialty:** {specialty}\n- **Lane:** {lane}\n"

def build_lore_answer(hero: dict) -> str:
    lore = get_hero_lore(hero["id"])
    title_info = ""
    for l in lores_data.get("hero_lores", []):
        if l["hero_id"] == hero["id"]:
            title_info = f" — *{l.get('title', '')}*"
            break
    if lore: return f"📖 **Lore {hero['name']}**{title_info}\n\n{lore}"
    return f"Maaf, lore untuk **{hero['name']}** belum tersedia."

def build_combo_answer(hero: dict) -> str:
    combo = get_hero_combo(hero["id"])
    if not combo: return f"Data combo untuk **{hero['name']}** belum tersedia."
    lines = [f"⚔️ **Combo {hero['name']}**\n", f"**Self Combo:**\n{combo.get('self_combo', '-')}\n"]
    for pair in combo.get("best_pair_combos", []):
        lines.append(f"🤝 **Pair dengan {pair['partner']}:**\n{pair['combo']}")
    lines.append(f"\n💡 **Tips:** {combo.get('tips', '-')}")
    return "\n".join(lines)

def build_counter_answer(hero: dict) -> str:
    counter = get_hero_counter(hero["id"])
    if not counter: return f"Data counter untuk **{hero['name']}** belum tersedia."
    return (f"🛡️ **Counter Info {hero['name']}**\n\n"
            f"**Dicounter oleh:** {', '.join(counter.get('countered_by', []))}\n*Alasan:* {counter.get('reason_countered', '-')}\n\n"
            f"**Mengcounter:** {', '.join(counter.get('counters', []))}\n*Alasan:* {counter.get('reason_counters', '-')}")

def build_build_answer(hero: dict) -> str:
    rec = get_hero_recommendation(hero["id"])
    if not rec: return f"Data build untuk **{hero['name']}** belum tersedia."
    items_list = "\n".join(f"  {i+1}. {item}" for i, item in enumerate(rec.get("recommended_items", [])))
    return (f"🔧 **Rekomendasi Build {hero['name']}**\n\n**Items:**\n{items_list}\n\n"
            f"**Emblem:** {rec.get('recommended_emblem', '-')}\n**Talent:** {rec.get('emblem_talent', '-')}\n\n💡 {rec.get('item_notes', '-')}")

def build_hero_list_answer() -> str:
    heroes = heroes_data.get("heroes", [])
    lines = ["📋 **Daftar 50 Hero MLBB:**\n"]
    roles_group: dict[str, list] = {}
    for h in heroes:
        primary_role = h["role"][0] if h.get("role") else "Other"
        roles_group.setdefault(primary_role, []).append(h["name"])
    for role, names in sorted(roles_group.items()):
        lines.append(f"**{role}:** {', '.join(names)}")
    return "\n".join(lines)

def build_item_info_answer(text: str) -> str:
    for item in items_data.get("items", []):
        if item["name"].lower() in text.lower():
            stats_str = ", ".join(f"{k}: {v}" for k, v in item.get("stats", {}).items())
            return (f"🗡️ **{item['name']}**\n- **Kategori:** {item.get('category', '-')}\n"
                    f"- **Stats:** {stats_str}\n- **Fungsi:** {item.get('function', '-')}\n"
                    f"- **Passive:** {item.get('passive', item.get('active', '-'))}")
    return "Maaf, informasi item tersebut tidak ditemukan."

def build_emblem_info_answer(text: str) -> str:
    for emb in emblems_data.get("emblems", []):
        if emb["name"].lower() in text.lower():
            talents = "\n".join(f"  - **{t['name']}:** {t['description']}" for t in emb.get("tier3_talents", []))
            return (f"💎 **{emb['name']}**\n- **Stats:** {', '.join(emb.get('primary_stats', []))}\n"
                    f"- **Fungsi:** {emb.get('function', '-')}\n- **Tier 3 Talents:**\n{talents}\n"
                    f"- **Hero yang cocok:** {', '.join(emb.get('recommended_heroes', []))}")
    return "Maaf, informasi emblem tersebut tidak ditemukan."

# ─── Main Query Function ─────────────────────────────────────────────────────
def query_rag(question: str) -> dict:
    intent = detect_intent(question)
    hero = detect_hero(question)
    image_path = None
    hero_data = None

    # 1. Handle Esports Intents
    if intent == "player":
        player = find_player(question)
        if player:
            # Tampilkan info player + timnya
            team_name = player.get("team", "")
            team = _team_index.get(team_name.lower())
            player_info = build_player_answer(player)
            team_info = f"\n\n🏆 **Tim:** {build_team_answer(team, player['nickname'])}" if team else ""
            ans = player_info + team_info
        else:
            ans = "❌ Pro player tidak ditemukan. Coba sebutkan nickname (contoh: Sanji, Kiboy, Lemon, R7)."
        return {"answer": ans, "image_path": None, "hero_name": None, "hero_data": None}

    if intent == "team":
        team = find_team(question)
        
        # Cek apakah user tanya "team [player_name]"
        player_mentioned = None
        words = question.lower().split()
        for i, word in enumerate(words):
            if word in ["team", "tim"] and i+1 < len(words):
                player_mentioned = words[i+1]
                break
        
        if team:
            ans = build_team_answer(team, player_mentioned)
        else:
            ans = "❌ Tim tidak ditemukan. Coba sebutkan nama tim (contoh: RRQ Hoshi, ONIC, EVOS)."
        return {"answer": ans, "image_path": None, "hero_name": None, "hero_data": None}

    if intent == "tournament":
        return {"answer": build_tournament_answer(), "image_path": None, "hero_name": None, "hero_data": None}

    # 2. Handle Game Data (tetap sama seperti sebelumnya)
    if hero:
        image_path = hero.get("image_path")
        hero_data = {"name": hero["name"], "role": hero.get("role", []), "specialty": hero.get("specialty", []), "lane": hero.get("lane", "")}

    if intent == "hero_list": answer = build_hero_list_answer()
    elif intent == "item_info": answer = build_item_info_answer(question)
    elif intent == "emblem_info": answer = build_emblem_info_answer(question)
    elif hero is None: answer = "Maaf, saya tidak menemukan data yang dimaksud. Coba sebutkan nama hero, item, atau pro player secara spesifik."
    elif intent == "lore": answer = build_lore_answer(hero)
    elif intent == "combo": answer = build_combo_answer(hero)
    elif intent == "counter": answer = build_counter_answer(hero)
    elif intent == "item_build": answer = build_build_answer(hero)
    else: answer = build_hero_info_answer(hero)

    return {"answer": answer, "image_path": image_path, "hero_name": hero["name"] if hero else None, "hero_data": hero_data}

# Alias untuk kompatibilitas dengan app.py
def generate_answer(query: str, history=None):
    res = query_rag(query)
    # Mapping ke format yang diharapkan app.py
    return {
        "answer": res["answer"],
        "retrieved_docs": [{"name": res.get("hero_name") or "General", "type": "info", "score": 0.9}]
    }