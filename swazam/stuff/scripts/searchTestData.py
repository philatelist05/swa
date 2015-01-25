#!/usr/bin/python

import os, random, sqlite3, sys, time

# compares the fingerprint stored in the database with the one given by `subprints` and returns the hamming distance of the two
def checkFingerprint(c, songId, pos, subprints):
	rc = 0

	c.execute("SELECT fingerprint, pos FROM fingerprint WHERE song_id = ? AND pos BETWEEN ? AND ? ORDER BY pos ASC", (songId, pos, pos+len(subprints)-1))
	for foundSubprint, foundPos in c:
		rc += hammingDistance(foundSubprint, subprints[foundPos-pos])

	return rc

# returns the hamming distance of two integer values
def hammingDistance(value1, value2):
	rc = 0
	while value1 > 0 or value2 > 0:
		rc += (value1%2) ^ (value2%2)
		value1 /= 2
		value2 /= 2

	return rc

# returns a list of all hamming neighbors up tho the distance specified by `limit`
def hammingNeighbors(value, limit, _yieldedValues = set()):
	_yieldedValues.add(value)
	yield value

	if limit > 0:
		for i in range(32):
			newValue = value ^ (1<<i)
			if not newValue in _yieldedValues:
				for v in hammingNeighbors(newValue, limit-1, _yieldedValues):
					yield v

# searches for and yields all subprints matching the given `fingerprint` up to hamming distance `distance`
def searchSubprint(c, fingerprint, distance = 1):
	for v in hammingNeighbors(fingerprint, distance):
		c.execute("SELECT song_id, pos, fingerprint FROM fingerprint WHERE fingerprint = ?", (v,))
		for row in c:
			yield row

# finds a fingerprint in the database.
# first, it picks a random subprint and searches for it (with max hamming distance of 1)
# for all possible matches, it checks if checkFingerprint() returns a distance less than `threshold`
def search(c, fingerprint, hammingThreshold, resultLimit = 1):
	# split hex print into 4 byte integer values (8 hex chars)
	if len(fingerprint) % 8 > 0:
		raise Exception("ERROR: hex fingerprint's length must be a multiple of 4 bytes (8 hex chars)\n")

	subprints = []
	for i in range(0, len(fingerprint), 8):
		subprints.append(int(fingerprint[i:i+8], 16))

	# pick a random one and search for it
	n = random.randint(0, len(subprints)-1)
	for songId, pos, foundPrint in searchSubprint(c, subprints[n], 1):
		print "possible result, checking rest of the print: songId={0}, pos={1}, print={2}".format(songId, pos, foundPrint)
		distance = checkFingerprint(c, songId, pos-n, subprints)
		if distance <= hammingThreshold:
			# found a match => yield it (and return if we found enough matches)
			yield songId, pos-n, distance
			if resultLimit:
				resultLimit -= 1
				if resultLimit <= 0:
					return
		else:
			print "Result above threshold: {0}, {1}, {2}".format(songId, pos-n, distance)

def main():
	path = 'fingerprints.sqlite3'
	fingerprint = "DEADC0DE"
	hammingThreshold=10

	if len(sys.argv) > 1:
		path = sys.argv[1]

	if len(sys.argv) > 2:
		fingerprint = sys.argv[2]

	if len(sys.argv) > 3:
		hammingThreshold = int(sys.argv[3])

	if not os.path.exists(path):
		print "ERROR: file not found: '{0}'".format(path)
		print "USAGE: {0} [fingerprint.sqlite3] [hexFingerprint] [hammingThreshold]".format(sys.argv[0])
		sys.exit(1)

	random.seed()
	conn = sqlite3.connect(path)
	c = conn.cursor()

	start = time.time()
	for row in search(c, fingerprint, hammingThreshold):
		print "Result: {0}".format(row)
	end = time.time()
	print "took {0}s".format(end-start)

if __name__ == '__main__':
	main()

