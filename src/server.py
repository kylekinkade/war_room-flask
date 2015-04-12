import os
import random
from logging import log
from flask import Flask, request, session, g, redirect, url_for, jsonify, abort
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
    return "Hello there! c:"

@app.route('/getUpdates/<username>')
def getUpdates(username):
    cur = g.db.execute('select name, population from players order by id desc')
    players = [{'name':row[0],'pop':row[1]} for row in cur.fetchall()]
    return jsonify(players=players)

@app.route('/register/<username>')
def register(username):
    addPlayer(username)
    return "Success"

@app.route('/getHand/<username>')
def getHand(username):
    cur = g.db.execute('select card_id from players_cards where name=?', [username])
    cards = [jsonify(card_id, row[0]) for row in cur.fetchall()]

@app.route('/move', methods=['POST'])
def move():
    user = request.form['user']
    card_idx = request.form['card_idx']
    target = request.form['target']

    return "TODO"

def addPlayer(username, population=2000000):
    cur = g.db.execute('select * from players where name=?', [username])
    if len(cur.fetchall()) > 0:
        abort(400)
    g.db.execute('insert into players (name, population) values (?, ?)', [username, population])
    g.db.commit()

def drawCards():
    cur = g.db.execute('select id from players')
    for player in cur.fetchall():
        player_id = player.row[0]
        addCard(getRandomAttackCard(), player_id)
        addCard(getRandomAttackCard(), player_id)
        addCard(getRandomBuffCard(), player_id)

def addCard(card_id, player_id):
    g.db.execute('insert into players_cards (card_id, player_id) values (?, ?)', [card_id, player_id])
    g.db.commit()

def clearHands():
    g.db.execute('drop form players_cards')
    g.db.commit()

def getRandomAttackCard():
    return getRandomCard("attack")

def getRandomBuffCard():
    return getRandomCard("buff")

def getRandomCard(cardType):
    with open('cards.json') as data_file:
        cards = json.load(data_file)[cardType]
        card_index = random.randomint(1,len(cards))-1
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
