import os
import random
from logging import log
from flask import Flask, request, session, g, redirect, url_for, jsonify, abort, render_template
from sqlite3 import dbapi2 as sqlite3
from contextlib import closing
import json

app = Flask(__name__)

app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'war_room.db'),
    SECRET_KEY='8bithistory',
    USERNAME='admin',
    PASSWORD='rawrwar',
))

app.config.from_envvar('WAR_ROOM_SETTINGS', silent=True)

@app.route('/')
def hello():
    return render_template('game.html');

@app.route('/getUpdates/<username>')
def getUpdates(username):
    players = getPlayers()
    hand = getHand(username)
    return json.dumps({"players":players, "hand":hand})

@app.route('/register/<username>')
def register(username):
    if len(getPlayers()) == 4:
        abort(400)
    return addPlayer(username)

@app.route('/start')
def startGame():
    nextTurn()

@app.route('/move', methods=['POST'])
def move():
    user = request.form['user']
    card_idx = request.form['card_idx']
    target_name = request.form['target']
    round_num = getCurrentRound()

    cur = g.db.execute('select * from moves where player_id=? and round=?', [getPlayerId(user), round_num])
    if len(cur.fetchall()) == 3:
        abort(400)

    card_id = getCardByIndex(card_idx)
    target_id = getPlayerId(target_name)
    addMove(user, card_id, target, round_num)
    if len(getCurrentRoundMoves()) == len(getPlayers()*3):
        resolveTurn()

def resolveTurn():
    for move in getCurrentRoundMoves():
        card = getCard(move["card_id"])
        damage = card["power"] * 100000
        setPlayerPopulation(getPlayerPopulation(move['target']) - damage)
    nextTurn()

@app.route('/tableFlip')
def reset():
    init_db()
    return "Success"

def nextTurn():
    g.db.execute('insert into round (foo) values ("bar")')
    g.db.commit()
    clearHands()
    drawCards()
    return "Success"

def getPlayerPopulation(player_id):
    return g.db.execute('select population from players where id = ?', [player_id]).fetchall()[0]

def setPlayerPopulation(player_id, population):
    g.db.execute('update players set population=? where id=?', [population, player_id])
    g.db.commit()

def getHand(username):
    cur = g.db.execute('select card_id from players_cards join players on players_cards.player_id=players.id where players.name=?', [username])
    cards = [row[0] for row in cur.fetchall()]
    return cards

def getPlayers():
    cur = g.db.execute('select country, population from players order by id desc')
    players = [{'name':row[0],'pop':row[1]} for row in cur.fetchall()]
    return players

def getMoves():
    cur=g.db.execute('select * from moves order by id desc')
    return cur.fetchall()

def getCurrentRoundMoves():
    return g.db.execute('select * from moves where round = ? order by id desc', [getCurrentRound()]).fetchall()

def addMove(user, card_id, target, round_num):
    g.db.execute('insert into moves (player_id, card_id, target_id, round) values (?, ?, ?, ?)', [user, card_id, target, round_num])
    g.db.commit()

def addPlayer(username, population=2000000):
    if len(getMoves()) > 0:
        abort(400)
    cur = g.db.execute('select * from players where name=?', [username])
    if len(cur.fetchall()) > 0:
        abort(400)
    names = ["Somethingland", "Newtopia", "Oldtopia", "Empireland"]
    country = names[len(getPlayers())]
    g.db.execute('insert into players (name, population, country) values (?, ?, ?)', [username, population, country])
    g.db.commit()
    return country

def getPlayerId(username):
    cur = g.db.execute('select id from players where name=?', [username])
    return cur.fetchall()[0]['id']

def getRounds():
    return g.db.execute('select * from round order by id desc').fetchall()

def getCurrentRound():
    return len(getRounds())

def drawCards():
    cur = g.db.execute('select id from players')
    for player in cur.fetchall():
        player_id = player["id"]
        addCard(getRandomAttackCard(), player_id)
        addCard(getRandomAttackCard(), player_id)
        addCard(getRandomBuffCard(), player_id)

def addCard(card_id, player_id):
    g.db.execute('insert into players_cards (card_id, player_id) values (?, ?)', [card_id, player_id])
    g.db.commit()

def getCard(card_id):
    with open(os.path.join(app.root_path, 'cards.json')) as data_file:
        cards = json.load(data_file)[cardType]
        for card in cards:
            if card['id'] == card_id:
                return card

def clearHands():
    g.db.execute('delete from players_cards')
    g.db.commit()

def getRandomAttackCard():
    return getRandomCard("attack")

def getRandomBuffCard():
    return getRandomCard("buff")

def getRandomCard(cardType):
    with open(os.path.join(app.root_path, 'cards.json')) as data_file:
        cards = json.load(data_file)[cardType]
        card_index = random.randint(1,len(cards))-1
        return cards[card_index]["id"]

def connect_db():
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv

def init_db():
    with closing(connect_db()) as db:
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db

@app.before_request
def before_request():
    g.db = connect_db()

@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqli

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

if __name__ == '__main__':
    app.run(debug=True, use_debugger=False, use_reloader=False)
    init_db()
