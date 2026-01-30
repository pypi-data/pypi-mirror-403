from .values import SuperValue, AggregateValue
from .nodes import *
from .environment import Environment
import itertools

class Instance:
    def __init__(self, class_def):
        self.class_def = class_def
        self.env = Environment()

    def get_method(self, name):
        if name in self.class_def.methods:
            return self.class_def.methods[name]
        raise AttributeError(f"Method {name} not found")

    def copy(self):
        new_inst = Instance(self.class_def)
        new_inst.env.vars = {
            k: SuperValue(v.values.copy()) 
            for k, v in self.env.vars.items()
        }
        if hasattr(self.env, "protected"):
            new_inst.env.protected = set(self.env.protected)
        return new_inst

    def __repr__(self):
        return f"<{self.class_def.name} Instance>"


class ReturnException(Exception):
    def __init__(self, value):
        self.value = value


# --------------------------------------------------
# Utility: Zip logic helper
# --------------------------------------------------
def zip_values(list_a, list_b):
    len_a = len(list_a)
    len_b = len(list_b)
    max_len = max(len_a, len_b)
    
    out_a = []
    out_b = []
    
    for i in range(max_len):
        out_a.append(list_a[i % len_a])
        out_b.append(list_b[i % len_b])
        
    return out_a, out_b, max_len

# --------------------------------------------------
# Utility: expand environment
# --------------------------------------------------
def expand_env(env: Environment):
    if not env.vars:
        return [env]

    max_len = 1
    for v in env.vars.values():
        if len(v.values) > max_len:
            max_len = len(v.values)

    worlds = []
    for i in range(max_len):
        nw = Environment()
        if hasattr(env, "protected"):
            nw.protected = set(env.protected)

        for name, superval in env.vars.items():
            idx = i % len(superval.values)
            val = superval.values[idx]
            if isinstance(val, Instance):
                val = val.copy()
            nw.vars[name] = SuperValue([val])
        
        worlds.append(nw)

    return worlds

# --------------------------------------------------
# Core evaluator
# --------------------------------------------------
def eval_node(node, env):

    if isinstance(node, Block):
        for stmt in node.statements:
            eval_node(stmt, env)
        return None

    # --- Declarations ---
    if isinstance(node, ClassDef):
        env.set(node.name, SuperValue([node]))
        return None

    if isinstance(node, FuncDef):
        env.set(node.name, SuperValue([node]))
        return None

    if isinstance(node, Let):
        val = eval_node(node.expr, env)
        env.set(node.name, val)
        return val

    # --- Superposition & Aggregation ---
    if isinstance(node, Superpose):
        values = []
        for item in node.values:
            values.extend(eval_node(item, env).values)
        return SuperValue(values)

    if isinstance(node, Aggregate):
        val = eval_node(node.expr, env)
        return SuperValue([AggregateValue(val)])

    # --- Functions & Methods ---
    if isinstance(node, FuncCall):
        func_super = env.get(node.name)
        arg_supers = [eval_node(a, env) for a in node.args]

        max_len = 1
        if arg_supers:
            max_len = max(len(s.values) for s in arg_supers)

        results = []
        for i in range(max_len):
            concrete_args = []
            for s in arg_supers:
                concrete_args.append(s.values[i % len(s.values)])

            for item in func_super.values:
                # Constructor Logic
                if isinstance(item, ClassDef):
                    inst = Instance(item)
                    if "init" in item.methods:
                        m = item.methods["init"]
                        m_env = Environment()
                        m_env.vars = inst.env.vars
                        for p, a in zip(m.params, concrete_args):
                            m_env.set(p, SuperValue([a]))
                        try:
                            for stmt in m.body.statements:
                                eval_node(stmt, m_env)
                        except ReturnException:
                            pass
                    results.append(inst)
                
                # Function Logic
                elif isinstance(item, FuncDef):
                    f_env = Environment()
                    # Shallow copy globals for now
                    f_env.vars = {k: v for k, v in env.vars.items()}
                    for p, a in zip(item.params, concrete_args):
                        f_env.set(p, SuperValue([a]))
                    
                    try:
                        eval_node(item.body, f_env)
                        results.append(None) # No return
                    except ReturnException as r:
                        results.extend(r.value.values)

        return SuperValue(results)
    
    if isinstance(node, MethodCall):
        insts = eval_node(node.instance, env)
        args = [eval_node(a, env) for a in node.args]
        out = []

        for inst in insts.values:
            m = inst.get_method(node.method_name)
            
            # Cartesian Product for Search
            arg_values = [a.values for a in args]
            if not arg_values: 
                arg_product = [()]
            else:
                arg_product = list(itertools.product(*arg_values))

            new_state_map = {} 
            inst_depth = max(len(v.values) for v in inst.env.vars.values()) if inst.env.vars else 1
            
            for concrete_args in arg_product:
                for i in range(inst_depth):
                    m_env = Environment()
                    for k, v in inst.env.vars.items():
                        val = v.values[i % len(v.values)]
                        m_env.vars[k] = SuperValue([val])

                    for p, a in zip(m.params, concrete_args):
                        m_env.set(p, SuperValue([a]))
                        m_env.protected.add(p) 

                    try:
                        for s in m.body.statements:
                            eval_node(s, m_env)
                    except ReturnException as r:
                        out.extend(r.value.values)

                    for k, v in m_env.vars.items():
                        if k not in m.params:
                            new_state_map.setdefault(k, []).extend(v.values)
            
            inst.env.vars = {k: SuperValue(v) for k, v in new_state_map.items()}

        return SuperValue(out)

    # --- Assignments & Ops ---
    if isinstance(node, Assign):
        val = eval_node(node.expr, env)
        env.set(node.name, val)
        return val

    if isinstance(node, Var):
        return env.get(node.name)

    if isinstance(node, Number):
        return SuperValue([node.value])
    
    if isinstance(node, String):
        return SuperValue([node.value])

    if isinstance(node, BinOp):
        l = eval_node(node.left, env)
        r = eval_node(node.right, env)
        l_vals, r_vals, _ = zip_values(l.values, r.values)
        res = []
        for x, y in zip(l_vals, r_vals):
            if node.op == "+": res.append(x + y)
            if node.op == "-": res.append(x - y)
            if node.op == "*": res.append(x * y)
            if node.op == "/": res.append(x / y)
        return SuperValue(res)

    if isinstance(node, Compare):
        l = eval_node(node.left, env)
        r = eval_node(node.right, env)
        l_vals, r_vals, _ = zip_values(l.values, r.values)
        res = []
        for x, y in zip(l_vals, r_vals):
            if node.op == "==": res.append(x == y)
            elif node.op == "!=": res.append(x != y)
            elif node.op == ">": res.append(x > y)
            elif node.op == "<": res.append(x < y)
            elif node.op == ">=": res.append(x >= y)
            elif node.op == "<=": res.append(x <= y)
        return SuperValue(res)

    if isinstance(node, Return):
        raise ReturnException(eval_node(node.expr, env))

    if isinstance(node, Observe):
        val = eval_node(node.expr, env)
        print(f"OBSERVED: {val}")
        return val

    # --- Control Flow ---
    if isinstance(node, If):
        concrete_worlds = expand_env(env)
        true_worlds = []
        false_worlds = []

        for w in concrete_worlds:
            cond = eval_node(node.condition, w)
            if any(v is True for v in cond.values):
                true_worlds.append(w)
            else:
                false_worlds.append(w)

        result_worlds = []
        for w in true_worlds:
            eval_node(node.true_body, w)
            result_worlds.append(w)

        if node.false_body:
            for w in false_worlds:
                eval_node(node.false_body, w)
                result_worlds.append(w)
        else:
            result_worlds.extend(false_worlds)

        merged = {}
        for w in result_worlds:
            for name, val in w.vars.items():
                merged.setdefault(name, []).extend(val.values)

        env.vars = {k: SuperValue(v) for k, v in merged.items()}
        return None

    if isinstance(node, Repeat):
        count_super = eval_node(node.count, env)
        limit = int(max(count_super.values)) if count_super.values else 0
        for _ in range(limit):
             eval_node(node.body, env)
        return None

    if isinstance(node, Where):
        # Desugar 'where' into 'select' statements
        for stmt in node.body.statements:
            sel = Select(node.target, stmt)
            eval_node(sel, env)
        return None

    if isinstance(node, GetAttr):
        insts = eval_node(node.instance, env)
        out = []
        for inst in insts.values:
            val = inst.env.get(node.name)
            out.extend(val.values)
        return SuperValue(out)

    if isinstance(node, Select):
        target_val = env.get(node.target)
        
        # --- GLOBAL PRUNING (X) ---
        if target_val.values and isinstance(target_val.values[0], AggregateValue):
            agg = target_val.values[0]
            surviving_indices = []
            
            # Check which indices in the aggregate pass the condition
            for i, val in enumerate(agg.values):
                cond_env = Environment()
                cond_env.vars = env.vars.copy()
                
                # Context variables available inside 'select X'
                cond_env.set("value", SuperValue([val]))
                cond_env.set("freq", SuperValue([agg.freq(val)]))
                # Add min/max check logic if needed
                
                res = eval_node(node.condition, cond_env)
                if any(v is True for v in res.values):
                    surviving_indices.append(i)

            # Prune ALL variables in the environment
            for name, superval in env.vars.items():
                if isinstance(superval.values[0], AggregateValue): continue
                
                # Filter strict to surviving indices
                new_vals = []
                for idx in surviving_indices:
                    if idx < len(superval.values):
                        new_vals.append(superval.values[idx])
                
                # If variable was constant (len 1), keep it constant
                if len(superval.values) == 1 and len(surviving_indices) > 0:
                    pass # Don't prune constants
                else:
                    superval.values = new_vals

            return None

        # --- LOCAL PRUNING (Standard) ---
        survivors = []
        original_super = target_val

        for item in original_super.values:
            saved_env = {k: SuperValue(v.values.copy()) for k, v in env.vars.items()}
            env.vars = {k: SuperValue(v.values.copy()) for k, v in saved_env.items()}
            env.set(node.target, SuperValue([item]))

            result = eval_node(node.condition, env)
            env.vars = saved_env

            if isinstance(item, Instance):
                keep_indices = [i for i, val in enumerate(result.values) if val is True]
                
                if keep_indices:
                    new_inst = item.copy()
                    for k, v in new_inst.env.vars.items():
                        current_vals = v.values
                        if len(current_vals) < len(result.values):
                             current_vals = list(itertools.islice(itertools.cycle(current_vals), len(result.values)))
                        if len(current_vals) >= len(result.values):
                            filtered = [current_vals[i] for i in keep_indices]
                            new_inst.env.vars[k] = SuperValue(filtered)
                    survivors.append(new_inst)
            else:
                if any(v is True for v in result.values):
                    survivors.append(item)

        env.set(node.target, SuperValue(survivors))
        return None

    # ---------- WHILE ----------
    if isinstance(node, While):
        worlds = expand_env(env)
        while True:
            continuing = []
            finished = []
            for w in worlds:
                cond = eval_node(node.condition, w)
                if any(v is True for v in cond.values):
                    continuing.append(w)
                else:
                    finished.append(w)
            if not continuing:
                worlds = finished
                break
            for w in continuing:
                # Body is now a block, handle statements
                for stmt in node.body.statements:
                    eval_node(stmt, w)
            worlds = continuing + finished
        merged = {}
        for w in worlds:
            for name, val in w.vars.items():
                merged.setdefault(name, []).extend(val.values)
        env.vars = {k: SuperValue(v) for k, v in merged.items()}
        return None

    return None