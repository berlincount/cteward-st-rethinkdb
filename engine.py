#!/usr/bin/env python

# Simple storage backend using Flask & RethinkDB
import argparse
import json
import os

from flask import Flask, g, jsonify, render_template, request, abort

import rethinkdb as r
from rethinkdb.errors import RqlRuntimeError, RqlDriverError

# basic configuration settings (TODO: no config file used yet)
RDB_HOST = os.environ.get('RDB_HOST') or 'localhost'
RDB_PORT = os.environ.get('RDB_PORT') or 28015
DATABASE = os.environ.get('DATABASE') or 'cteward-ctorage-000-dev'

# Database creation
def dbSetup():
    connection = r.connect(host=RDB_HOST, port=RDB_PORT)
    try:
        r.db_create(DATABASE).run(connection)
        r.db(DATABASE).table_create('entries').run(connection)
        print 'Database setup completed. Now run the app without --setup.'
    except RqlRuntimeError:
        print 'App database already exists. Run the app without --setup.'
    finally:
        connection.close()

app = Flask(__name__)
app.config.from_object(__name__)

# connection handler (TODO: no pooling done yet)
@app.before_request
def before_request():
    try:
        g.rdb_conn = r.connect(host=RDB_HOST, port=RDB_PORT, db=DATABASE)
    except RqlDriverError:
        abort(503, "No database connection could be established.")

@app.teardown_request
def teardown_request(exception):
    try:
        g.rdb_conn.close()
    except AttributeError:
        pass

# list existing entries (TODO: no subtables yet)
@app.route("/entries", methods=['GET'])
def get_entries():
    selection = list(r.table('entries').run(g.rdb_conn))
    return json.dumps(selection)

# create an entry
@app.route("/entries", methods=['POST'])
def new_entry():
    inserted = r.table('entries').insert(request.json).run(g.rdb_conn)
    return jsonify(id=inserted['generated_keys'][0])

# get a single entry
@app.route("/entries/<string:entry_id>", methods=['GET'])
def get_entry(entry_id):
    entry = r.table('entries').get(entry_id).run(g.rdb_conn)
    return json.dumps(entry)

# replacing an entry (TODO: no updating / transaction log yet)
@app.route("/entries/<string:entry_id>", methods=['PUT'])
def update_entry(entry_id):
    return jsonify(r.table('entries').get(entry_id).replace(request.json)
                    .run(g.rdb_conn))

# updating an entry (TODO: no updating / transaction log yet)
@app.route("/entries/<string:entry_id>", methods=['PATCH'])
def patch_entry(entry_id):
    return jsonify(r.table('entries').get(entry_id).update(request.json)
                    .run(g.rdb_conn))


# deleting an entry (TODO: no updating / transaction log yet)
@app.route("/entries/<string:entry_id>", methods=['DELETE'])
def delete_entry(entry_id):
    return jsonify(r.table('entires').get(entry_id).delete().run(g.rdb_conn))

@app.route("/")
def show_entries():
    return render_template('entries.html')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run the Flask cteward-st-rethinkdb app')
    parser.add_argument('--setup', dest='run_setup', action='store_true')

    args = parser.parse_args()
    if args.run_setup:
        dbSetup()
    else:
        app.run(host='0.0.0.0', debug=True)
