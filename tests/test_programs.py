import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import random

import main
import smile

@pytest.fixture
def runner():
    global_frame = smile.create_global_frame()
    
    def runner(line):
        return main.run(line, global_frame)
        
    return runner

def test_simple(runner):
    runner("""
        (a bind 1) link
        (b bind 2) link 
        (c bind (a add b)) link 
        (d bind ((a link b) function (
            a add b mul 2
        )))       
    """)
    
    assert runner("c") == 3
    assert runner("5 d 5") == 20
    
def test_sum_recursive(runner):
    runner("""
        func bind ((a link b) function (
            (a add ((a sub 1) func b)) if (a greater 0)
        ))       
    """) # recursively add 1..a
    
    assert runner("6 func 5") == 21