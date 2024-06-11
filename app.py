import json
from flask import Flask, render_template
from riotwatcher import LolWatcher, ApiError

app = Flask(__name__)

with open('config.json', 'r') as config_file:
    config = json.load(config_file)

lol_watcher = LolWatcher(config['api_key'])

aka = { 
    "teadrinker3": "i'm just bad at the game",
    "acerd": "peaked d4 10 years ago",
    "moon9": "blind to his own mistakes",
    "practice improve": "most passive male player",
    "xanax": "allergic to good botlanes"
}

# simple yet effective way of ordering ranks of players
def calc_player_rank_score(data):
    tiers = {'DIAMOND': 3, 'EMERALD': 2, 'PLATINUM': 1}
    ranks = {'IV': 1, 'III': 2, 'II': 3, 'I': 4}
    return (tiers.get(data['tier']) * 1000) + (ranks.get(data['rank']) * 100) + data['lp']

def get_stats():
    summoners = config['summoner_ids'].items()
    all_player_stats = []
    for name, summoner_id in summoners:
        try:
            # might contain both flex and soloq data
            ranked_stats = lol_watcher.league.by_summoner("euw1", summoner_id)
            soloq_stats = next(entry for entry in ranked_stats if entry['queueType'] == 'RANKED_SOLO_5x5')
            games = soloq_stats["wins"] + soloq_stats["losses"]
            winrate = round(soloq_stats["wins"] / games * 100)
            player_stats = {
                'name': name,
                'aka': aka[name],
                'tier': soloq_stats["tier"],
                'rank': soloq_stats["rank"],
                'lp': soloq_stats["leaguePoints"],
                'full_rank': f'{soloq_stats["tier"]} {soloq_stats["rank"]} {soloq_stats["leaguePoints"]}lp',
                'games': games,
                'winrate': winrate
            }
            all_player_stats.append(player_stats)
        except (ApiError, StopIteration) as e:
            print(f'Error fetching data for summoner {name}: {e}')
    return all_player_stats
    
@app.route('/')
def index():
    sorted_leaderboard = sorted(get_stats(), key=calc_player_rank_score, reverse=True)
    # the place of the players in the leaderboard
    for index, player in enumerate(sorted_leaderboard, start=1):
        player['place'] = index
    print(sorted_leaderboard)
    return render_template('index.html', data=sorted_leaderboard)

if __name__ == '__main__':
    app.run(debug=True)
    
