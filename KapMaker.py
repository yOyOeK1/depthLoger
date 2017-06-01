
import os
import sys
import random
from FileActions import *
from PIL import Image, ImageDraw, ImageFont,ImageEnhance,ImageFilter
import time


boxColector = []
modifyd = 0
modifydFiles = []


class KapRefCon:
	def __init__(self, x,y,lat,lon):
		self.x = int(x)
		self.y = int(y) 
		self.lat = float(lat)
		self.lon = float(lon)


class Box:
	def __init__(self, x,y,w,h, depth):
		self.x = x
		self.y = y
		self.w = w
		self.h = h
		self.depth = depth
		self.visible = True

	def setVisible(self, show ):
		self.visible = show


def BoxCollisionDetect(bft):
	global boxColector

	a = bft
	margin = 3
	tr = []

	for b in boxColector:
		if b.visible and \
			( (a.x+a.w)<(b.x-margin) or (a.x-margin) > (b.x+b.w) ) == False and \
			( (a.y+a.h)<(b.y-margin) or (a.y-margin) > (b.y+b.h) ) == False:
			#tr.append(b)			
			return True

			
	#return tr
	return False
			
class KapFile:
	def __init__(self, path, fileName, pointsForMaps,pathDest,action=""):
		self.path = path
		self.pathDest = pathDest
		self.fileName = fileName,
		self.pointsForMaps = pointsForMaps
		self.fullPath = os.path.join( path, fileName )
		self.fullPathDest = os.path.join( pathDest, fileName)
		self.rand = random.Random()
		self.tmpPath = "/tmp/kapTmp.kap"
		self.action = action
		
		self.refs = []
		self.fileStatus = True
		self.fileModify = False

		self.x0 = None
		self.y0 = None
		self.lat0 = None
		self.lon0 = None
		self.x1 = None
		self.y1 = None
		self.lat1 = None
		self.lon1 = None

		self.pixW = 0
		self.pixH = 0
		self.latC = 0.00
		self.lonC = 0.00
		self.pixLat = 0.00
		self.pixLon = 0.00

		self.scale = None
		
		self.analize()
		#print " found %s point of reference" % len(self.refs) 

		self.makeTheRest()

	def makeTheRest(self):

		if self.x0<>None and self.x1<>None:
			#print " references extracted"
			self.latC = self.lat0-self.lat1
			self.lonC = self.lon0-self.lon1

			if self.action == "squersArea":
				print([self.lat0, self.lon0, self.lat1, self.lon1]) 
				return [self.lat0, self.lon0, self.lat1, self.lon1]
			
		else:
			print " references extraction problem :("
			self.fileStatus = False


		if self.fileStatus:
			modIt = False
			for p in self.pointsForMaps:
				#print "point"
				if self.lat0>=p.lat and self.lat1<=p.lat and \
					self.lon0<=p.lon and self.lon1>=p.lon:
					modIt = True
					break

		if modIt == False:
			print " skip the file no points on this kap file"
			self.fileStatus = False
			
		if self.fileStatus:
			print " make tmp copy of kap file"
			if self.mkcopy( self.fullPath, self.tmpPath) == False:
				self.fileStatus = False

		if self.fileStatus:
			print " extracting png file from kap"
			self.extractImage()

		if self.fileStatus:
			print " making new depth layer on img"
			self.makeNewDepths()

		if self.fileStatus and self.fileModify:
			print " file %s modifyed :)" % self.fileName
			inputFile = "%s_mod.png"%self.tmpPath
			cmd = "imgkap \"%s\" \"%s\" \"%s\" \"%s;%s\" \"%s\" \"%s\" \"%s;%s\" \"%s\"" % \
				(inputFile, self.lat0, self.lon0, self.x0, self.y0, \
				self.lat1, self.lon1, self.x1-1, self.y1-1, self.fullPathDest)
			os.remove(self.fullPathDest)
			#print cmd
			os.system(cmd)

	def makeNiceDepth(self, depth_):
		if depth_>5:
			depth = "%s" % int(depth_)
		else:
			depth = "%s" % round(depth_,1)
			if depth[-2:] == ".0":
				depth = depth[:-2]

		depthDecimal = 0
		dt = depth.split(".")
		if len(dt)>1:
			depth = dt[0]
			depthDecimal = dt[1]

		return [depth, depthDecimal]
				

	def makeNewDepths(self):
		global boxColector, modifyd,modifydFiles
		
		pc = len(self.pointsForMaps)-1

		"""
		file_data = Image.open("%s_mod.png"%self.tmpPath)
		file_data = file_data.convert('RGB') # conversion to RGB
		file_data = file_data.convert('P', palette=Image.ADAPTIVE, colors=256)
		"""

		"""
		import numpy as np
		import cv2
		from matplotlib import pyplot as plt

		img = cv2.imread("%s.png"%self.tmpPath)

		dst = cv2.fastNlMeansDenoisingColored(img,None,10,10,7,21)

		plt.subplot(121),plt.imshow(img)
		plt.subplot(122),plt.imshow(dst)
		plt.show()

		sys.exit(0)
		"""

		img = Image.open("%s.png"%self.tmpPath)
		img = img.convert("RGBA")
		
		fnt = ImageFont.truetype("Arial.ttf",12)
		fntSmall = ImageFont.truetype("Arial.ttf",9)
		fntBig = ImageFont.truetype("Arial.ttf",14)
		
		imgBg = Image.new('RGBA', img.size, (255,255,255,0))		
		imgBgDraw = ImageDraw.Draw(imgBg)
		imgTxt = Image.new('RGBA', img.size, (255,255,255,0))		
		imgTxtDraw = ImageDraw.Draw(imgTxt)
		

		self.pixW = img.size[0]-1
		self.pixH = img.size[1]-1
		self.pixLat = self.pixH/self.latC#/self.pixH
		self.pixLon = self.pixW/self.lonC#/self.pixW

		#print "x0 %s y0 %s  x1 %s y1 %s" %(self.x0, self.y0, self.x1, self.y1)
		#print "w %s h %s" %( self.pixW, self.pixH )
		#print "latC %s lonC %s" % ( self.latC, self.lonC )

		# -------- painting background color in order first shallow
		

		for i in range(pc,0,-1):
			p = self.pointsForMaps[i]
			depth, depthDecimal = self.makeNiceDepth(p.depth)
			bgc = False

			twidth,theight = fnt.getsize(depth)

			if p.depth<10.0 and p.depth>2.2:
				bgc = True
				dep = ((p.depth-2.2)/7.8)
				r = dep
				g = 0.5+(dep*0.5)
				b = 0.75+(dep*0.25)
				
			elif p.depth <=2.2:
				bgc = True
				dep = ((p.depth-2.2)/8.8)*0.9
				r = 0.75
				g = 0.75
				b = 0.99

			elif p.depth>=10.0 and p.isVisible:
				bgc = True
				r = 1
				g = 1
				b = 1
				
			if bgc:
				margin = 2
				x = (self.lon0-p.lon)*self.pixLon
				y = (self.lat0-p.lat)*self.pixLat
				if depthDecimal!=0:
					twidth+=6				
				txc = x-(twidth/2.0)
				tyc = y-(theight/2.0)								
				
				imgBgDraw.rectangle(
					((txc-margin,tyc-margin),(txc+twidth+margin,tyc+theight+margin)), 
					fill=(int(r*255),int(g*255),int(b*255),255))

		

		
	
		for p in self.pointsForMaps:
			if p.isVisible == False:
				continue

			if self.lat0>=p.lat and self.lat1<=p.lat and \
				self.lon0<=p.lon and self.lon1>=p.lon:

				putOnChart = True
				
				x = (self.lon0-p.lon)*self.pixLon
				y = (self.lat0-p.lat)*self.pixLat
				
				depth, depthDecimal = self.makeNiceDepth(p.depth)
				twidth, theight = fnt.getsize(depth)
				if depthDecimal!=0:
					twidth+=6	
					theight+=4			
				self.fileModify = True
				txc = x-(twidth/2.0)
				tyc = y-(theight/2.0)								
				
				b = Box( x,y,twidth, theight, p.depth )
				bcol = BoxCollisionDetect (b)
				#if len(bcol)>0:
				if bcol == True:
					b.setVisible (False)
					putOnChart = False

				cb = 0.9

				if putOnChart:
					imgTxtDraw.text( (txc+1, tyc+1), depth, font=fnt, fill="gray" )
					imgTxtDraw.text( (txc, tyc), depth, font=fnt, fill="black" )
										
					if depthDecimal!=0:
						imgTxtDraw.text( (txc+8, tyc+5), depthDecimal, font=fntSmall, fill="gray" )
						imgTxtDraw.text( (txc+7, tyc+4), depthDecimal, font=fntSmall, fill="black" )
					
					
				boxColector.append(b)


		strtime = time.strftime("%Y%m%d_%H%M%S")
		tw, th = fntBig.getsize(strtime)
		imgTxtDraw.text((img.size[0]-tw-4, img.size[1]-th-4 ), strtime,  font=fntBig, fill=(255,0,0,255))
		
		enhancer = ImageEnhance.Sharpness(img)
		factor = 7.0 / 4.0
		img = enhancer.enhance(factor)

		imgBg = imgBg.filter(ImageFilter.BLUR)
		imgBg = imgBg.filter(ImageFilter.MinFilter(3))
	

		img = Image.alpha_composite(img,imgBg)
		img = Image.alpha_composite(img,imgTxt)
		
		img = img.convert('RGB') # conversion to RGB
		img = img.convert('P', palette=Image.ADAPTIVE, colors=126)
		img = img.convert('RGB')

		img.save("%s_mod.png"%self.tmpPath)

		modifyd+=1
		modifydFiles.append(self.fullPathDest)
			
	def extractImage( self ):
		cmd = "imgkap -p RGB \"%s\" \"%s.png\"" % (self.tmpPath, self.tmpPath)
		os.system(cmd)
					
	def mkcopy(self, srcFile, destFile):
		try:
			f = open( srcFile )
			s = []
			while True:
				l = f.readline()
				if l:
					s.append(l)
				else:
					break

			fa = FileActs()
			fa.writeFile(destFile, "".join(s))
			return True
		except:
			return False
			
			
	def analize(self):
		f = open( self.fullPath )
		print "analize ... [%s]" % self.fullPath

		while True:
			l = f.readline()
			if l:
				self.parse( l )	
				if len(self.refs) == 4:
					break
			else:
				return 0
				

	def parse(self, line):	

		if line[:7] == "KNP/SC=":
			t = line[7:].split(",")
			self.scale = int( t[0] )
		
		if line[:4] == "REF/":
			t = line[4:-2].split(",")
			self.refs.append( KapRefCon(t[1], t[2], t[3], t[4]) )
			#print t
			x = int( t[1] )
			y = int( t[2] )
			lat = float( t[3] )
			lon = float( t[4] )

			if self.x0 == None:
				self.x0 = x
				self.y0 = y 
				self.lat0 = lat
				self.lon0 = lon
				self.x1 = x
				self.y1 = y 
				self.lat1 = lat
				self.lon1 = lon

			if self.x0 >= x and self.y0 >= y:
				self.x0 = x
				self.y0 = y
				self.lat0 = lat
				self.lon = lon

			if self.x1 <= x and self.y1 <= y:
				self.x1 = x
				self.y1 = y 
				self.lat1 = lat
				self.lon1 = lon
				
class KapMaker:
	def __init__(self,config, pointsForMaps, makeOnlyTestArea,action=""):
		print "KapMaker init"

		self.config = config
		self.pointsForMaps = pointsForMaps
		self.makeOnlyTestArea = makeOnlyTestArea
		self.action = action
		#print self.pointsForMaps
		
		self.files = []
		
		print "chk directorys..."
		if self.chkDirs() == False:
			sys.exit(1)

		print "prepare file list"
		if self.makeFileList () == False:
			sys.exit(1)

			
	def chkDirs(self):
		ds = os.path.isdir(self.config['kapFilesPathSource'])
		if ds == True:
			print "source directory OK"
		else:
			return False

		dd = os.path.isdir(self.config['kapFilesPathDestination'])
		if dd == True:
			print "destination directory OK"
		else:
			return False

		return True	
		
		
	def makeFileList(self):
		global boxColector, modifyd,modifydFiles
		
		src = self.config['kapFilesPathSource']
		d = os.listdir(src)
		a = 0
		for f in d:
			a+=1	#debug
			if True:
				fp = os.path.join(src, f)
				if os.path.isfile( fp ):
					boxColector = []
					t = fp.split(".")
					if t[-1].lower() == "kap" and \
						(self.makeOnlyTestArea == False or ( self.makeOnlyTestArea and t[-2][-4:]=="7-22" ) ):
						kf = KapFile(src, f, self.pointsForMaps, 
							self.config['kapFilesPathDestination'],
							action=self.action)
						self.files.append( kf )

					
		print "found %s .kap files in source directory" % len(self.files)
		print "modifyd %s files" % modifyd
		print modifydFiles
		if len( self.files ) == 0:
			return False

		return True
		



		