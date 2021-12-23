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

def test_arithmetic(runner):
    for _ in range(3):
        operand1 = random.randint(1, 20)
        operand2 = random.randint(1, 20)
        
        assert runner(f"{operand1} add {operand2}") == operand1 + operand2
        assert runner(f"{operand1} sub {operand2}") == operand1 - operand2
        assert runner(f"{operand1} mul {operand2}") == operand1 * operand2
        assert runner(f"{operand1} div {operand2}") == operand1 / operand2

def test_reference(runner):
    assert runner("var") == "unknown identifier :^("
    
    runner("var bind 40")
    
    assert runner("var") == 40
    
    runner("var bind (var mul 2)")
    
    assert runner("var") == 80
    
def test_function(runner):
    runner("""
        double_then_add bind ((a link b) function (
            (a mul 2) add b
        ))       
    """)
    
    assert runner("4 double_then_add 2") == 10
    
    assert runner("2 ((a link b) function (a add b add b)) 3") == 8