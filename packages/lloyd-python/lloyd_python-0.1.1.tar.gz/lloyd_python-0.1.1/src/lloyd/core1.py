import sys, os, shutil
from lloyd.core2 import MathCore

class LloydCore:
    def __init__(self):
        self.base_dir = os.path.expanduser("~/lloyd_project")
        self.tgt_dir = os.path.join(self.base_dir, "tgt")
        if not os.path.exists(self.tgt_dir): os.makedirs(self.tgt_dir)
        
        self.math_engine = MathCore(self.base_dir)

        # The Full Legit Vocabulary
        self.vocabulary = {
            "info": "Lists vocabulary.",
            "ma": "Math/Variables. Usage: ma {x=10}",
            "math": "Math/Variables.",
            "sea": "Search files. Usage: sea {tgt}",
            "search": "Search files.",
            "dl": "Download file to tgt. Usage: dl {source}",
            "download": "Download file.",
            "ac": "Access/Read file. Usage: ac {filename}",
            "access": "Access/Read file.",
            "ex": "Execute command. Usage: ex {ls -la}",
            "execute": "Execute command.",
            "name": "Rename file in tgt. Usage: name {old > new}",
            "rename": "Rename file.",
            "bk": "Backup terminal.",
            "backup": "Backup terminal."
        }

    def _strip(self, arg): return arg.strip("{}").strip()

    def ma(self, arg):
        print(self.math_engine.solve(self._strip(arg)))

    def sea(self, arg):
        p = self._strip(arg)
        target = self.tgt_dir if p == "tgt" else p
        if os.path.exists(target):
            for i in os.listdir(target): print(f" - {i}")
        else: print("Path not found.")

    def dl(self, arg):
        s = self._strip(arg)
        if os.path.exists(s):
            shutil.copy2(s, os.path.join(self.tgt_dir, os.path.basename(s)))
            print(f"Captured {os.path.basename(s)}")

    def ac(self, arg):
        p = os.path.join(self.tgt_dir, self._strip(arg))
        if os.path.exists(p):
            with open(p, 'r', errors='ignore') as f: print(f.read())
        else: print("File not found in tgt.")

    def ex(self, arg):
        os.system(self._strip(arg))

    def name(self, arg):
        clean = self._strip(arg)
        if ">" in clean:
            old, new = [x.strip() for x in clean.split(">")]
            old_p, new_p = os.path.join(self.tgt_dir, old), os.path.join(self.tgt_dir, new)
            if os.path.exists(old_p):
                os.rename(old_p, new_p)
                print(f"Renamed {old} to {new}")
            else: print(f"Error: {old} not found.")

    def info(self, arg=""):
        clean = self._strip(arg)
        if not clean:
            print("--- Lloyd Unified System ---")
            for word in sorted(set(self.vocabulary.keys())): print(f"Word: {word}")
        else:
            print(f"Function: {self.vocabulary.get(clean, 'Unknown')}")

    def bk(self, _=None):
        os.system(os.path.expanduser("~/.tmux/plugins/tmux-resurrect/scripts/save.sh"))

def main():
    l = LloydCore()
    if len(sys.argv) < 2: l.info(); return
    cmd, arg = sys.argv[1], (sys.argv[2] if len(sys.argv) > 2 else "")
    
    # Mapping every word and its short version
    actions = {
        "info": l.info, "ma": l.ma, "math": l.ma, 
        "sea": l.sea, "search": l.sea, "dl": l.dl, "download": l.dl,
        "ac": l.ac, "access": l.ac, "ex": l.ex, "execute": l.ex,
        "name": l.name, "rename": l.name, "bk": l.bk, "backup": l.bk
    }
    
    if cmd in actions: actions[cmd](arg)
    else: print(f"Unknown: {cmd}")

if __name__ == "__main__": main()
0
