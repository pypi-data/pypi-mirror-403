import os, json

class MathCore:
    def __init__(self, base_dir):
        self.mem_file = os.path.join(base_dir, "memory.json")
        self.memory = self._load_memory()

    def _load_memory(self):
        if os.path.exists(self.mem_file):
            with open(self.mem_file, 'r') as f: return json.load(f)
        return {}

    def _save_memory(self):
        with open(self.mem_file, 'w') as f: json.dump(self.memory, f)

    def solve(self, expr):
        if "=" in expr and "==" not in expr:
            var_name, val = expr.split("=")
            try:
                calc_val = eval(val, {"__builtins__": None}, self.memory)
                self.memory[var_name.strip()] = calc_val
                self._save_memory()
                return f"Stored: {var_name.strip()} = {calc_val}"
            except Exception as e: return f"Assignment Error: {e}"
        else:
            try:
                clean_expr = expr.replace("×", "*").replace("÷", "/")
                result = eval(clean_expr, {"__builtins__": None}, self.memory)
                return f"Result: {result}"
            except Exception as e: return f"Math Error: {e}"

