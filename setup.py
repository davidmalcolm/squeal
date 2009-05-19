#from ez_setup import use_setuptools
#use_setuptools()
from setuptools import setup, find_packages

setup(name="squeal",
      version="0.4",
      description="SQL-style querying for the command line",
      author="David Malcolm",
      author_email="dmalcolm@redhat.com.com",
      packages=find_packages(exclude='tests'),
      scripts=['squeal.py']
      )

