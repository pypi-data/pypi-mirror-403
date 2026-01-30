#!/usr/bin/env python3
import sys
import readline
import os
import time

# Try to import torch with helpful error message
try:
    import torch
except ImportError:
    print("❌ ERROR: PyTorch is not installed!")
    print("Run: pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu")
    print("Then: pip install -r requirements.txt")
    sys.exit(1)

from .memory import ConversationMemory
from .utils import print_colored, print_banner, print_help, Colors, stream_response
from .config import get_config

def main():
    """Main CLI entry point for QwenVPFCode-AI"""
    
    # Print banner with identity
    print_banner()
    
    # Get configuration with device selection
    try:
        config = get_config()
    except KeyboardInterrupt:
        print_colored("\nSetup cancelled.", Colors.YELLOW)
        return
    except Exception as e:
        print_colored(f"Configuration error: {e}", Colors.RED)
        return
    
    # Initialize memory first
    try:
        memory = ConversationMemory(config)
    except Exception as e:
        print_colored(f"Memory initialization error: {e}", Colors.RED)
        return
    
    # Initialize model
    print_colored("Loading AI model...", Colors.YELLOW)
    try:
        from .model import QwenModel
        model = QwenModel(config)
    except ImportError as e:
        print_colored(f"Model import error: {e}", Colors.RED)
        print_colored("Make sure all dependencies are installed:", Colors.YELLOW)
        print_colored("pip install transformers accelerate sentencepiece tiktoken", Colors.CYAN)
        return
    except Exception as e:
        print_colored(f"Model loading error: {e}", Colors.RED)
        return
    
    # Ready message
    print_colored(f"✅ Ready! Using: {config['device'].upper()}", Colors.GREEN)
    print_colored(f"💾 Memory: {len(memory.messages)-1} previous messages loaded", Colors.YELLOW)
    print_colored(f"🎯 Max tokens per response: {config['max_new_tokens']}", Colors.CYAN)
    print_colored("-" * 60, Colors.CYAN)
    print_colored("Type /help for commands, /exit to quit", Colors.MAGENTA)
    
    # Main conversation loop
    while True:
        try:
            # Get user input with colored prompt
            user_input = input(f"{Colors.BLUE}{Colors.BOLD}You: {Colors.END}").strip()
            
            # Skip empty input
            if not user_input:
                continue
            
            # ===== COMMAND HANDLING =====
            
            # Exit command
            if user_input.lower() == "/exit" or user_input.lower() == "/quit":
                print_colored("👋 Goodbye! Your conversation has been saved.", Colors.YELLOW)
                memory._save_history()
                break
            
            # Clear memory (keeps system prompt)
            elif user_input.lower() == "/clear":
                memory.clear()
                print_colored("🧹 Conversation cleared! System identity preserved.", Colors.GREEN)
                continue
            
            # Help command
            elif user_input.lower() == "/help":
                print_help()
                continue
            
            # Save command
            elif user_input.lower() == "/save":
                memory._save_history()
                print_colored(f"💾 Saved {len(memory.messages)-1} messages to {config['history_file']}", Colors.GREEN)
                continue
            
            # Load command
            elif user_input.lower() == "/load":
                old_count = len(memory.messages)
                memory._load_history()
                new_count = len(memory.messages)
                print_colored(f"📂 Loaded {new_count-1} messages (added {new_count-old_count})", Colors.GREEN)
                continue
            
            # Identity command - shows creator info
            elif user_input.lower() == "/identity" or user_input.lower() == "/info":
                try:
                    identity_info = memory.get_identity_info()
                    print(identity_info)
                except:
                    print_colored("I am QwenVPFCode-AI, created by Adriano (litaliano00-dev) for OPFTS!", Colors.CYAN)
                continue
            
            # Status command
            elif user_input.lower() == "/status" or user_input.lower() == "/stats":
                print_colored(f"📊 Current Status:", Colors.BOLD + Colors.CYAN)
                print_colored(f"  Device: {config['device'].upper()}", Colors.CYAN)
                print_colored(f"  Memory usage: {len(memory.messages)-1}/{memory.max_messages*2} messages", Colors.CYAN)
                print_colored(f"  History file: {config['history_file']}", Colors.CYAN)
                if config['device'] == 'cuda':
                    gpu_mem = torch.cuda.memory_allocated() / 1024**3
                    print_colored(f"  GPU memory: {gpu_mem:.2f} GB used", Colors.CYAN)
                continue
            
            # Model command
            elif user_input.lower() == "/model":
                print_colored(f"🤖 Model: {config['model_name']}", Colors.CYAN)
                print_colored(f"  Max context: {config['max_length']} tokens", Colors.CYAN)
                print_colored(f"  Max response: {config['max_new_tokens']} tokens", Colors.CYAN)
                continue
            
            # ===== AI RESPONSE GENERATION =====
            
            # Add user message to memory
            memory.add("user", user_input)
            
            # Generate AI response with timing
            print_colored("AI: ", Colors.MAGENTA + Colors.BOLD, end="", flush=True)
            
            start_time = time.time()
            try:
                # Get conversation for context
                conversation = memory.get_conversation()
                
                # Generate response
                response = model.generate(conversation)
                
                # Calculate tokens per second
                end_time = time.time()
                gen_time = end_time - start_time
                
                # Simple token estimation (4 chars ~= 1 token)
                est_tokens = len(response) / 4
                if gen_time > 0:
                    tps = est_tokens / gen_time
                    speed_info = f" ({tps:.1f} tokens/sec)"
                else:
                    speed_info = ""
                
                # Print response with timing
                print_colored(response, Colors.CYAN)
                if gen_time > 1.0:  # Only show timing for longer responses
                    print_colored(f"⏱️  Generated in {gen_time:.2f}s{speed_info}", Colors.YELLOW)
                
                # Add AI response to memory
                memory.add("assistant", response)
                
            except torch.cuda.OutOfMemoryError:
                print_colored("🚫 GPU out of memory! Try using /clear or restarting.", Colors.RED)
                memory.messages.pop()  # Remove the last user message that caused OOM
                print_colored("Last message removed from memory.", Colors.YELLOW)
            except KeyboardInterrupt:
                print_colored("\n✋ Response generation interrupted.", Colors.YELLOW)
                memory.messages.pop()  # Remove the incomplete user message
                print_colored("You can continue with a new message.", Colors.GREEN)
            except Exception as e:
                print_colored(f"❌ Generation error: {e}", Colors.RED)
                memory.messages.pop()  # Remove the problematic user message
                print_colored("Last message removed due to error.", Colors.YELLOW)
            
            print()  # Blank line for readability
            
        except KeyboardInterrupt:
            print_colored("\n\n⚠️  Use /exit to quit properly and save your conversation.", Colors.YELLOW)
            print_colored("Press Enter to continue with a new message...", Colors.GREEN)
            continue
        except EOFError:
            print_colored("\n\n👋 Goodbye!", Colors.YELLOW)
            memory._save_history()
            break
        except Exception as e:
            print_colored(f"❌ Unexpected error: {e}", Colors.RED)
            print_colored("You can continue with a new message.", Colors.GREEN)

if __name__ == "__main__":
    main()
