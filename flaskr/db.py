import pymysql

import click
from flask import current_app, g
from flask.cli import with_appcontext


def init_db():
    return pymysql.connect(
        host="localhost",
        user="root",
        password="",
        db="ml_bitbybit",
        cursorclass=pymysql.cursors.DictCursor
    )


def close_db():
    init_db().close()


def get_db():
    return init_db().cursor()


@click.command('init-db')
@with_appcontext
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo('Initialized the database.')


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)

cursor = get_db()
cursor.execute("SELECT * FROM _user_data WHERE id = 1")
print(cursor.fetchone())
