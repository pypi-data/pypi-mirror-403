from .exceptions import OwnershipError
import inspect
import threading

class GlobalStore:
    def __init__(self):
        self._values = {}    
        self._owners = {}    
        self._declared_in = {} 
        self._lock = threading.Lock()

    def set(self, key, value, owner=None):
        frame = inspect.currentframe().f_back
        locals_ = frame.f_locals

        # 🟡 Declaration inside class body
        if '__qualname__' in locals_ and owner is None:
            class_name = locals_['__qualname__']
            with self._lock:
                if key not in self._declared_in:
                    self._declared_in[key] = class_name
                    self._values[key] = value
            return

        # ❌ BLOCK global update for class-owned keys
        if owner is None:
            if key in self._declared_in:
                raise OwnershipError(
                f"\n[StrictStore] Write blocked for key '{key}'\n"
                f"Owner class : {self._declared_in[key]}\n\n"
                f"Reason:\n"
                f"- This key was declared inside a class body.\n\n"
                f"Fix:\n"
                f"- Update the key using an instance of '{self._declared_in[key]}'\n"
            )

            with self._lock:
                self._values[key] = value
            return

        # 🔵 Instance update (allowed only for owner class)
        owner_cls = owner.__class__
        with self._lock:
            declared = self._declared_in.get(key)
            if declared and declared != owner_cls.__name__:
                raise OwnershipError(
                    f"\n[StrictStore] Ownership violation for key '{key}'\n"
                    f"Declared in : {declared}\n"
                    f"Updater     : {owner_cls.__name__}\n\n"
                    f"Reason:\n"
                    f"- Only the declaring class may update this key.\n\n"
                    f"Fix:\n"
                    f"- Use an instance of '{declared}' to update '{key}'\n"
                )

            self._owners[key] = owner_cls
            self._values[key] = value


    def get(self, key, default=None):
        return self._values.get(key, default)
