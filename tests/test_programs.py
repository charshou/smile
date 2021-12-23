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
    """) # recursively add 1..a (ignore b)
    
    assert runner("6 func 5") == 21
    
def test_bigger(runner):
    runner("""
        (a bind 3) link 
        (b bind 12) link 
        (c bind ((x link y) function (
            (var1 bind 4) link
            (var2 bind 8) link
            (x add y add var1 add var2)
        ))) link
        (d eval (6 c 7))
    """)
    
    assert runner("d") == 25
    
def test_dot_product(runner): # create simple classes with function definitions
    runner("""
        (create_2d_vector bind ((x link y) function (
            (x link y)
        ))) link
        (dot bind ((v1 link v2) function (
            ((v1 get 0) mul (v2 get 0)) add ((v1 get 1) mul (v2 get 1))     
        )))  
    """)
    
    runner("""
        (v1 bind (3 create_2d_vector 4)) link
        (v2 bind (5 create_2d_vector 6)) link
        (result bind (v1 dot v2))
    """)
    
    assert runner("result") == 39