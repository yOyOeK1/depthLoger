from math import cos, asin, sqrt,ceil

class LatLon:

	def convertNmeaRMCToLatLon(self,line):
		#['$GPGLL', '0933.083', 'N', '07857.121', 'W', '120417.86', 'A', 'D*7C']
		#$GPRMC,114402.14,A,0932.909,N,07857.334,W,0.0,000.0,040417,000.0,E,A*27

		cdef float sog = 0.0		
		t = line.split(",")
		
		cdef float lat = float(t[3])/float(100.0000)
		lat = self.convertMinToDeg (lat)
		if t[4]=="S":
			lat*=float(-1.0000)
		
		cdef float lon = float(t[5])/float(100.0000)
		lon = self.convertMinToDeg (lon)
		if t[6]=="W":
			lon*=float(-1.0000)

		try:
			sog = float(t[7])
		except:
			sog = 0.0
			print "error geting speed[%s]"%t[7]
			
		return [lat, lon, sog]

		
	def convertMinToDeg(self,minutes):
		s = "%s" % minutes
		ss = s.split(".")
		cdef float dec = float("0.%s"%ss[1])/float(0.6) 
		return float(ss[0])+dec
		
		
	def distanceLL(self,p0, p1): #in latitudelong
		return sqrt((p1.lon - p0.lon)**2 + (p1.lat - p0.lat)**2)

		
	def distance(self, lat1,lon1, lat2,lon2 ): #km
		cdef float p = 0.01745329251994 
		a = 0.5 - cos((lat2 - lat1) * p)/2 + cos(lat1 * p) * cos(lat2 * p) * (1 - cos((lon2 - lon1) * p)) / 2 
		return 12742 * asin(sqrt(a))


	def distanceInM(self, lat1,lon1, lat2,lon2 ): #m
		cdef float p = 0.01745329251994 
		a = 0.5 - cos((lat2 - lat1) * p)/2 + cos(lat1 * p) * cos(lat2 * p) * (1 - cos((lon2 - lon1) * p)) / 2 
		return int(12742000 * asin(sqrt(a)))

		