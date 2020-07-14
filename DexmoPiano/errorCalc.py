# naive example for error computation

# add up all milliseconds where notes where pressed in either case
# pitch, velocity etc. are not taken into account
def computeError(targetNoteInfoList, actualNoteInfoList):
	timeSums = []

	for noteInfoList in [targetNoteInfoList, actualNoteInfoList]:

		tempSum = 0

		for noteInfo in noteInfoList:
			tempSum += noteInfo[3] - noteInfo[2]

		timeSums.append(round(tempSum, 3))

	errorDiff = round(timeSums[1] - timeSums[0], 3)

	return timeSums, errorDiff
