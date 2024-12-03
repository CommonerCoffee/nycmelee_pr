import time
import requests
from sgg_queries import *

# Classes
class TooManyRequestsError(Exception):
    # Means we're submitting too many requests
    pass

class ResponseError(Exception):
    # Unknown other error
    pass

class RequestError(Exception):
    # Bad request (normally means your key is wrong)
    pass

class ServerError(Exception):
    # Server error, not my fault
    pass

class NoIdeaError(Exception):
    # If you get this, please send this to me so I can figure it out lol
    pass

# Runs queries
def run_query(query, variables, header, auto_retry):
    # This helper function is necessary for TooManyRequestsErrors
    def _run_query(query, variables, header, auto_retry, seconds): 
        json_request = {'query': query, 'variables': variables}
        try:
            request = requests.post(url='https://api.smash.gg/gql/alpha', json=json_request, headers=header)
            if request.status_code == 400:
                raise RequestError
            elif request.status_code == 429:
                raise TooManyRequestsError
            elif 400 <= request.status_code < 500:
                raise ResponseError
            elif 500 <= request.status_code < 600:
                raise ServerError
            elif 300 <= request.status_code < 400:
                raise NoIdeaError

            response = request.json()
            return response

        except RequestError:
            print("Error 400: Bad request (probably means your key is wrong)")
            return
        except TooManyRequestsError:
            if auto_retry:
                print("Error 429: Sending too many requests right now, trying again in {} seconds".format(seconds))
                time.sleep(seconds)
                return _run_query(query, variables, header, auto_retry, seconds*2)
            else:
                print("Error 429: Sending too many requests right now")
                return
        except ResponseError:
            print("Error {}: Unknown request error".format(request.status_code))
            return
        except ServerError:
            print("Error {}: Unknown server error".format(request.status_code))
            return
        except NoIdeaError:
            print("Error {}: I literally have no idea how you got this status code, please send this to me".format(request.status_code))
            return

    return _run_query(query, variables, header, auto_retry, 10)

#Filters
def event_id_filter(response, event_name):
    if response['data']['tournament'] is None:
        return

    for event in response['data']['tournament']['events']:
        if event['slug'].split("/")[-1] == event_name:
            return event['id']

    return

# Filters for the show_players function
def show_entrants_filter(response):
    if response['data']['event'] is None:
        return

    if response['data']['event']['standings']['nodes'] is None:
        return
    
    entrants = []    # Need for return at the end
    
    for node in response['data']['event']['standings']['nodes']:
        cur_entrant = {}
        cur_entrant['entrantId'] = node['entrant']['id']
        cur_entrant['tag'] = node['entrant']['name']
        cur_entrant['finalPlacement'] = node['placement']
        if node['entrant']['seeds'] is None:
            cur_entrant['seed'] = -1
        else:
            cur_entrant['seed'] = node['entrant']['initialSeedNum']

        players = []
        for user in node['entrant']['participants']:
            cur_player = {}
            if user['player']['id'] is not None:
                cur_player['playerId'] = user['player']['id']
            else:
                cur_player['playerId'] = "None"
            cur_player['playerTag'] = user['player']['gamerTag']
            players.append(cur_player)
        cur_entrant['entrantPlayers'] = players

        entrants.append(cur_entrant)

    return entrants


# Filter for the show_sets function
def show_sets_filter(response):
    if 'data' not in response:
        return
    if response['data']['event'] is None:
        return

    if response['data']['event']['sets']['nodes'] is None:
        return
        
    
    sets = [] # Need for return at the end

    for node in response['data']['event']['sets']['nodes']:
        if len(node['slots']) < 2:
            continue # This fixes a bug where player doesn't have an opponent
        if (node['slots'][0]['entrant'] is None or node['slots'][1]['entrant'] is None):
            continue # This fixes a bug when tournament ends early

        cur_set = {}
        cur_set['id'] = node['id']
        cur_set['entrant1Id'] = node['slots'][0]['entrant']['id']
        cur_set['entrant2Id'] = node['slots'][1]['entrant']['id']
        cur_set['entrant1Name'] = node['slots'][0]['entrant']['name']
        cur_set['entrant2Name'] = node['slots'][1]['entrant']['name']

        if (node['games'] is not None):
            entrant1_chars = []
            entrant2_chars = []
            game_winners_ids = []
            for game in node['games']:
                if (game['selections'] is None): # This fixes an issue with selections being none while games are reported
                    continue
                elif (node['slots'][0]['entrant']['id'] == game['selections'][0]['entrant']['id']):
                    entrant1_chars.append(game['selections'][0]['selectionValue'])
                    if len(game['selections']) > 1:
                        entrant2_chars.append(game['selections'][1]['selectionValue'])
                else:
                    entrant2_chars.append(game['selections'][0]['selectionValue'])
                    if len(game['selections']) > 1:
                        entrant1_chars.append(game['selections'][1]['selectionValue'])
                    
                game_winners_ids.append(game['winnerId'])

            cur_set['entrant1Chars'] = entrant1_chars
            cur_set['entrant2Chars'] = entrant2_chars
            cur_set['gameWinners'] = game_winners_ids
        
        # Next 2 if/else blocks make sure there's a result in, sometimes DQs are weird
        # there also could be ongoing matches
        match_done = True
        if node['slots'][0]['standing'] is None:
            cur_set['entrant1Score'] = -1
            match_done = False
        elif node['slots'][0]['standing']['stats']['score']['value'] is not None:
            cur_set['entrant1Score'] = node['slots'][0]['standing']['stats']['score']['value']
        else:
            cur_set['entrant1Score'] = -1
        
        if node['slots'][1]['standing'] is None:
            cur_set['entrant2Score'] = -1
            match_done = False
        elif node['slots'][1]['standing']['stats']['score']['value'] is not None:
            cur_set['entrant2Score'] = node['slots'][1]['standing']['stats']['score']['value']
        else:
            cur_set['entrant2Score'] = -1

        # Determining winner/loser (elif because sometimes smashgg won't give us one)
        if match_done:
            cur_set['completed'] = True
            if node['slots'][0]['standing']['placement'] == 1:
                cur_set['winnerId'] = cur_set['entrant1Id']
                cur_set['loserId'] = cur_set['entrant2Id']
                cur_set['winnerName'] = cur_set['entrant1Name']
                cur_set['loserName'] = cur_set['entrant2Name']
            elif node['slots'][0]['standing']['placement'] == 2:
                cur_set['winnerId'] = cur_set['entrant2Id']
                cur_set['loserId'] = cur_set['entrant1Id']
                cur_set['winnerName'] = cur_set['entrant2Name']
                cur_set['loserName'] = cur_set['entrant1Name']
        else:
            cur_set['completed'] = False

        cur_set['fullRoundText'] = node['fullRoundText']

        if node['phaseGroup'] is not None:
            cur_set['bracketName'] = node['phaseGroup']['phase']['name']
            cur_set['bracketId'] = node['phaseGroup']['id']
        else:
            cur_set['bracketName'] = None
            cur_set['bracketId'] = None

        # This gives player_ids, but it also is made to work with team events
        for j in range(0, 2):
            players = []
            for user in node['slots'][j]['entrant']['participants']:
                cur_player = {}
                if user['player'] is not None:
                    cur_player['playerId'] = user['player']['id']
                    cur_player['playerTag'] = user['player']['gamerTag']
                    if user['entrants'] is not None:
                        cur_player['entrantId'] = user['entrants'][0]['id']
                    else:
                        cur_player['entrantId'] = node['slots'][j]['entrant']['id']
                    players.append(cur_player)
                else:
                    cur_player['playerId'] = None
                    cur_player['playerTag'] = None
                    cur_player['entrantId'] = node['slots'][j]['entrant']['id']
            
            cur_set['entrant' + str(j+1) + 'Players'] = players

        sets.append(cur_set) # Adding that specific set onto the large list of sets

    return sets

# Helper function to get an eventId from a tournament
def get_event_id(tournament_name, event_name, header, auto_retry):
    variables = {"tourneySlug": tournament_name}
    response = run_query(EVENT_ID_QUERY, variables, header, auto_retry)
    data = event_id_filter(response, event_name)
    return data


# Shows all the sets from an event 
def show_sets(tournament_name, event_name, page_num, header, auto_retry):
    event_id = get_event_id(tournament_name, event_name, header, auto_retry)
    variables = {"eventId": event_id, "page": page_num}
    response = run_query(SHOW_SETS_QUERY, variables, header, auto_retry)
    data = show_sets_filter(response)
    return data
            
# Shows all entrants from a specific event
def show_entrants(tournament_name, event_name, page_num, header, auto_retry):
    event_id = get_event_id(tournament_name, event_name, header, auto_retry)
    variables = {"eventId": event_id, "page": page_num}
    response = run_query(SHOW_ENTRANTS_QUERY, variables, header, auto_retry)
    data = show_entrants_filter(response)
    return data