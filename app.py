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
    match = lol_watcher.match.by_id("euw1", match_id)
    return match['info']['participants']

# batch process matches
def process_matches(match_history):
    processed_data = {}
    for match_id in match_history:
        if match_id not in processed_data:
            processed_data[match_id] = get_match_details(match_id)
    return processed_data

# given a game and a player -> returns if that player won
def get_match_outcome(name, match):
    for player in match:
        if player['summonerId'] == config['summoner_ids'][name]:
            return player['win']
    return None

# returns the win/loss streak of a player
def calc_streak(name, player_matches):
    if not player_matches:
        return None, 0
    streak_type = None
    current_streak = 0
    for match in player_matches.values():
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

# returns the amount of times the player's bot lane has died in a given game
def get_bot_lane_deaths(name, match):
    player_team = None
    bot_lane_deaths = 0
    for player in match:
        if player['summonerId'] == config['summoner_ids'][name]:
            player_team = player['teamId']
            break
    if player_team is not None:
        bot_lane_deaths = sum(player['deaths'] for player in match 
                              if player['lane'] == 'BOTTOM' and player['teamId'] == player_team)
    return bot_lane_deaths

# returns the average number of bot lane deaths in the player's team from the last 10 games
def calc_avg_bot_lane_deaths(name, player_matches):
    if not player_matches:
        return 0
    total_bot_lane_deaths = sum(get_bot_lane_deaths(name, match) for match in player_matches.values())
    avg_bot_lane_deaths = total_bot_lane_deaths / len(player_matches)
    return avg_bot_lane_deaths

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
            processed_player_matches = process_matches(match_history[:10])
            streak = calc_streak(name, processed_player_matches)
            avg_bot_lane_deaths = calc_avg_bot_lane_deaths(name, processed_player_matches)
            player_stats = {
                'name': name,
                'aka': config['aka'][name],
                'tier': soloq_stats["tier"],
                'rank': soloq_stats["rank"],
                'lp': soloq_stats["leaguePoints"],
                'full_rank': f'{soloq_stats["tier"]} {soloq_stats["rank"]} {soloq_stats["leaguePoints"]} LP',
                'games': games,
                'winrate': winrate,
                'streak': f'{streak[1]} {streak[0]}',
                'avg_bot_lane_deaths': avg_bot_lane_deaths
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
    
