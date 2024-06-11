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
            'rank': f'{soloq_stats["tier"]} {soloq_stats["rank"]} {soloq_stats["leaguePoints"]}lp',
            'games': games,
            'winrate': winrate
        }

        processed_data.append(processed_item)
    
    print(processed_data)

    return processed_data
    


@app.route('/')
def index():
    return render_template('index.html', data=fetch_data())

if __name__ == '__main__':
    app.run(debug=True)
    
