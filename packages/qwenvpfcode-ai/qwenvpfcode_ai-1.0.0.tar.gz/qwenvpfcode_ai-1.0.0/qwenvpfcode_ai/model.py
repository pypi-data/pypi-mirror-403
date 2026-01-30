import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from typing import List, Dict
import warnings
warnings.filterwarnings("ignore")

class QwenModel:
    def __init__(self, config):
        self.config = config
        
        print(f"Loading model to {self.config['device']}...")
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.config["model_name"],
            cache_dir=self.config["cache_dir"],
            trust_remote_code=True
        )
        
        # Proper model loading with bfloat16 support for compatible GPUs[citation:8]
        if self.config["device"] == "cuda" and torch.cuda.is_bf16_supported():
            torch_dtype = torch.bfloat16
        else:
            torch_dtype = self.config["dtype"]
        
        self.model = AutoModelForCausalLM.from_pretrained(
            self.config["model_name"],
            torch_dtype=torch_dtype,
            device_map="auto" if self.config["device"] == "cuda" else None,
            cache_dir=self.config["cache_dir"],
            trust_remote_code=True
        )
        
        # CRITICAL: Enable KV cache for performance[citation:8]
        self.model.config.use_cache = self.config["use_cache"]
        
        if self.config["device"] == "cpu":
            self.model = self.model.to(self.config["device"])
        
        print("Model loaded successfully!")
    
    def generate(self, messages: List[Dict]) -> str:
        text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        
        inputs = self.tokenizer.encode(text, return_tensors="pt").to(self.config["device"])
        
        # Create attention mask to fix the warning you saw
        attention_mask = torch.ones_like(inputs)
        
        with torch.no_grad():
            outputs = self.model.generate(
                inputs,
                attention_mask=attention_mask,
                max_new_tokens=self.config["max_new_tokens"],
                temperature=0.7,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id,
                repetition_penalty=1.1,  # Reduces repetitive text
            )
        
        response = self.tokenizer.decode(outputs[0][inputs.shape[1]:], skip_special_tokens=True)
        return response
