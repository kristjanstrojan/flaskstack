#!/usr/bin/python
#! -*- coding: utf-8 -*-

import os
import sys
import json
import datetime
import sqlite3
from functools import wraps

from flask import Flask, request, session, g, redirect, url_for, abort, \
    render_template, flash

# This helps with the special non
# ascii characters (greek letters, etc).
reload(sys)
sys.setdefaultencoding("utf-8")


# Intitialize and configure Flask app.
app = Flask(__name__)
app.config.from_object(__name__)
app.config.update(dict(
    SECRET_KEY="#$dsflks943JHSs9dueidoijdf", # secret key for signing sessions
    USERNAME='admin',       # change username here
    PASSWORD='test'         # change password here
))
app.config.from_envvar('APP_SETTINGS', silent=True)


# Connection to the sqlite database.
conn = sqlite3.connect('db/Skroutz.db', check_same_thread=False)


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

# Loads current user before each request.
@app.before_request
def load_user():
    if session.get("logged_in") == True:
        user = 'Admin'
    else:
        user = None
    g.user = user


# Decorator for login required.
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.user is None:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


@app.route("/")
@login_required
def index():
    conn.row_factory = sqlite3.Row
    db = conn.cursor()

    db.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = db.fetchall()
    return render_template('index.html', tables=tables)

@app.route("/table/<tname>")
@login_required
def table(tname):
    conn.row_factory = sqlite3.Row
    db = conn.cursor()
    query = "SELECT * FROM '%s'" % tname
    db.execute(query)
    names = db.fetchone().keys()
    return render_template("table.html",tname=tname, names=names)


@app.route("/datatable/<tname>")
def datatable(tname):
    conn.row_factory = dict_factory
    # request arguments
    draw     = request.args.get('draw')
    start    = request.args.get('start')
    length   = request.args.get('length')
    ord_col  = request.args.get('order[0][column]')
    ord_dir  = request.args.get('order[0][dir]')
    search   = request.args.get('search[value]')

    db = conn.cursor()
    row_query = "SELECT * FROM '%s'" % tname
    db.execute(row_query)
    names = db.fetchone().keys()
    recordsTotal = db.execute("SELECT COUNT(*) FROM '%s'" % tname).fetchone()["COUNT(*)"]
    conn.row_factory = None
    db = conn.cursor()
    if search:
        like = "%"+search+"%"
    else:
        like="%"
    try:
        query = "SELECT * FROM '%s' WHERE Product LIKE '%s' LIMIT %d OFFSET %d" % (tname, like, int(length), int(start))
    except:
        query = "SELECT * FROM '%s' LIMIT %d OFFSET %d" % (tname, like, int(length), int(start))
    db.execute(query)
    table = db.fetchall()
   
    recordsFiltered = db.execute("SELECT COUNT(*) FROM '{}' WHERE Product LIKE '{}'".format(tname, like)).fetchone()[0] 
    result = dict(draw=draw, recordsTotal=recordsTotal, recordsFiltered=recordsFiltered, data=table)
    return json.dumps(result)






@app.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == 'POST':
        if request.form['username'] != app.config['USERNAME']:
            error = 'Invalid username'
        elif request.form['password'] != app.config['PASSWORD']:
            error = 'Invalid password'
        else:
            g.user = "admin"
            session['logged_in'] = True
            flash("You were logged in!")
            return redirect(url_for('index'))
    return render_template('login.html', error=error)

@app.route("/logout")
def logout():
    session.pop('logged_in', None)
    g.user = None
    flash('You were logged out.')
    return redirect(url_for('index'))







if __name__ == "__main__":
    app.run(debug=True)
