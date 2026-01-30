import os
import shutil
from omnimind import create_model
from omnimind.training.dataset import SimpleTokenizer

def verify_export():
    save_dir = "test_export_output"
    
    # Clean up previous run
    if os.path.exists(save_dir):
        shutil.rmtree(save_dir)
        
    print(f"Testing export to {save_dir}...")
    
    # 1. Create and save model
    model = create_model("nano")
    print("Saving model...")
    model.save_pretrained(save_dir)
    
    # 2. Create and save tokenizer
    tokenizer = SimpleTokenizer()
    print("Saving tokenizer...")
    tokenizer.save_pretrained(save_dir)
    
    # 3. Verify files
    expected_files = [
        "config.json",
        "model.safetensors",
        "tokenizer_config.json",
        "special_tokens_map.json",
        "vocab.json",
        "chat_template.jinja",
        "tokenizer.json",
        "merges.txt",
        "README.md"
    ]
    
    missing = []
    for f in expected_files:
        path = os.path.join(save_dir, f)
        if os.path.exists(path):
            print(f"✅ Found {f} ({os.path.getsize(path)} bytes)")
        else:
            print(f"❌ Missing {f}")
            missing.append(f)
            
    if not missing:
        print("\n🎉 All files exported successfully!")
    else:
        print(f"\n⚠️ Verification failed. Missing: {missing}")

if __name__ == "__main__":
    verify_export()
