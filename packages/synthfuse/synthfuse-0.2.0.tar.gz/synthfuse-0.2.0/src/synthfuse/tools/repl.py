"""
Interactive ALCHEM-J spell REPL
Usage:  python -m synthfuse.tools.repl
"""
import cmd
import jax
import jax.numpy as jnp
from synthfuse.alchemj import compile_spell
from synthfuse.recipes import get_recipe   # central index

BANNER = r"""
     ░█▄█░█▀█░█▀▀░█░█░█▀▄ █▀▀░█▀█░█▀▄
     ░█░█░█▀█░█░░░█░█░█▀▄ █▀▀░█▀█░█▀▄
     ░▀░▀░▀ ▀░▀▀▀░▀▀▀░▀ ▀ ▀▀▀░▀ ▀░▀ ▀
     Synth-Fuse  ‑  Interactive Spell Casting
     Type help or ? for commands.
"""


class AlchemJREPL(cmd.Cmd):
    intro = BANNER
    prompt = "alj ⭢ "

    def __init__(self):
        super().__init__()
        self._step_fn = None
        self._state = None
        self._key = jax.random.PRNGKey(0)

    # ------- helpers ----------------------------------------------
    def _compile(self, source: str):
        try:
            return compile_spell(source)
        except Exception as e:
            print(f"[err] {e}")
            return None

    def _ensure_state(self, shape=(10,)):
        if self._state is None:
            self._state = dict(x=jnp.zeros(shape))

    # ------- commands ---------------------------------------------
    def do_compile(self, arg: str):
        """compile <spell>  – build JIT kernel"""
        if not arg:
            print("need spell string")
            return
        self._step_fn = self._compile(arg)
        if self._step_fn:
            print("[ok] JIT compiled")

    def do_recipe(self, arg: str):
        """recipe <name>  – load pre-built recipe"""
        if not arg:
            print("available:", ", ".join(get_recipe.list()))
            return
        try:
            spell = get_recipe(arg)
            self._step_fn = self._compile(spell)
            if self._step_fn:
                print(f"[ok] recipe '{arg}' loaded")
        except KeyError:
            print("[err] unknown recipe")

    def do_run(self, arg: str):
        """run [n=1]  – execute compiled spell n times"""
        if self._step_fn is None:
            print("[err] nothing compiled")
            return
        n = int(arg) if arg else 1
        self._ensure_state()
        for i in range(n):
            self._key, sub = jax.random.split(self._key)
            self._state = self._step_fn(sub, self._state, {})
        print(f"[ok] ran {n} step(s)  –  x[:5] =", self._state["x"][:5])

    def do_shape(self, arg: str):
        """shape [dims]  – resize latent state"""
        dims = tuple(map(int, arg.split())) if arg else (10,)
        self._state = dict(x=jnp.zeros(dims))
        print(f"[ok] state shape → {dims}")

    def do_params(self, arg: str):
        """params key=val ...  – update parameter dict"""
        if not arg:
            print("usage: params alpha=1.5 scale=0.1")
            return
        pairs = arg.split()
        new_p = {}
        for p in pairs:
            k, v = p.split("=", 1)
            try:
                new_p[k] = float(v)
            except ValueError:
                new_p[k] = v
        # store inside state for next run
        if "params" not in (self._state or {}):
            self._ensure_state()
        self._state.setdefault("params", {}).update(new_p)
        print("[ok] params updated")

    def do_symbols(self, _):
        """symbols  – list registered primitives"""
        from synthfuse.alchemj.registry import _REGISTRY
        print("symbols:", " ".join(sorted(_REGISTRY.keys())))

    def do_reset(self, _):
        """reset  – zero state & new PRNG key"""
        self._state = None
        self._key = jax.random.PRNGKey(0)
        print("[ok] reset")

    def do_quit(self, _):
        """quit"""
        print("✦  see you in the latent space")
        return True

    def emptyline(self):
        pass

    def default(self, line: str):
        # treat bare line as spell to compile & run once
        if line.strip():
            self.do_compile(line)
            if self._step_fn:
                self.do_run("1")


# ------------------------------------------------------------------
# 6.  Entry
# ------------------------------------------------------------------
def main():
    AlchemJREPL().cmdloop()


if __name__ == "__main__":
    main()