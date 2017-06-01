
import time

class PointOfMesure:
	def __init__(self):
		self.popd = False

		self.tripNo = 0
		self.usable = 1
		self.lat = 0.00
		self.lon = 0.00
		self.depth = 0.00
		self.sog = 0
		self.time = 0
		self.isVisible = True
		
				
	def setValues(self, lat, lon, depth ):
		self.lat = float(lat)
		self.lon = float(lon)
		self.depth = float(depth)
		
	
	def storeValues(self, tripNo,gpsS,nmea):
		self.tripNo = tripNo
		self.usable = 1
		self.lat = gpsS['lat']
		self.lon = gpsS['lon']
		self.depth = nmea['depth']
		self.sog = gpsS['speed']
		self.time = time.time()

		
	def getMany(self):
		return [( self.tripNo, self.usable, self.lat, self.lon, self.depth, self.sog, self.time)]

