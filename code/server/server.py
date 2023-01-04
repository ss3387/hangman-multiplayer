from flask_socketio import SocketIO, send, join_room, leave_room
from flask import Flask , request
from data import words
import os, uuid, random, re, time

def newPuzzle():

    timer(3, 'w_puzzle')

    for player in players.values():
        player['tries'] = 7
        player['time'] = None
        player['letters_guessed'] = 0
        player['guessed_wrong'] = False
        player['guessed_right'] = False
        player['guessed_first'] = False

    gameData['theme'] = random.choice(list(words.keys()))
    gameData['word'] = random.choice(words[gameData['theme']])
    gameData['word_length'] = len(gameData['word'].replace(' ', ''))
    gameData['split_word'] = re.split(r"([- '])", gameData['word'])
    gameData['actual_split_word'] = re.split(r"([- '])", gameData['word'])
    gameData['display_split_word'] = re.split(r"([- '])", gameData['word'])
    gameData['start_time'] = time.time()
    gameData['puzzle_number'] += 1
    gameData['puzzle_ended'] = False
    gameData['puzzle_time'] = 10 + gameData['word_length']*10

    for w in range(len(gameData['split_word'])):
        if gameData['split_word'][w] != "-" and gameData['split_word'][w] != "'" and gameData['split_word'][w] != ' ':
            gameData['split_word'][w] = '_  '*len(gameData['split_word'][w])
            gameData['display_split_word'][w] = '  '.join([*gameData['display_split_word'][w]])
        else:
            gameData['split_word'][w] = '  ' + gameData['split_word'][w] + '  '
            gameData['display_split_word'][w] = '  ' + gameData['display_split_word'][w] + '  '
       
    for player in players:
        players[player]['split_word'] = gameData['split_word'][:]
        data = {
            **players[player], 
            'type': 'new_puzzle',
            'theme': gameData['theme'],
            'puzzle_number': gameData['puzzle_number']
        }
        send(data, room=player)
    
    update_standings()

    if gameData['game_started']:
        timer(gameData['puzzle_time'], 'puzzle')

def update_standings():
    standings = []
    for p in list(players.values()):
        if p['guessed_right']:
            standings.append([p['name'], p['score'], '✓'])
        elif p['guessed_wrong']:
            standings.append([p['name'], p['score'], '𐄂'])
        else:
            standings.append([p['name'], p['score'], f"{p['letters_guessed']}/{gameData['word_length']}"])
    standings = sorted(standings, key=lambda x: x[1], reverse=True)
    send({'type': 'leaderboard_update', 'standings': standings}, room=gameData['game_id'])

def timer(secs: int, key: str):
    for s in range(secs):
        if gameData['puzzle_ended'] and key == 'puzzle':
            return
        send({'type': 'time_update', 'time': secs - s, 'keyword': key, 'total': secs, 'winners': winners()}, room=gameData['game_id'])
        time.sleep(1)
    if key == 'puzzle':
        calculate_scores()

def calculate_scores():
    gameData['puzzle_ended'] = True
    for player in players.values():
        player['score'] += player['letters_guessed']*10
        if player['guessed_first']: player['score'] += 50
        if player['guessed_right']: player['score'] += 100 + player['tries']*20
        if player['time']: player['score'] += int(gameData['puzzle_time'] - player['time'])
    send({'type': 'split_word_update', 'split_word': gameData['display_split_word']}, room=gameData['game_id'])
    update_standings()
    if gameData['puzzle_number'] == 5: 
        gameData['puzzle_number'] = 0
        
        timer(secs=15, key='round')
        for player in players.values():
            player['score'] = 0
    newPuzzle()

def winners():
    scores = [p['score'] for p in players.values()]
    highest_score = max(scores)
    winning_players = [p['name'] for p in players.values() if p['score'] == highest_score]
    return ', '.join(winning_players)


app = Flask(__name__)
app.secret_key = os.urandom(24)
socketio = SocketIO(app, manage_session=False)

players = {}
gameData = {'game_id': str(uuid.uuid4().fields[-1])[: 5], 'game_started': False, 'puzzle_ended': False}

@socketio.on('message')
def handle_message(msg):
    global gameData

    player_id = request.sid

    if msg['type'] == 'join' and len(players) <= 10:

        players[player_id] = {
            'player_id': player_id,
            'name': msg['name'],
            'tries': 7,
            'score': 0,
            'time': None,
            'letters_guessed': 0,
            'guessed_wrong': False,
            'guessed_right': False,
            'guessed_first': False
        }
        join_room(gameData['game_id'], player_id)
    
        if len(players) == 2 and not gameData['game_started']:
            gameData['game_started'] = True
            gameData['puzzle_number'] = 0
            newPuzzle()
            
        
        if len(players) > 2:
            players[player_id]['split_word'] = gameData['split_word'][:]
            data = {
                **players[player_id], 
                'type': 'new_puzzle',
                'theme': gameData['theme'],
                'puzzle_number': gameData['puzzle_number']
            }
            send(data, room=player_id)
            update_standings()
        
        
    
    
    if msg['type'] == 'guess' and gameData['game_started'] and not(players[player_id]['guessed_right'] or players[player_id]['guessed_wrong'] or gameData['puzzle_ended']):
        data_to_send = msg
        csw = players[player_id]['split_word']
        has_at_least_one_match = False
        for i in range(len(gameData['actual_split_word'])):
            matches = [i for i, letter in enumerate(gameData['actual_split_word'][i]) if letter == msg['guess']]
            for m in matches:
                csw[i] = csw[i].replace(' ', '')
                csw[i] = csw[i][:m] + msg['guess'] + csw[i][m+1:]
                csw[i] = '  '.join(list(csw[i]))
                players[player_id]['letters_guessed'] += 1
                has_at_least_one_match = True
    
        players[player_id]['split_word'] = csw
        if has_at_least_one_match: 
            data_to_send['guessed'] = True
        else:
            players[player_id]['tries'] -= 1
            data_to_send['guessed'] = False
        if players[player_id]['tries'] == 0: 
            players[player_id]['guessed_wrong'] = True
        if not '_' in ''.join(players[player_id]['split_word']):
            players[player_id]['guessed_right'] = True
            players[player_id]['time'] = time.time() - gameData['start_time']
        send({**data_to_send, **players[player_id]}, room=player_id)
        update_standings()
        if all(player['guessed_wrong'] or player['guessed_right'] for player in players.values()):
            calculate_scores()
        #send({'type': 'leaderboard_update', **players}, room=gameData['game_id'])

    if msg['type'] == 'quit':
        players.pop(player_id)
        leave_room(gameData['game_id'], player_id)
        update_standings()
        if len(players) == 0:
            gameData['game_started'] = False

socketio.run(app, host='0.0.0.0', port=8080, debug = True) # Run socketio app
