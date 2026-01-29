import ctypes
import os
import platform
import sys

# Constants
N = 768
BLOCK_SIZE = (N + 1) * 2  # 1538 bytes per bit

class EncryptionMode:
    STANDARD = 0
    METERED = 1

class AbhedyaError(Exception):
    pass

class Abhedya:
    def __init__(self, lib_path=None):
        if lib_path is None:
            # Try to find the library in standard locations or project structure
            suffix = ".dylib" if sys.platform == "darwin" else ".so"
            if sys.platform == "win32":
                suffix = ".dll"
            
            # Default to checking target/release if running from project root
            cwd = os.getcwd()
            potential_paths = [
                os.path.join(cwd, "target", "release", f"libabhedya_ffi{suffix}"),
                os.path.join(cwd, "..", "target", "release", f"libabhedya_ffi{suffix}"),
                f"./libabhedya_ffi{suffix}"
            ]
            
            found = False
            for path in potential_paths:
                if os.path.exists(path):
                    lib_path = path
                    found = True
                    break
            
            if not found:
                raise AbhedyaError(f"Could not locate libabhedya_ffi{suffix}. Please provide explicit path.")

        self.lib = ctypes.CDLL(lib_path)
        
        # Define Argument Types
        # abhedya_keygen(pk_buf, pk_len_ptr, sk_buf, sk_len_ptr)
        self.lib.abhedya_keygen.argtypes = [
            ctypes.POINTER(ctypes.c_ubyte), ctypes.POINTER(ctypes.c_size_t),
            ctypes.POINTER(ctypes.c_ubyte), ctypes.POINTER(ctypes.c_size_t)
        ]
        self.lib.abhedya_keygen.restype = ctypes.c_int
        
        # abhedya_encrypt(pk_buf, pk_len, msg_ptr, msg_len, mode, out_buf, out_len_ptr)
        self.lib.abhedya_encrypt.argtypes = [
            ctypes.POINTER(ctypes.c_ubyte), ctypes.c_size_t,
            ctypes.POINTER(ctypes.c_ubyte), ctypes.c_size_t,
            ctypes.c_int,
            ctypes.POINTER(ctypes.c_ubyte), ctypes.POINTER(ctypes.c_size_t)
        ]
        self.lib.abhedya_encrypt.restype = ctypes.c_int
        
        # abhedya_decrypt(sk_buf, sk_len, ct_ptr, ct_len, out_buf, out_len_ptr)
        self.lib.abhedya_decrypt.argtypes = [
            ctypes.POINTER(ctypes.c_ubyte), ctypes.c_size_t,
            ctypes.POINTER(ctypes.c_ubyte), ctypes.c_size_t,
            ctypes.POINTER(ctypes.c_ubyte), ctypes.POINTER(ctypes.c_size_t)
        ]
        self.lib.abhedya_decrypt.restype = ctypes.c_int

    def keygen(self):
        """Generates a keypair (pk, sk) as bytes."""
        # Estimate sizes
        # PK: (768^2 + 768) * 2 ~ 1.2MB
        # SK: 768 * 2 = 1.5KB
        
        pk_size = (N * N + N) * 2
        sk_size = N * 2
        
        pk_buf = (ctypes.c_ubyte * pk_size)()
        sk_buf = (ctypes.c_ubyte * sk_size)()
        
        pk_len = ctypes.c_size_t(pk_size)
        sk_len = ctypes.c_size_t(sk_size)
        
        res = self.lib.abhedya_keygen(
            pk_buf, ctypes.byref(pk_len),
            sk_buf, ctypes.byref(sk_len)
        )
        
        if res != 0:
            raise AbhedyaError(f"Keygen failed with code {res}")
            
        return bytes(pk_buf[:pk_len.value]), bytes(sk_buf[:sk_len.value])

    def encrypt(self, pk_bytes, message_bytes, mode=EncryptionMode.STANDARD):
        """Encrypts bytes using Public Key."""
        # Output size: num_bits * 1538
        num_bits = len(message_bytes) * 8
        max_out_size = num_bits * BLOCK_SIZE
        
        out_buf = (ctypes.c_ubyte * max_out_size)()
        out_len = ctypes.c_size_t(max_out_size)
        
        pk_buf = (ctypes.c_ubyte * len(pk_bytes)).from_buffer_copy(pk_bytes)
        msg_buf = (ctypes.c_ubyte * len(message_bytes)).from_buffer_copy(message_bytes)
        
        res = self.lib.abhedya_encrypt(
            pk_buf, len(pk_bytes),
            msg_buf, len(message_bytes),
            mode,
            out_buf, ctypes.byref(out_len)
        )
        
        if res != 0:
            raise AbhedyaError(f"Encryption failed with code {res}")
        
        return bytes(out_buf[:out_len.value])

    def decrypt(self, sk_bytes, ct_bytes):
        """Decrypts ciphertext using Secret Key."""
        # Output expected size
        if len(ct_bytes) % BLOCK_SIZE != 0:
            raise AbhedyaError("Invalid ciphertext length")
            
        num_bits = len(ct_bytes) // BLOCK_SIZE
        num_bytes = (num_bits + 7) // 8
        
        out_buf = (ctypes.c_ubyte * num_bytes)()
        out_len = ctypes.c_size_t(num_bytes)
        
        sk_buf = (ctypes.c_ubyte * len(sk_bytes)).from_buffer_copy(sk_bytes)
        ct_buf = (ctypes.c_ubyte * len(ct_bytes)).from_buffer_copy(ct_bytes)
        
        res = self.lib.abhedya_decrypt(
            sk_buf, len(sk_bytes),
            ct_buf, len(ct_bytes),
            out_buf, ctypes.byref(out_len)
        )
        
        if res != 0:
            raise AbhedyaError(f"Decryption failed with code {res}")
            
        return bytes(out_buf[:out_len.value])
