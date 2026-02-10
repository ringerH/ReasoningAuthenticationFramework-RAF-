# src/evaluation/oracle.py

class ICCROracle:
    def __init__(self, problem_data: dict):
        self.problem = problem_data
        self.operands = problem_data['operands']
        self.structure = problem_data['structure_masked']
        self.calls_made = 0
        
    def get_structure(self) -> str:
        self.calls_made += 1
        return self.structure
    
    def get_operand(self, index: int) -> str:
        self.calls_made += 1
        try:
            return str(self.operands[int(index)])
        except (IndexError, ValueError):
            return "ERROR"