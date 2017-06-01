

class PomHelper:
	
	def __init__(self, db):
		self.db = db

		
	def chkDiffs(self, p0, p1 ):
		tr = False
		
		if p0.lat <> p1.lat or p0.lon <> p1.lon:
			tr = True
		else:
			print "pom is the same as old one"
		
		if tr == True:	
			row = self.db.getOneRow("depths", ("lat=\"%s\" AND lon=\"%s\""%(p1.lat,p1.lon)),False)
			if row:
				print "pom is in db"
				tr = False
		
		return tr

		