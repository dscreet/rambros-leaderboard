import json
from flask import Flask, render_template
from flask_caching import Cache
from riotwatcher import LolWatcher, ApiError

app = Flask(__name__)
# SimpleCache is sufficient for this app
cache = Cache(app, config={'CACHE_TYPE': 'SimpleCache', 'CACHE_DEFAULT_TIMEOUT': 300})

with open('config.json', 'r') as config_file:
    config = json.load(config_file)

lol_watcher = LolWatcher(config['api_key'])

# this api call takes long so caching is used
# reduces time from 0.1s per call to 0.
@cache.memoize(timeout=3600)  # result is cached for an hour
def get_match_details(match_id):
    return lol_watcher.match.by_id("euw1", match_id)

# given a game and a player -> returns if that player won
def get_match_outcome(name, match_id):
    match = get_match_details(match_id)
    participants = match['info']['participants']
    for player in participants:
        if player['summonerId'] == config['summoner_ids'][name]:
            return player['win']
    return None

# returns the win/loss streak of a player
def calc_streak(name, match_history):
    if not match_history:
        return None, 0
    streak_type = None
    current_streak = 0
    for match in match_history:
        match_won = get_match_outcome(name, match)
        if streak_type is None:
            streak_type = 'W' if match_won else 'L'
        if match_won and streak_type == 'W':
            current_streak += 1
        elif not match_won and streak_type == 'L':
            current_streak += 1
        else:
            break
    return streak_type, current_streak

# simple yet effective way of ordering ranks of players
def calc_player_rank_score(data):
    tiers = {'DIAMOND': 3, 'EMERALD': 2, 'PLATINUM': 1}
    ranks = {'IV': 1, 'III': 2, 'II': 3, 'I': 4}
    return (tiers.get(data['tier']) * 1000) + (ranks.get(data['rank']) * 100) + data['lp']

# fetches and processes all the data for players to be used in the table
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
            match_history = lol_watcher.match.matchlist_by_puuid("euw1", config['puuids'][name], queue=420)
            streak = calc_streak(name, match_history)
            player_stats = {
                'name': name,
                'aka': config['aka'][name],
                'tier': soloq_stats["tier"],
                'rank': soloq_stats["rank"],
                'lp': soloq_stats["leaguePoints"],
                'full_rank': f'{soloq_stats["tier"]} {soloq_stats["rank"]} {soloq_stats["leaguePoints"]}lp',
                'games': games,
                'winrate': winrate,
                'streak': f'{streak[1]} {streak[0]}'
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
    return render_template('index.html', data=sorted_leaderboard)

if __name__ == '__main__':
    app.run(debug=True)
    
