from flask_socketio import SocketIO, send, join_room, leave_room
from flask import Flask , request
from data import words
import os, uuid, random, re, time

def newPuzzle():
    gameData['theme'] = random.choice(list(words.keys()))
    gameData['word'] = random.choice(words[gameData['theme']])
    gameData['word_length'] = len(gameData['word'].replace(' ', ''))
    gameData['split_word'] = re.split(r"([- '])", gameData['word'])
    gameData['actual_split_word'] = re.split(r"([- '])", gameData['word'])
    gameData['start_time'] = time.time()
    gameData['puzzle_number'] += 1
    for w in range(len(gameData['split_word'])):
        if gameData['split_word'][w] != "-" and gameData['split_word'][w] != "'" and gameData['split_word'][w] != ' ':
            gameData['split_word'][w] = '_  '*len(gameData['split_word'][w])
        else:
            gameData['split_word'][w] = '  ' + gameData['split_word'][w] + '  '

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

app = Flask(__name__)
app.secret_key = os.urandom(24)
socketio = SocketIO(app, manage_session=False)

players = {}
gameData = {'game_id': str(uuid.uuid4().fields[-1])[: 5], 'game_started': False}

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
            'letters_guessed': 0,
            'guessed_wrong': False,
            'guessed_right': False
        }
        join_room(gameData['game_id'], player_id)
    
        if len(players) == 2 and not gameData['game_started']:
            gameData['game_started'] = True
            gameData['puzzle_number'] = 0
            newPuzzle()
            player1 = list(players.keys())[0]
            players[player1]['split_word'] = gameData['split_word'][:]
            data = {
                **players[player1], 
                'type': 'new_puzzle',
                'theme': gameData['theme'],
                'puzzle_number': gameData['puzzle_number']
            }
            send(data, room=player1)
        
        if len(players) >= 2:
            players[player_id]['split_word'] = gameData['split_word'][:]
            data = {
                **players[player_id], 
                'type': 'new_puzzle',
                'theme': gameData['theme'],
                'puzzle_number': gameData['puzzle_number']
            }
            send(data, room=player_id)
            update_standings()
    
    
    if msg['type'] == 'guess' and gameData['game_started'] and not(players[player_id]['guessed_right'] or players[player_id]['guessed_wrong']):
        print(msg['guess'])
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
        #send({'type': 'leaderboard_update', **players}, room=gameData['game_id'])

    if msg['type'] == 'quit':
        print(players[player_id], 'quits the game')
        players.pop(player_id)
        leave_room(gameData['game_id'], player_id)
        update_standings()
        if len(players) == 0:
            gameData['game_started'] = False





socketio.run(app, host='0.0.0.0', port=8080, debug = True) # Run socketio app