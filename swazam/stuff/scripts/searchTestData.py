#!/usr/bin/python

import random
import sqlite3
import sys

def checkSubPrint(c, songId, pos, expectedPrint, distance):
#	print ":: checkSubPrint: pos={0}, print={1}".format(pos, expectedPrint)
	c.execute("SELECT fingerprint FROM fingerprint WHERE song_id = ? AND pos = ?", (songId, pos))
	for foundPrint, in c:
		for v in hamming(expectedPrint, distance):
			if foundPrint == v:
				return True
		return False
	

def hamming(value, limit, _yieldedValues = set()):
	_yieldedValues.add(value)
	yield value

	if limit > 0:
		for i in range(32):
			newValue = value ^ (1<<i)
			if not newValue in _yieldedValues:
				for v in hamming(newValue, limit-1, _yieldedValues):
					yield v


def searchSubprint(c, fingerprint, distance):
	for v in hamming(fingerprint, distance):
		c.execute("SELECT song_id, pos, fingerprint FROM fingerprint WHERE fingerprint = ?", (v,))
		for row in c:
			yield row



def search(c, fingerprint, distance, resultLimit = 1):
	# split hex print into 4 byte integer values (8 hex chars)
	if len(fingerprint) % 8 > 0:
		raise Exception("ERROR: hex fingerprint's length must be a multiple of 4 bytes (8 hex chars)\n")

	subprints = []
	for i in range(0, len(fingerprint), 8):
		subprints.append(int(fingerprint[i:i+8], 16))

	# pick a random one and search for it
	n = random.randint(0, len(subprints)-1)
	for songId, pos, foundPrint in searchSubprint(c, subprints[n], distance):
#		print "possible result, checking rest of the print: songId={0}, pos={1}, print={2}".format(songId, pos, foundPrint)
		mismatch = False
		# check all the subprints other than n
		for i in range(len(subprints)):
			if i != n: # we've already checked the n'th one
				if not checkSubPrint(c, songId, pos-n+i, subprints[i], distance):
					mismatch = True
					break
		if not mismatch:
			# We've found a match => yield it
			yield songId, pos-n
			if resultLimit:
				resultLimit -= 1
				if resultLimit <= 0:
					return

def main(path, fingerprint, distance):
	conn = sqlite3.connect(path)
	c = conn.cursor()

	for row in search(c, fingerprint, distance):
		print "Result: {0}".format(row)

path = 'fingerprints.sqlite3'
fingerprint = "DEADC0DE"
distance=2

random.seed()

if len(sys.argv) > 1:
	path = sys.argv[1]

if len(sys.argv) > 2:
	fingerprint = sys.argv[2]

if len(sys.argv) > 2:
	distance = int(sys.argv[3])

main(path, fingerprint, distance)
