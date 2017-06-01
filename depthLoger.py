#!/usr/bin/env python2
import os
import sys
import time
import threading
import sqlite3
import multiprocessing
import pickle
import hashlib

from optparse import OptionParser,OptionGroup

import LatLon
import proxDepth
#from proxDepth import *
import PomHelper

from FileActions import *
from math import cos, asin, sqrt,ceil
from gps.gps import *
from KapMaker import *
#from PointOfMesure import *
import PointOfMesure

config = {
	'depthOffset' : 2.2,
	'depthUnits' : 'm', # m - meters or f - feet
	'dbPath' : '/home/yoyo/Apps/depthLoger/LogDepth.db',
	'layerPath' : '/home/yoyo/.opencpn/layers/',
	'nmeaDeamonReaderDelay' : 0.2,
	'nmeaCmd': 'gpspipe -r',
	'postProcess' : 'adb start-server;adb push ~/.opencpn/layers/depths.gpx /sdcard/Android/data/org.opencpn.opencpn_free/files/layers/',
	'kapFilesPathSource' : '/home/yoyo/Apps/ChartsBauhauseSource',
	'kapFilesPathDestination': '/home/yoyo/Charts/a_panama_bauhause'
	}

gpsS = {
	'lon' : 0.00,
	'lonO' : "",
	'lat' : 0.00,
	'latO' : "",
	'time' : 0,
	'speed' : 0
	}

nmea = {
	'sog' : 0.00,
	'depth' : 0.00,
	'time' : 0
	}

versionNo = "0.1"

makeOnlyTestArea = False
squerSize = 0.025
appRunTime = 0
runGpsDeamon = True
gpsDevice = None
gpsRaport = {}
runNmeaDeamon = True
animation = "-"
db = None
tripNo = 1
tripDist = 0.00
tripsDistances = 0.00
oldPom = None
pom = None
pomCount = 0
proxCash = []
makeOnlyPoints = False
makeWithNotVisible = False
density = 1.0




class DataBase:
	def __init__(self):
		global tripNo
		self.con = sqlite3.connect(config['dbPath'])
		
		self.con.enable_load_extension(True)
		self.con.execute("select load_extension('/usr/lib/libsqlitefunctions')")

		self.create()
		
	def gc(self):
		return self.con.cursor()

	def query(self, query):
		c = self.gc()
		c.execute (query)
		try:
			self.con.commit()
		except:
			a=0
	
	def getOneValue(self,table,what,where,ifNoReturn):
		c = self.gc()
		res = c.execute("SELECT %s FROM %s WHERE %s LIMIT 1"%(what, table,where))
		for row in res:
			return row[0]
		
		return ifNoReturn
		
	def getOneRow(self,table,where,ifNoReturn):
		c = self.gc()
		res = c.execute("SELECT * FROM %s WHERE %s LIMIT 1"%(table,where))
		for row in res:
			return row
		
		return ifNoReturn
	
	def getSelect(self,table,what,where,ifNoReturn):
		c = self.gc()
		q = "SELECT %s FROM %s WHERE %s"%(what,table,where)
		#print q
		return c.execute(q)
		
		#return ifNoReturn

	def getTripNr(self):
		return int(self.getOneValue("trips", "treep", "treep order by treep desc",0))+1
	
		
	"""
SELECT 
	denumire, 
	(6371 * acos( cos( radians(45.20327) ) * cos( radians( lat ) ) * cos( radians( 23.7806 ) - 
		radians(lon) ) + sin( radians(45.20327) ) * sin( radians(lat) ) )
		) AS distanta 
FROM depths 
WHERE lat<>'' AND lon<>'' 
HAVING distanta<50 
ORDER BY distanta desc
	"""
		
		
	def create(self):
		try:
			c = self.gc()
			c.execute('''
				CREATE TABLE depths
				(
					id INTEGER PRIMARY KEY AUTOINCREMENT, 
					treep INTEGER,
					usable INTEGER,
					lat text, 
					lon text, 
					depth text, 
					sog text,
					entryDate text
					);
				''')
			self.con.commit()
		except:
			a=1#print("db - error 1")

		try:
			c = self.gc()
			c.execute('''
				CREATE TABLE trips
				(
					id INTEGER PRIMARY KEY AUTOINCREMENT, 
					treep INTEGER,
					distance text,
					entryDate text,
					description text
					);
				''')
			self.con.commit()
		except:
			a=1#print("db - error 2")

		

	
	def delete(self, table, where):
		c = self.gc()
		c.execute("DELETE FROM %s WHERE %s" %(table,where))
		self.con.commit()	
	
	def insertTrip(self,description):
		global tripNo,tripDist
		
		c = self.gc()
		d = [(tripNo, tripDist, time.time(), description)]
		c.executemany('INSERT INTO trips (treep,distance,entryDate, description) VALUES (?,?,?,?)', d)
		self.con.commit()

	def insert(self, pom):
		c = self.con.cursor()
		#d = [(gpsS['lat'], gpsS['lon'], nmea['depth'], time.time())]
		c.executemany('INSERT INTO depths (treep,usable,lat,lon,depth,sog,entryDate) VALUES (?,?,?,?,?,?,?)', pom)
		self.con.commit()
		print("db - insert")

	def insertDoCommit(self, pom):
		c = self.con.cursor()
		#d = [(gpsS['lat'], gpsS['lon'], nmea['depth'], time.time())]
		c.executemany('INSERT INTO depths (treep,usable,lat,lon,depth,sog,entryDate) VALUES (?,?,?,?,?,?,?)', pom)
		return self.con

		
class nmeaDeamon:
	def __init__(self):
		print("nmeaDemon")
	
	def parseDepth(self,report):
		s = report.split(",")
		d = round(float(s[1]),1)
		nmea['depth'] = d+config['depthOffset']
		
	def start(self):
		self.tNmea = threading.Thread(target=self.makeItRun,args=())
		self.tNmea.start()
	
	def stop(self):
		print("TODO - stop nmea threading") 
		#self.tGps.exit()
		
		
	def makeItRun(self):
		c = os.popen(config["nmeaCmd"], "r")
		l = c.readline()
		while l:
			t = time.time()
			if (t-appRunTime)>3.00:
				break
			#print("nmeaDeamon line[%s]" % l )
			#$SDDPT,8.3,*72
			if l[:6] == "$SDDPT":
				self.parseDepth(l)
				nmea['time'] = t
				#printData()
			else:
				None
			
			l = c.readline()			
			time.sleep(config['nmeaDeamonReaderDelay'])
			
		print("nmeaDeamon - STOP")

class gpsDeamon:
	def __init__(self, ll):
		print("gpsDeamon")
		self.ll = ll
		self.session = None
		
	def parse(self, report):
		a = 0
		try:
			gpsS['lon'] = report['lon']
			if gpsS['lon'] > 0.0:
				gpsS['lonO'] = "E"
			else:
				gpsS['lonO'] = "W"
				
			a+=1
		except:
			b=1
		
		try:
			gpsS['lat'] = report['lat']
			if gpsS['lat'] > 0.0:
				gpsS['latO'] = "N"
			else:
				gpsS['latO'] = "S"
				
			a+=1
		except:
			b=1
		
		try:
			gpsS['speed'] = report['speed']
		except:
			gpsS['speed'] = 0	
		
		if a > 0:
			gpsS['time'] = time.time()			
		else:
			#print report
			try:
				if len(report['path'])>0 and report['class'] == "DEVICE" and report['activated'] > 0:
					gpsDevice = True
					print("gps device connected")
				else:
					gpsDevice = None
					print("gps device disconnected")
			except:
				b=1
		#print("lon[%s] lat[%s]"%(lon,lat))
		
	def start(self):
		self.tGps = threading.Thread(target=self.makeItRun,args=())
		self.tGps.start()
	
	def stop(self):
		print("TODO - stop gps threading") 
		#self.tGps.exit()
		
	def makeItRun(self):
		self.session = gps()
		self.session.stream(WATCH_ENABLE)
		try:
			for report in self.session:
				if (time.time()-appRunTime)>3.00:
					break
				self.parse(report)
				#print report
				
		except KeyboardInterrupt:
		# Avoid garble on ^C
			print("......... from gps")
	
		
		print("gpsDeamon - STOP")

def printData():
	os.system("clear")
	#print("---------------------------------------------------------------")
	global animation, tripDist, oldPom, pom, pomCount,tripsDistances
	
	t = time.time()
	
	if animation == "-":
		animation = "/"
	elif animation == "/":
		animation = "|"
	elif animation == "|":
		animation = "\\"
	elif animation == "\\":
		animation = "-"
		
	gpsStatus = False
	
	print("Depth loger version (%s) (%s) [%s]" % (versionNo, animation, time.ctime()))
	print("===========================================================")
	if gpsS['lon']!=0.00 and gpsS['lat']!=0.00 and (t-gpsS['time'] )<2.00 :
		print("- gps status")
		print("	lat, lon	(%s) %s , (%s) %s" % (gpsS['latO'], gpsS['lat'], gpsS['lonO'], gpsS['lon']) )
		print("	speed		%s Knots" % gpsS['speed'])
		print("	old		%s sec." % round(t-gpsS['time'], 2) )
		
		tripDist+= gpsS['speed']/3600.00
				
		gpsStatus = True
		
		
	else:
		print("gps waiting for fix or gps device...")
		if gpsDevice == None:
			print("	- no gps device found :(")
	
	print("")
	
	nmeaStatus = False
	
	if (t-nmea['time'])<2.00:
		print("- nmea status")
		print("	sog		(%s) Knots" % nmea['sog'])
		print("	depth		read (%s) %s	(%s)" % (nmea['depth'],config['depthUnits'],(nmea['depth']-config['depthOffset'])) )

		nmeaStatus = True

	if gpsStatus and nmeaStatus:
		print("\n- from app")
		print("	treap NO	%s" % tripNo)
		print("	trip distance	%s nMiles" % (round(tripDist,4)) )
		print("	total distance	%s nMiles" % round((tripsDistances+tripDist),4) )
		print("	pom on trip	%s" % pomCount)
		
		if pom:
			oldPom = pom
		pom = PointOfMesure.PointOfMesure()
		pom.storeValues(tripNo,gpsS, nmea)
		
		if oldPom and pom:
			if pomh.chkDiffs(oldPom, pom):
				db.insert(pom.getMany())
				pomCount+=1
			
		
def chkIsItFarAnuff(pom, ptr):	
	for p1 in ptr:
		if not p1.isVisible:
			continue
		dist = ll.distanceInM( pom.lat, pom.lon, p1.lat, p1.lon )
		if proxDepth.proxDepth(pom, p1,density, dist) == False:
			return False
	
	return True

	
	
def getPoints():
	global makeOnlyPoints,makeWithNotVisible
	makeOnlyPoints = True
	makeWithNotVisible = True
	return makeGpxFile()


def makeNiceDepth(depth):
	if depth>5.00:
		return int(depth)
	else:
		d = str(round(depth,1))
		if d[-2:] == ".0":
			return d[:-2]
		else:
			return d

def enhanceMin(i):
	global squerSize

	if i < 0.0:
		a = 0.0
		while True:
			if a <= i:
				return a
			else:
				a-= squerSize

	if i > 0.0:
		a = 0.0
		while True:
			if a > i:
				return a-squerSize
			else:
				a+= squerSize


	return i

def getMinMaxLatLon():
	global db,makeOnlyTestArea
	if makeOnlyTestArea == False:
		minLat = db.getOneValue("depths", "lat", "1 ORDER BY lat", False)
		maxLat = db.getOneValue("depths", "lat", "1 ORDER BY lat DESC", False)
		minLon = db.getOneValue("depths", "lon", "1 ORDER BY lon", False)
		maxLon = db.getOneValue("depths", "lon", "1 ORDER BY lon DESC", False)
	else:
		#PLY/1,9.4969963,-79.0048066
		#PLY/2,9.4969963,-78.9292565
		#PLY/3,9.4502272,-78.9292565
		#PLY/4,9.4502272,-79.0048066 
		minLat = 9.4502272
		maxLat = 9.4969963
		minLon = -79.0048066
		maxLon = -78.9292565
		
	return [ enhanceMin(minLat), maxLat, enhanceMin(minLon), maxLon]
			
def makeGpxFile(dbQueryExtra="", destFileName="depths.gpx"):
	global db, makeOnlyPoints,makeWithNotVisible,density,squerSize
	print("make gpx.....")

	cpuCount = multiprocessing.cpu_count()*2+1
	print("will use %s threads"% cpuCount)
	
	tp = []
	pc = 0
	ptr = []
	skipt = 0
	uncloge = 0
	#rebuildPPDist()
	fa = FileActs()
	
	tp.append("""<?xml version="1.0"?>
<gpx version="1.1" creator="OpenCPN" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="http://www.topografix.com/GPX/1/1" xmlns:gpxx="http://www.garmin.com/xmlschemas/GpxExtensions/v3" xsi:schemaLocation="http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd" xmlns:opencpn="http://www.opencpn.org">\n"""
		)

	minLat, maxLat, minLon, maxLon = getMinMaxLatLon()
	print("min max lat\n	%s\n	%s\nmin max lon\n   %s\n	%s"% (minLat, maxLat, minLon, maxLon))
	x = maxLon-minLon
	y = maxLat-minLat
	print("min max diff x,y (%s,%s)"%(x,y))
	xw=int(ceil(x/squerSize))	
	yh=int(ceil(y/squerSize))
	print("squers todo x,y (%s,%s)"%(xw,yh))

	rTotal = db.getOneValue("depths","count(id)", "%s 1" %dbQueryExtra, 0 )
	print("points in database %s" %rTotal)
	
	tl = []
	tcount = 0
	tPickleCount = 0
	ql = []
	tlPickle = []
	
	for x in range(0,xw,1):
		for y in range(0,yh,1):
			latMin = minLat+(y*squerSize)
			latMax = minLat+((y+1)*squerSize)+0.0000001
			lonMin = minLon+(x*squerSize)
			lonMax = minLon+((x+1)*squerSize)+0.0000001

			q = "%s " % dbQueryExtra +\
				"lat>%s AND lat<%s AND "%(latMin,latMax)+ \
				"lon>%s AND lon<%s "%(lonMin,lonMax)+ \
				"ORDER BY depth"

			if makeOnlyTestArea:
				q="%s LIMIT 1000" % q

			sys.stdout.write("prechk [%s,%s].......\r"%(x,y))
			qt = q.split("LIMIT")
			if dbQueryExtra == "":
				pCount = db.getOneValue("depths","count(id)",qt[0],0)
			else:
				pCount = 1
			fName = "%s_%s_%s_%s" % (density, latMin, lonMin, pCount)
			if makeOnlyTestArea:
				fName = "%sTEST" % fName
			#fName = "cashe_%s.pickle"% hashlib.md5(fName).hexdigest()
			fName = os.path.join("cashe","%s.pickle" %fName)

			if not fa.isFile(fName) and pCount > 0:
				tl.append( threadMakeGpxSquer(
					q, rTotal, pc, "%s,%s"%(x,y), fName
					))
				tcount+=1
			elif pCount == 0:
				skipSquerNoWorkToBeDone = 1
			elif dbQueryExtra == "":
				t = pickle.load(open(fName, 'rb'))
				for tpi in t[0]:
					tp.append(tpi)
				for ptri in t[1]:
					ptr.append(ptri)
				tPickleCount+=1
	
	useThreads = True
	#useThreads = False
	if useThreads:
		print("entering thread watchdog loop")
		while True:		
			trun = 0
			tdone = 0
			tinit = 0
		
			for t in tl:
				if t.status == "runing":
					trun+=1
				if t.status == "done":
					tdone+=1
				if t.status == "init":
					tinit+=1
			
			if trun < cpuCount:
				for t in tl:
					if t.status == "init":
						t.start()
						trun+=1
						if trun >= cpuCount:
							break
				
			if tcount == tdone:
				break

			sys.stdout.write("init %s   runing %s   done %s   from pickle %s...............\r"%(tinit, trun, tdone, tPickleCount))
			time.sleep(0.05)
		
		print("watchdog loop done")
		if dbQueryExtra == "":
			print("dumping to pickle")
			for t in tl:
				if len(t.tp)>0 or len(t.ptr)>0:
					pickle.dump([t.tp, t.ptr], open(t.fName, 'wb'))
			print("pickle process done :)")

	else:
		snr = 0
		for t in tl:
			snr+=1
			t.run()
			sys.stdout.write("status squera runs %s / %s...............\r"%(snr, len(tl)))
			

	for t in tl:
		for tpi in t.tp:
			tp.append(tpi)
		for ptri in t.ptr:
			ptr.append(ptri)

		skipt+=t.skipt
		uncloge+=t.uncloge			
	
	tp.append("\n</gpx>")
	
	if not makeOnlyPoints:
		fa = FileActs()
		fa.writeFile( os.path.join(config['layerPath'],destFileName),"".join(tp))
	print("squer size %s [lat,lon]"%squerSize)
	print("points skipt %s" % skipt)
	print("squers from pickle files %s"%tPickleCount)
	print("pointss skipt uncloged %s " % uncloge)
	print("points added %s" % (len(ptr)-1))
	if not makeOnlyPoints:
		print( "gpx file ready :)")
	else:
		print( "make only point to png files %s"%len(ptr))
		return ptr

	#print(stats)

class threadMakeGpxSquer:
	def __init__(self, q, rTotal, pc, xy, fName):
		self.status = "init"
		self.q = q
		self.tp = []
		self.ptr = []
		self.skipt = 0
		self.uncloge = 0 
		self.rTotal = rTotal
		self.pc = pc
		self.xy = xy
		self.fName = fName


	def start(self):
		self.sq = threading.Thread(target=self.run,args=())
		self.sq.start()

		
	def run(self):
		self.status = "runing"

		self.tp,self.ptr,self.skipt,self.uncloge,self.pc = makeGpxSquer(
			self.q, 
			self.tp, [],
			self.skipt,
			self.uncloge,
			self.rTotal, 
			self.pc, 
			self.xy
			)
			
		self.status = "done"
		
	
def makeGpxSquer(q, tp, ptr, skipt, uncloge, rTotal,pc, squerNo):	
	oldPom = None
	lastPop = False

	db = DataBase()	
	rows = db.getSelect("depths", "lat,lon,depth,sog,id", 
		q, 
		False)

	for r in rows:
		add = False
		pc+=1
		
		p0 = PointOfMesure.PointOfMesure()
		p0.setValues(r[0], r[1], r[2])
	
		if not oldPom:
			add = True
		else:	
			dist = ll.distanceInM(p0.lat, p0.lon, oldPom.lat, oldPom.lon) 
			
			if proxDepth.proxDepth(p0, oldPom,density, dist):			
				#print "dist %s depth %s p0 [%s] oldPom [%s]" % (ll.distance(p0, oldPom), p0.depth, p0.depth, oldPom.depth)
				add = True
		
				if chkIsItFarAnuff(p0, ptr) == False:
					add = False
					uncloge+=1
			
		if add:
			depth = makeNiceDepth(r[2])
			tp.append(("""
  <wpt lon=\""""+str(r[1])+"""\" lat=\""""+str(r[0])+"""\">
    <name>"""+str(depth)+"""</name>
    <sym>empty</sym>
  </wpt>"""
  			))

			ptr.append( p0 )			  
			#idAdded.append(str(itemId))
			oldPom = p0
			
		else:
			skipt+=1
			if makeWithNotVisible:
				p0.isVisible = False
				ptr.append(p0)
			
	
	return [ tp, ptr, skipt,uncloge,pc ]
	

def tes():
	while True:
		print("th start")
		time.sleep(1)


def importFile( path ):
	print("importing file [%s]"%path)
	f = open(path)
	l = f.readline()[:-1]
	ln = 0
	depthLn = 0
	llLn = 0
	ll = LatLon.LatLon()
	ta = []
	tripNo = db.getTripNr()
	print("it will be %s tripNo"% tripNo)
	lat = False
	lon = False
	speed = False
	depth = 0
	depthOld = 0.00
	depthSame = 0
	depthError = 0
	gpsDelays = 0
	skipt = 0

	lines = []
	while l:
		if l[:2] == "Tx":
			l = l[10:]
				
		if l[:6]=="$SDDPT" or l[:6]=="$GPRMC":
			lines.append(l[:-2])

		l = f.readline()
	
	
	for l in lines:
		if l != "":
			ln+=1

			if (ln%10) == 0:
				sys.stdout.write("procesing line ...	%s       \r" %(ln))		
			
			#print("[%s]"%l)
			"""
			if depth and depth==126.2 and round(lat,6)==round(9.63543319702148,6):
				print" lat %s   lon %s  depth %s" %(lat, lon, depth)
				print llLine
				#sys.exit(1)
			"""
			
			if l[:6]=="$SDDPT":
				d = l.split(",")
				depth = float(d[1])+config['depthOffset']
				depthLn = ln				

				if (ln-llLn)<3 and lat and lon:
					pom = PointOfMesure.PointOfMesure()
					pom.tripNo = tripNo
					pom.setValues(lat,lon,depth)
					pom.sog = speed
					#print" lat %s   lon %s  depth %s" %(lat, lon, depth)

					add = True
					if len(ta)>1:
						p0lat = ta[-1].lat
						p0lon = ta[-1].lon
						if pom.lat==p0lat and pom.lon==p0lon:
							add=False
							skipt+=1

					if add:
						ta.append(pom)
					
					if depthOld == depth:
						depthSame+=1
					elif depthOld != depth and depthSame>20:
						for i in range(0,depthSame+3,1):
							try:
								ta.pop()
							except:
								abc=0
						depthError+=depthSame
						depthSame = 0
					elif depthOld != depth:
						depthSame = 0

					depthOld = depth
				else:
					gpsDelays+=1
				
			if l[:6]=="$GPRMC":
				llLine = l
				lat, lon, speed = ll.convertNmeaRMCToLatLon(l)
				llLn = ln
					
		
		
	print("add to db")
	insert=0
	con = None
	for p0 in ta:
		con = db.insertDoCommit(p0.getMany())
		insert+=1
		if (insert%100)==100:
			con.commit()
			sys.stdout.write("insert %s / %s...............\r"%(insert, len(ta)))		
			
		
	if con:
		con.commit()
	if len(ta)>1:
		dupCount = db.getOneValue("depths", "count(id)", "1 group by lat||\"_\"||lon having count(id)>1 order by count(id) desc",0)
		if dupCount>0:
			for i in range(0,dupCount,1):
				db.query("delete from depths where id in (select id from depths where 1 group by lat||\"_\"||lon having count(id)>1);")
	db.insertTrip("file:%s"%path)
		
	print("found pom to add %s" % len(ta))
	print("found errors in readings %s"% depthError)
	print("gps delays %s"%gpsDelays)
	print("inserted to db %s"%insert)
	print("skip the same lat lon %s"%skipt)

		
	print(" done")

def makeBackAction():
	lastTripIp = db.getOneValue("trips","treep","1 order by treep desc", 0)
	desc = db.getOneValue("trips","description","treep=%s"%lastTripIp,0)
	count = db.getOneValue("depths", "count(id)", "treep=%s"%lastTripIp,0)
	print("last trip id is %s it have %s inserts" % (lastTripIp,count))
	print("treep description [%s]"%desc)
	a = raw_input("do you what to delete it ? [y/n]")
	if a == "y":
		db.delete("depths","treep=%s"%lastTripIp)
		db.delete("trips", "treep=%s"%lastTripIp)
		print "DONE"
	
def makeRecursiveImportFromFiles(path):
	list = os.listdir(path)
	fa = FileActs()
	for i in list:
		fp = os.path.join(path, i)
		if fa.isFile(fp):
			test = db.getOneValue("trips","id",("description=\"%s\""%("file:%s"%fp)), "")
			if test=="":
				importFile(fp)
			else:
				print("skip [%s] is in db"%fp)
		if fa.isDir(fp):
			makeRecursiveImportFromFiles(fp)

def makeGpxFilesOutSiteOfKap():
	km = KapMaker(config,None, makeOnlyTestArea,action="squersArea")						
	q = []
	for k in km.files:
		if k.lat0<>None and k.lon0<>None and k.lat1<>None and k.lon1<>None:
			q.append( " ( lat<=%s and lat>=%s and lon>=%s and lon<=%s )"%(k.lat0,k.lat1, k.lon0,k.lon1) )
	qAdd = " or \n".join(q)
	qAdd = "id not in ( select id from depths where %s) and" % qAdd 
	#print qAdd
	makeGpxFile( dbQueryExtra=qAdd, destFileName="depthOutOfSquers.gpx")

def makeParserView():
	parser = OptionParser()
	parser.add_option("-i", "--import", dest="iimport",action="store", type="str", default="",
				help="import file or directory of nmea files")
	parser.add_option("-k", dest="kap",action="store_true", default=False,
				help="make kap files with aditional depth readings. Kap file source directory [%s] and put them to [%s] "%(config['kapFilesPathSource'], config['kapFilesPathDestination']))
	parser.add_option("-g", dest="gpx",action="store_true", default=False,
				help="make gpx file with depths")
	parser.add_option("-r", dest="gpxrest",action="store_true", default=False,
				help="make gpx file with depths reading outsite of kap files areas")	
	
	
	group = OptionGroup(parser, "Configuration options")
	group.add_option("-u","--units", dest="units", action="store", default=config['depthUnits'], choices=["m","f"],
				help="set unit type [m|f] only to use during import or live loging")
	group.add_option("-d","--database", dest="dbPath", action="store", type="str", default=config['dbPath'], 
				help="set location for data base file default [%s]"%config['dbPath'])
	group.add_option("-o","--offset", dest="offset", action="store", type="float", default=config['depthOffset'],
				help="set offset for your depthsounder default is [%s] %s"%(config['depthOffset'],config['depthUnits']) )
	group.add_option("-c", dest="config",action="store_true", default=False,
				help="print config and exit")
	parser.add_option_group(group)


	group = OptionGroup(parser, "Dangerous Options",
                    "Caution: use these options at your own risk.  "
                    "It is believed that some of them bite.")
	group.add_option("-b", "--back", dest="back",action="store_true", default=False,
				help="remove last trip logs from data base")
	#group.add_option("--makePickle", dest="mkPickle",action="store_true", default=False,
	#			help="make pickle cashe file (good for testing not for using)")
	#group.add_option("--usePickle", dest="usePickle",action="store_true", default=False,
	#			help="use pickled data if it is there (good for testing not for using)")
	group.add_option("-t", "--test", dest="test", action="store_true", default=False,
                help="make small sample run (for testing and coding) can be use with [-g|-k]")
	parser.add_option_group(group)


	return parser

def exitAndPlaySound(exitStatus=0):
	os.system("play ./1bells.wav")
	sys.exit(exitStatus)

def makeConfigUpdate(parser):
	(opt, args) = parser.parse_args()

	config['depthUnits'] = opt.units
	config['depthOffset'] = opt.offset
	config['dbPath'] = opt.dbPath

	return opt

if __name__ == "__main__":
	appRunTime = time.time()
	
	db = DataBase()
	tripNo = db.getTripNr()
	tripsDistances = db.getOneValue("trips", "sum(distance)", "1", 0)
	ll = LatLon.LatLon()
	pomh = PomHelper.PomHelper(db)

	parser = makeParserView()
	opt = makeConfigUpdate(parser)

	print os.path.realpath(__file__)
	#print opt
	if opt.config:
		print ("%s"%config).replace(",","\n")
		sys.exit(0)

	if opt.test:
		makeOnlyTestArea = True

	#if opt.mkPickle:
	#	print("making only pickle file")
	#	pom = getPoints()
	#	pickle.dump(pom, open('save_pom_pickle.p', 'wb'))
	#	print("pickle points stored.")
	#	sys.exit(0)

	if opt.back:
		makeBackAction()
		sys.exit(0)

	if opt.gpx:
		makeGpxFile()
		exitAndPlaySound()

	if opt.gpxrest:
		makeGpxFilesOutSiteOfKap()
		exitAndPlaySound()

	if opt.kap:
		density = 0.2
		#if opt.usePickle:
		#	pom = pickle.load(open('save_pom_pickle.p', 'rb'))
		#	print("using pickle data for pom")
		#else:
		#	pom = getPoints()
		#	pickle.dump(pom, open('save_pom_pickle.p', 'wb'))
		#	print("pickle points stored.")
		pom = getPoints()
		km = KapMaker(config,pom, makeOnlyTestArea)						
		exitAndPlaySound()

	if opt.iimport <> "":
		fa = FileActs()
		if fa.isDir(opt.iimport):
			makeRecursiveImportFromFiles(opt.iimport)
		elif fa.isFile(opt.iimport):
			importFile(opt.iimport)
		exitAndPlaySound()


	
	g = gpsDeamon(ll)
	g.start()
	
	n = nmeaDeamon()
	n.start()
		
	try:	
		while True:
			appRunTime = time.time()
			printData()
			time.sleep(1)
			
	except KeyboardInterrupt:
		# Avoid garble on ^C
		print(".........")
		db.insertTrip("live recorde")
		g.stop()	
		n.stop()

	
	os.kill(os.getpid(), 1 )
	print("DONE")
	