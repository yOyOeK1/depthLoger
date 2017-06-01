
# several files with ext .pyx, that i will call by their name
from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext

ext_modules=[
    Extension("proxDepth",       ["proxDepth.pyx"]),
    Extension("LatLon",         ["LatLon.pyx"]),
	Extension("PomHelper",		["PomHelper.pyx"]),
	Extension("PointOfMesure",  ["PointOfMesure.pyx"])
]

setup(
  name = 'MyProject',
  cmdclass = {'build_ext': build_ext},
  ext_modules = ext_modules,
)