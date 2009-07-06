#from ez_setup import use_setuptools
#use_setuptools()
from setuptools import setup, find_packages

setup(name="squeal",
      version="0.4.1",
      description="SQL-style querying for the command line",
      url="https://fedorahosted.org/squeal/",
      author="David Malcolm",
      author_email="dmalcolm@redhat.com",
      packages=find_packages(exclude='tests'),
      scripts=['squeal.py']
      )

