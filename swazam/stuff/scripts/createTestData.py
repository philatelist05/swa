#!/usr/bin/python

import random
import sqlite3
import sys

def createIndex(conn):
	c = conn.cursor()

	c.execute('CREATE INDEX idx_fingerprint ON fingerprint(fingerprint)')
	conn.commit()

def createTables(conn):
	c = conn.cursor()

	c.execute('''CREATE TABLE IF NOT EXISTS song (
		song_id INTEGER PRIMARY KEY NOT NULL, -- will be incremented automatically
		title VARCHAR(200),
		artist VARCHAR(200),
		album VARCHAR(200)
	)''')

	c.execute('''CREATE TABLE IF NOT EXISTS fingerprint (
		song_id INTEGER NOT NULL,
		pos INTEGER NOT NULL,
		fingerprint INTEGER NOT NULL,
		PRIMARY KEY (song_id, pos)
	)''')
	conn.commit()

def createSong(c, duration, skipPrints=5):
	c.execute("INSERT INTO song (title, artist, album) VALUES(hex(randomblob(6)), hex(randomblob(6)), hex(randomblob(6)))")
	songId = c.lastrowid

	print("creating song {0} (duration={1})".format(songId, duration))
	pos = 0
	data = []
	while duration > 0:
		data.append((songId, pos))
		pos += 1
		duration -= skipPrints*(3./256)
	c.executemany("INSERT INTO fingerprint (song_id, pos, fingerprint) VALUES (?, ?, RANDOM() & 0xFFFFFFFF)", data)


def fillDb(conn, songs, commitAfter=100, baseDuration=270, variation=30):
	c = conn.cursor()

	for i in range(songs):
		if i % commitAfter == 0:
			print "::begin"
			c.execute('BEGIN TRANSACTION')

		duration = random.randint(baseDuration-variation, baseDuration+variation)
		createSong(c, duration)

		if i % commitAfter == commitAfter-1:
			print "::commit"
			conn.commit()

	conn.commit()
	

def main(path, songCount):
	conn = sqlite3.connect(path)
	createTables(conn)

	fillDb(conn, songCount)

	print "creating index..."
	createIndex(conn)

path = 'fingerprints.sqlite3'
songCount = 1000

if len(sys.argv) > 1:
	path = sys.argv[1]
if len(sys.argv) > 2:
	songCount = int(sys.argv[2])

main(path, songCount)

