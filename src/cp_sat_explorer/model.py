import math
from typing import Tuple, Callable, List

# Operators
def lte(val, bound) -> bool:
    return val <= bound


def gte(val, bound) -> bool:
    return val >= bound


def eq(val, bound) -> bool:
    return val == bound


class Variable:
    def __init__(self, name:str, min_val: int, max_val: int):
        self.name = name
        self.domain = {val for val in range(min_val, max_val + 1)}
    
    def is_assigned(self) -> bool:
        return len(self.domain) == 1

    def assigned_val(self) -> int:
        if self.is_assigned():
            return next(iter(self.domain))
        return None

    def __repr__(self):
        if self.is_assigned():
            return f"{self.name}={self.assigned_val()}"
        return f"{self.name}∈{sorted(self.domain)}"
    

class Constraint:
    def propogate(self) -> bool:
        raise NotImplementedError


class LinearConstraint(Constraint):
    def __init__(self, terms: Tuple[int, Variable], operator: Callable, bound: int):
        self.terms = terms
        self.operator = operator
        self.bound = bound

    def propogate(self) -> bool:
        if self.operator == lte:
            total = 0
            for term in self.terms:
                if term[0] > 0:
                    total += term[0] * min(term[1].domain)
                else:
                    total += term[0] * max(term[1].domain)

            if self.operator(total, self.bound):
                for term in self.terms:
                    if term[0] > 0:
                        max_var = (self.bound - (total - (term[0] * min(term[1].domain)))) // term[0]
                        if max_var < max(term[1].domain):
                            term[1].domain = {val for val in term[1].domain if val <= max_var}
                    else:
                        min_var = math.ceil((self.bound - (total - (term[0] * max(term[1].domain)))) / term[0])
                        if min_var > min(term[1].domain):
                            term[1].domain = {val for val in term[1].domain if val >= min_var}
                return True
        if self.operator == gte:
            return True

        if self.operator == eq:
            return True
    

class AllDifferentConstraint(Constraint):
    def __init__(self, variables:List[Variable]):
        self.variables = variables


    def propogate(self):
        assignments = {var.name: var.assigned_val() for var in self.variables if var.is_assigned()}

        if not len(assignments):
            return True

        if len(set(assignments.values())) != len(assignments.values()):
            # we have a duplicate
            return False
        
        for name, assignment in assignments.items():
            for var in self.variables:
                if var.is_assigned():
                    continue
                var.domain.discard(assignment)
        
        return not any([len(var.domain) == 0 for var in self.variables])


class CSPModel:

    def __init__(self):
        self.variables = []
        self.constraints = []
    

    def new_int_var(self, name:str, lb: int, up: int) -> Variable:
        var = Variable(name=name, min_val=lb, max_val=up)
        self.variables.append(var)
        
        return var
    

    def add_constraint(self, constraint: Constraint):
        self.constraints.append(constraint)
    
