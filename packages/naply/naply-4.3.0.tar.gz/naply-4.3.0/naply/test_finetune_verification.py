
import os
import shutil
import sys
import numpy as np

# Ensure we can import naply (assuming it's in the parent directory or installed)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import naply
    from naply import finetune, load_for_finetune, add_lora, train_lora, NaplyModel, LoRAConfig
    print("[SUCCESS] Naply fine-tuning modules imported successfully.")
except ImportError as e:
    print(f"[ERROR] Failed to import naply fine-tuning modules: {e}")
    sys.exit(1)

def test_lora_layer():
    print("\nTesting LoRA Layer...")
    from naply.finetune import LoRALayer
    from naply.tensor import Tensor
    
    in_dim, out_dim = 64, 64
    lora = LoRALayer(in_dim, out_dim, rank=4, alpha=8)
    
    x = Tensor(np.random.randn(2, 10, in_dim).astype(np.float32))
    out = lora(x)
    
    print(f"   Input shape: {x.data.shape}")
    print(f"   Output shape: {out.data.shape}")
    
    assert out.data.shape == (2, 10, out_dim)
    print("   [PASS] LoRA forward pass works.")

def test_finetune_flow():
    print("\nTesting Fine-tuning Flow...")
    
    # 1. Mock Data
    data_file = "test_data.jsonl"
    with open(data_file, "w") as f:
        f.write('{"instruction": "Hi", "output": "Hello!"}\n')
        f.write('{"instruction": "Bye", "output": "Goodbye!"}\n')
    
    # 2. Mock Model (Tiny)
    print("   Creating tiny model...")
    config = naply.base_model_loader.MODEL_CONFIGS["tiny"]
    config.num_hidden_layers = 1 # Very small for speed
    config.hidden_size = 32
    config.num_attention_heads = 4
    model = NaplyModel(config)
    
    # 3. Add LoRA
    print("   Adding LoRA...")
    model = add_lora(model, rank=4)
    
    # 4. Train
    print("   Training...")
    output_dir = "test_finetune_output"
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
        
    try:
        train_lora(model, data_file, epochs=1, batch_size=2, output_dir=output_dir)
        print("   [PASS] Training completed.")
    except Exception as e:
        print(f"   [FAIL] Training failed: {e}")
        import traceback
        traceback.print_exc()
        raise
    
    # 5. Check Output
    if os.path.exists(os.path.join(output_dir, "lora_weights.pkl")):
        print("   [PASS] LoRA weights saved.")
    else:
        print("   [FAIL] LoRA weights not found.")
        
    # Cleanup
    if os.path.exists(data_file):
        os.remove(data_file)
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)

if __name__ == "__main__":
    test_lora_layer()
    test_finetune_flow()
    print("\n[SUCCESS] All verification tests passed.")
