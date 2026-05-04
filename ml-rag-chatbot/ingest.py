"""
ingest.py — Membangun knowledge base dari semua file JSON di folder /data
Termasuk: Hero, Item, Emblem, Combo, Counter, Rekomendasi, Lore, MPL Players, M1 Championship
Jalankan sekali: python ingest.py
Output: knowledge_base.pkl
"""

import json
import pickle
import os
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
OUTPUT   = Path(__file__).parent / "knowledge_base.pkl"

# ─── Load semua JSON ──────────────────────────────────────────────────────────

def load_json(filename):
    path = DATA_DIR / filename
    if not path.exists():
        print(f"[SKIP] {filename} tidak ditemukan")
        return {}
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"[OK]   {filename} dimuat")
    return data

# ─── Flatten semua data menjadi list dokumen teks ─────────────────────────────

def build_documents(heroes, items, emblems, combos, counters, recommendations, lores, mpl_players=None, m1_championship=None, mpl_teams=None):
    docs = []

    # 1. Heroes
    for h in heroes.get("heroes", []):
        roles     = ", ".join(h.get("role", []))
        specialty = ", ".join(h.get("specialty", []))
        docs.append({
            "id":   f"hero_{h['id']}",
            "type": "hero_info",
            "text": (
                f"Hero: {h['name']}. "
                f"Role: {roles}. "
                f"Specialty: {specialty}. "
                f"Lane: {h.get('lane', '-')}."
            )
        })

    # 2. Items
    for item in items.get("items", []):
        stats_str = ", ".join(f"{k} {v}" for k, v in item.get("stats", {}).items())
        docs.append({
            "id":   f"item_{item['id']}",
            "type": "item",
            "text": (
                f"Item: {item['name']}. "
                f"Kategori: {item.get('category', '-')}. "
                f"Stats: {stats_str}. "
                f"Fungsi: {item.get('function', '-')}. "
                f"Passive/Active: {item.get('passive', item.get('active', '-'))}."
            )
        })

    # 3. Emblems
    for emb in emblems.get("emblems", []):
        talents_text = "; ".join(
            f"{t['name']}: {t['description']}"
            for t in emb.get("tier3_talents", [])
        )
        docs.append({
            "id":   f"emblem_{emb['id']}",
            "type": "emblem",
            "text": (
                f"Emblem: {emb['name']}. "
                f"Stats utama: {', '.join(emb.get('primary_stats', []))}. "
                f"Fungsi: {emb.get('function', '-')}. "
                f"Talents: {talents_text}. "
                f"Hero cocok: {', '.join(emb.get('recommended_heroes', []))}."
            )
        })

    # 4. Combos
    for c in combos.get("hero_combos", []):
        pair_text = "; ".join(
            f"Pair dengan {p['partner']}: {p['combo']}"
            for p in c.get("best_pair_combos", [])
        )
        docs.append({
            "id":   f"combo_{c['hero_id']}",
            "type": "combo",
            "text": (
                f"Combo hero {c['hero_name']}: {c.get('self_combo', '-')}. "
                f"Best pair combos: {pair_text}. "
                f"Tips: {c.get('tips', '-')}."
            )
        })

    # 5. Counters
    for ct in counters.get("hero_counters", []):
        docs.append({
            "id":   f"counter_{ct['hero_id']}",
            "type": "counter",
            "text": (
                f"Counter hero {ct['hero_name']}: "
                f"Dicounter oleh {', '.join(ct.get('countered_by', []))}. "
                f"Alasan: {ct.get('reason_countered', '-')}. "
                f"Mengcounter: {', '.join(ct.get('counters', []))}. "
                f"Alasan: {ct.get('reason_counters', '-')}."
            )
        })

    # 6. Recommendations
    for r in recommendations.get("hero_recommendations", []):
        items_list = ", ".join(r.get("recommended_items", []))
        docs.append({
            "id":   f"rec_{r['hero_id']}",
            "type": "recommendation",
            "text": (
                f"Rekomendasi build {r['hero_name']}: "
                f"Items: {items_list}. "
                f"Emblem: {r.get('recommended_emblem', '-')}. "
                f"Talent: {r.get('emblem_talent', '-')}. "
                f"Catatan: {r.get('item_notes', '-')}."
            )
        })

    # 7. Lores
    for l in lores.get("hero_lores", []):
        docs.append({
            "id":   f"lore_{l['hero_id']}",
            "type": "lore",
            "text": (
                f"Lore {l['hero_name']} ({l.get('title', '')}): "
                f"{l.get('lore', '-')}"
            )
        })

    # 8. MPL Players (BARU)
    if mpl_players:
        for p in mpl_players.get("mpl_players", []):
            hero_pool = ", ".join(p.get("hero_pool", []))
            achievements = ", ".join(p.get("achievements", []))
            docs.append({
                "id":   f"mpl_player_{p['player_id']}",
                "type": "mpl_player",
                "text": (
                    f"Pro Player: {p['nickname']} ({p['real_name']}). "
                    f"Tim: {p['team']}. "
                    f"Role: {p['role']}. "
                    f"Negara: {p['country']}. "
                    f"Umur: {p['age']} tahun. "
                    f"Hero Pool: {hero_pool}. "
                    f"Signature Hero: {p.get('signature_hero', '-')}. "
                    f"Achievements: {achievements}. "
                    f"Win Rate: {p.get('win_rate', 0)}%. "
                    f"Total Matches: {p.get('total_matches', 0)}. "
                    f"MVP Count: {p.get('mvp_count', 0)}."
                )
            })

    # 9. M1 World Championship (BARU)
    if m1_championship:
        # Info Tournament
        tourney = m1_championship.get("tournament_info", {})
        docs.append({
            "id":   "m1_tournament_info",
            "type": "m1_tournament",
            "text": (
                f"Tournament: {tourney.get('name', 'M1 World Championship')}. "
                f"Tahun: {tourney.get('year', 2019)}. "
                f"Tanggal: {tourney.get('dates', '-')}. "
                f"Lokasi: {tourney.get('location', '-')}. "
                f"Prize Pool: {tourney.get('prize_pool', '-')}. "
                f"Champion: {tourney.get('champion', '-')}. "
                f"Runner-up: {tourney.get('runner_up', '-')}. "
                f"MVP Award: {tourney.get('mvp_award', '-')}. "
                f"Total Tim: {tourney.get('total_teams', 16)}."
            )
        })

        # Data Tim
        for team in m1_championship.get("teams", []):
            players_list = "; ".join(
                f"{pl['nickname']} ({pl['role']})"
                for pl in team.get("players", [])
            )
            docs.append({
                "id":   f"m1_team_{team['team_id']}",
                "type": "m1_team",
                "text": (
                    f"Tim M1: {team['team_name']} ({team['country']}). "
                    f"Ranking: {team['final_rank']}. "
                    f"Prize: {team['prize']}. "
                    f"Coach: {team.get('coach', '-')}. "
                    f"Players: {players_list}. "
                    f"Win Rate: {team.get('win_rate', 0)}%. "
                    f"Matches: {team.get('matches_played', 0)}."
                )
            })

        # Statistik M1
        stats = m1_championship.get("statistics", {})
        if stats:
            most_picked = "; ".join(
                f"{h['hero']} ({h['picks']} picks, {h['win_rate']}% WR)"
                for h in stats.get("most_picked_heroes", [])
            )
            most_banned = ", ".join(
                f"{h['hero']} ({h['bans']} bans)"
                for h in stats.get("most_banned_heroes", [])
            )
            docs.append({
                "id":   "m1_statistics",
                "type": "m1_stats",
                "text": (
                    f"M1 Statistics: "
                    f"Total Matches: {stats.get('total_matches', 0)}. "
                    f"Most Picked Heroes: {most_picked}. "
                    f"Most Banned Heroes: {most_banned}. "
                    f"Avg Match Duration: {stats.get('average_match_duration', '-')}. "
                    f"Longest Match: {stats.get('longest_match', '-')}. "
                    f"Shortest Match: {stats.get('shortest_match', '-')}."
                )
            })

        # Awards M1
        awards = m1_championship.get("awards", {})
        if awards:
            awards_text = []
            for award_key, award_data in awards.items():
                if isinstance(award_data, dict):
                    player = award_data.get("player", "")
                    team = award_data.get("team", "")
                    award_name = award_key.replace("_", " ").title()
                    awards_text.append(f"{award_name}: {player} ({team})")
            
            docs.append({
                "id":   "m1_awards",
                "type": "m1_awards",
                "text": f"M1 Awards: {'. '.join(awards_text)}."
            })

    # 10. MPL Teams (BARU)
    if mpl_teams:
        for team in mpl_teams.get("mpl_teams", []):
            roster = "; ".join(
                f"{pl['nickname']} ({pl['role']})"
                for pl in team.get("current_roster", [])
            )
            championships = ", ".join(team.get("championships", []))
            docs.append({
                "id":   f"mpl_team_{team['team_id']}",
                "type": "mpl_team",
                "text": (
                    f"Tim MPL: {team['team_name']}. "
                    f"Organisasi: {team.get('organization', '-')}. "
                    f"Didirikan: {team.get('founded', '-')}. "
                    f"Coach: {team.get('coach', '-')}. "
                    f"Championships: {championships}. "
                    f"Total Titles: {team.get('total_titles', 0)}. "
                    f"Roster: {roster}. "
                    f"Total Prize: {team.get('achievements_summary', {}).get('total_prize_money', '-')}."
                )
            })

    return docs


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("=" * 50)
    print("  MLBB RAG — Ingest Knowledge Base")
    print("=" * 50)

    heroes          = load_json("heroes.json")
    items           = load_json("items.json")
    emblems         = load_json("emblems.json")
    combos          = load_json("combos.json")
    counters        = load_json("counters.json")
    recommendations = load_json("recommendations.json")
    lores           = load_json("lores.json")
    
    # Load data baru (optional)
    mpl_players     = load_json("mpl_players.json")
    m1_championship = load_json("m1_world_championship.json")
    mpl_teams       = load_json("mpl_teams.json")

    docs = build_documents(
        heroes, items, emblems, combos, counters, recommendations, lores,
        mpl_players=mpl_players,
        m1_championship=m1_championship,
        mpl_teams=mpl_teams
    )

    print(f"\n[INFO] Total dokumen: {len(docs)}")
    
    # Hitung dokumen per tipe
    type_counts = {}
    for doc in docs:
        doc_type = doc["type"]
        type_counts[doc_type] = type_counts.get(doc_type, 0) + 1
    
    print("[INFO] Breakdown:")
    for dtype, count in sorted(type_counts.items()):
        print(f"  - {dtype}: {count}")

    with open(OUTPUT, "wb") as f:
        pickle.dump(docs, f)

    print(f"[DONE] Knowledge base disimpan ke: {OUTPUT}")
    print("=" * 50)


if __name__ == "__main__":
    main()