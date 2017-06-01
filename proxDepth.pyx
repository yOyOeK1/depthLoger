
def proxDepth(p0, p1,density, d):
	#cdef int d = dist	
		
	if p0.depth<40.0 and d>200:
		return True	
	if p0.depth>=40.0 and d>400:
		return True	
	if p0.depth<20.0 and d>60:
		return True
	if p0.depth<10.0 and d>(18*density):
		return True

	cdef float depthDiff = float(1.18)
	
	if( d > (10*density) and ( \
			( p0.depth > p1.depth and (p0.depth/p1.depth)>depthDiff ) or \
			( p0.depth < p1.depth and (p1.depth/p0.depth)>depthDiff ) \
			)  
		):
		return True
		
	return False