#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Oct 30 13:24:54 2020

@author: csmith
"""

    
import unittest

#python test runners 

separate unit tests from integration tests 
pgrad/tests/unit/__init__.py
pgrad/tests/unit/test_sum.py
pgrad/tests/integration/__init__.py
pgrad/tests/integration/test_integration.py
pgrad/tests/integration/fixtures/test_basic.json
pgrad/tests/integration/fixtures/test_complex.json



class TestSum(unittest.TestCase):

    def test_sum(self):
        self.assertEqual(sum([1, 2, 3]), 6, "Should be 6")

    def test_sum_tuple(self):
        self.assertEqual(sum((1, 2, 2)), 6, "Should be 6")

if __name__ == '__main__':
    unittest.main()

# create a folder called tests
# create tests tests/test_*.py
# target = __import__("my_sum.py")
# sum = target.sum

# file test.py 

import unittest

from my_sum import sum


class TestSum(unittest.TestCase): # subclass unittest.TestCase
    def test_list_int(self):
        """
        Test that it can sum a list of integers
        """
        data = [1, 2, 3]
        result = sum(data)
        self.assertEqual(result, 6)

if __name__ == '__main__':
    unittest.main() # runs all tests that start with test_*
    
# from cli python test.py runs unittest.main()    
    
unittest will cd to src/ dir, scan for all test*py files in tests/ dir
and execute them 
python -m unittest discover -s tests -t src

# assertions
# .assertEqual(a,b) 
# .assertTrue(boolean)    
# .assertIsNone(var)    
# .assertIn(a,b)
# .assertIsInstance(a,b)

travis CI - every time you commit travis will run the following  
.travia.yml file contains the following 
language: python
python:
  - "3.7"
install:
  - pip install -r requirements.txt
script:
  - python -m unittest discover
  
    


    
