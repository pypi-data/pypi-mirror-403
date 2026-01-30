import torch
import os

def get_config():
    print("Select device for inference:")
    print("1) GPU (CUDA) - Fast, requires NVIDIA GPU")
    print("2) CPU - Slower, no GPU required")
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "1" and torch.cuda.is_available():
        device = "cuda"
        dtype = torch.float16  # Faster, uses less memory
        print(f"GPU selected: {torch.cuda.get_device_name(0)}")
    else:
        device = "cpu"
        dtype = torch.float32  # More stable on CPU
        if choice == "1":
            print("CUDA not available. Falling back to CPU.")
        print("CPU selected.")
    
    return {
        "model_name": "Qwen/Qwen2.5-Coder-1.5B-Instruct",
        "max_length": 2048,  # Reduced for faster processing
        "max_new_tokens": 512,  # Limits response length for speed
        "memory_size": 20,  # Remembers last 10 exchanges
        "device": device,
        "dtype": dtype,
        "cache_dir": os.path.expanduser("~/.cache/qwenvpfcode"),
        "history_file": os.path.expanduser("~/.cache/qwenvpfcode/history.json"),
        "use_cache": True,  # Critical for performance[citation:8]
    }
