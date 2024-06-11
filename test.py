import json
from riotwatcher import LolWatcher, ApiError

with open('config.json', 'r') as config_file:
    config = json.load(config_file)

lol_watcher = LolWatcher(config['api_key'])

# riot id -> puuid -> summonerid -> stats

aka = { 
    "teadrinker3": "i'm just bad at the game",
    "acerd": "peaked d4 10 years ago",
    "moon9": "blind to his own mistakes",
    "practice improve": "most passive male player",
    "xanax": "allergic to good botlanes"
}

for k,v in config['summoner_ids'].items():
    #error handling...
    ranked_stats = lol_watcher.league.by_summoner("euw1", v)
    print(ranked_stats)
    soloq_stats = next(entry for entry in ranked_stats if entry['queueType'] == 'RANKED_SOLO_5x5')
    print(soloq_stats)
    games = soloq_stats["wins"] + soloq_stats["losses"]
    winrate = round(soloq_stats["wins"] / games * 100)

    print(f"Name: {k}")
    print(f"AKA {aka[k]}")
    print(f'Rank: {soloq_stats["tier"]} {soloq_stats["rank"]} {soloq_stats["leaguePoints"]}lp')
    print(f'Games: {games}')
    print(f'Winrate: {winrate}%')
