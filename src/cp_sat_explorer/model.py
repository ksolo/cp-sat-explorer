import math
from copy import deepcopy
from typing import Tuple, Callable, List
from dataclasses import dataclass

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
    def propagate(self) -> bool:
        raise NotImplementedError


class LinearConstraint(Constraint):
    def __init__(self, terms: Tuple[int, Variable], operator: Callable, bound: int):
        self.terms = terms
        self.operator = operator
        self.bound = bound
    
    @property
    def variables(self):
        return [term[1] for term in self.terms]


    def propagate(self) -> bool:
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


    def propagate(self):
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


@dataclass
class TrailEntry:
    variable: Variable
    constraint: Constraint
    value: int
    level: int


@dataclass
class NoGood:
    literals: List[Tuple[str, int]]
    

class Solver:
    def __init__(self, model: CSPModel):
        self.model = model
        self.trail_entries = []
        self.no_goods = []
        self.level = 0
        self.variables = {
            var.name: var
            for var in self.model.variables
        }


    def propagate_all(self) -> bool:
        while True:
            changed = False
            domains = {var.name: deepcopy(var.domain) for var in self.model.variables}

            self.propagate_no_goods()
            for constraint in self.model.constraints:
                result = constraint.propagate()
                if not result:
                    return False # contradition was found - cannot be solved
                
                for var in constraint.variables:
                    if domains[var.name] != var.domain:
                        changed = True
                        if var.is_assigned():
                            self.trail_entries.append(
                                TrailEntry(
                                    variable=var,
                                    constraint=constraint,
                                    value=var.assigned_val(),
                                    level=self.level
                                )
                            )
            
            if not changed:
                break

        return True

        
    def propagate_no_goods(self):
        


    def _set_no_goods(self):
        decisions = [entry for entry in self.trail_entries if entry.constraint is None]
        no_good = NoGood(literals=[
            (entry.variable.name, entry.variable.assigned_val())
            for entry in decisions
        ])
        self.no_goods.append(no_good)

        
    def solve(self) -> bool:
        if not self.propagate_all():
            self._set_no_goods()
            return False

        if all([var.is_assigned() for var in self.model.variables]):
            return True 
        
        min_domain = float(math.inf)
        min_var = None
        for var in self.model.variables:
            if var.is_assigned():
                continue

            domain_len = len(var.domain)
            if domain_len < min_domain:
                min_domain = domain_len
                min_var = var
        
        for val in list(min_var.domain):
            self.level += 1
            domains = {var.name: deepcopy(var.domain) for var in self.model.variables}
            min_var.domain = {val}
            self.trail_entries.append(
                TrailEntry(
                    variable=min_var,
                    value=val,
                    constraint=None,
                    level=self.level
                )
            )

            if self.solve():
                return True

            for var in self.model.variables:
                var.domain = domains[var.name]
        
            self.trail_entries = [e for e in self.trail_entries if e.level < self.level]
            self.level -= 1

        return False