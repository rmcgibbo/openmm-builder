import sys
try:
    # use setuptools if it is available, as it lets people
    # use setup.py develop, and keeps records for uninstall
    from setuptools import setup
except ImportError:
    # but it's not strictly necessary. distutils will work
    # fine for most people
    from distutils.core import setup


if sys.argv[1] in ['install', 'develop']:
    requirements = ['pystache', 'traits', 'traitsui']
    for r in requirements:
        try:
            __import__(r)
        except ImportError:
            print('#'*75)
            print('WARNING: openmm-builder requires %s' % r)
            print('%s can be downloaded from:' % r)
            print('    https://pypi.python.org/pypi/%s' % r)
            print('#'*75)
        

setup(name='openmm-qtbuilder',
      version='0.1',
      author='Robert McGibbon',
      license='GPLv3',
      scripts=['openmm-builder'])
