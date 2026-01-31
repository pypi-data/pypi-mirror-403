import random
from .encryption import method1, method2, method3

class PyxBlend:
    def __init__(self):
        self.methods = {
            1: method1.encrypt,
            2: method2.encrypt,
            3: method3.encrypt
        }

    def encrypt(self, code, method=1):
        if method not in self.methods:
            raise ValueError(f"Method {method} not found. Available methods: 1, 2, 3")
        
        result = self.methods[method](code)
        if result is None:
            raise RuntimeError(f"Encryption failed for method {method}.")
            
        return result

    def m1(self, code): return self.encrypt(code, 1)
    def m2(self, code): return self.encrypt(code, 2)
    def m3(self, code): return self.encrypt(code, 3)

    def random_encrypt(self, code, iterations=1):
        current_code = code
        safe_methods = [method1.encrypt, method2.encrypt]
        
        for _ in range(iterations):
            enc_func = random.choice(safe_methods)
            current_code = enc_func(current_code)
            
        return current_code
