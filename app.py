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

def sort_leaderboard(data):
    print('uh')
    print(data)
    tiers = {'DIAMOND': 3, 'EMERALD': 2, 'PLATINUM': 1}
    ranks = {'IV': 1, 'III': 2, 'II': 3, 'I': 4}
    return (tiers.get(data['tier']) * 1000) + (ranks.get(data['rank']) * 100) + data['lp']


def fetch_data():

    summoners = config['summoner_ids'].items()

    processed_data = []
    for k,v in summoners:
        #error handling...
        ranked_stats = lol_watcher.league.by_summoner("euw1", v)
        soloq_stats = next(entry for entry in ranked_stats if entry['queueType'] == 'RANKED_SOLO_5x5')

        games = soloq_stats["wins"] + soloq_stats["losses"]
        winrate = round(soloq_stats["wins"] / games * 100)

        processed_item = {
            'name': k,
            'aka': aka[k],
            'tier': soloq_stats["tier"],
            'rank': soloq_stats["rank"],
            'lp': soloq_stats["leaguePoints"],
            'disp': f'{soloq_stats["tier"]} {soloq_stats["rank"]} {soloq_stats["leaguePoints"]}lp',
            'games': games,
            'winrate': winrate
        }

        processed_data.append(processed_item)

    return processed_data
    


@app.route('/')
def index():
    sorted_leaderboard = sorted(fetch_data(), key=sort_leaderboard, reverse=True)
    print(sorted_leaderboard)
    return render_template('index.html', data=sorted_leaderboard)

if __name__ == '__main__':
    app.run(debug=True)
    
