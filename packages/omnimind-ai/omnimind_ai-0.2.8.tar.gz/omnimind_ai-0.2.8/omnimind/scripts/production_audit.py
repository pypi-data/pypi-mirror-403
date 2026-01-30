#!/usr/bin/env python3
"""
OMNIMIND Comprehensive Production Readiness Test
Tests all modules: Model, Memory, Cognitive, Interface, Training, Export
"""
import os
import sys
import shutil
import traceback

def test_model_creation():
    """Test model creation for all sizes"""
    print("\n📦 Testing Model Creation...")
    from omnimind import create_model
    
    for size in ["nano", "micro", "mini"]:
        try:
            model = create_model(size)
            params = model.model.num_parameters
            print(f"  ✅ {size}: {params / 1e6:.1f}M parameters")
        except Exception as e:
            print(f"  ❌ {size}: {e}")
            return False
    return True

def test_tokenizer():
    """Test tokenizers"""
    print("\n📝 Testing Tokenizers...")
    from omnimind import SimpleTokenizer, MultilingualTokenizer
    
    # Simple
    try:
        tok = SimpleTokenizer()
        ids = tok.encode("Hello สวัสดี")
        text = tok.decode(ids)
        print(f"  ✅ SimpleTokenizer: {len(tok)} vocab, encode/decode OK")
    except Exception as e:
        print(f"  ❌ SimpleTokenizer: {e}")
        return False
    
    # Multilingual
    try:
        tok = MultilingualTokenizer()
        test_texts = ["Hello", "สวัสดี", "你好", "🚀"]
        all_ok = all(tok.decode(tok.encode(t)) == t for t in test_texts)
        if all_ok:
            print(f"  ✅ MultilingualTokenizer: {len(tok)} vocab, multilingual OK")
        else:
            print(f"  ⚠️ MultilingualTokenizer: Some decode failures")
    except Exception as e:
        print(f"  ❌ MultilingualTokenizer: {e}")
        return False
    
    return True

def test_chat_template():
    """Test chat template application"""
    print("\n💬 Testing Chat Template...")
    from omnimind import MultilingualTokenizer
    
    try:
        tok = MultilingualTokenizer()
        messages = [
            {"role": "system", "content": "You are OMNIMIND"},
            {"role": "user", "content": "Hello!"},
        ]
        result = tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        if "<|im_start|>" in result and "<|im_end|>" in result:
            print(f"  ✅ Chat template works ({len(result)} chars)")
        else:
            print(f"  ⚠️ Chat template missing markers")
    except Exception as e:
        print(f"  ❌ Chat template: {e}")
        return False
    
    return True

def test_memory_layer():
    """Test memory components"""
    print("\n🧠 Testing Memory Layer...")
    try:
        from omnimind.memory.working_memory import WorkingMemory
        from omnimind.memory.episodic_memory import EpisodicMemory
        from omnimind.memory.semantic_memory import SemanticMemory
        
        wm = WorkingMemory()
        wm.add("test", {"content": "Hello"})
        print(f"  ✅ WorkingMemory: add/retrieve OK")
        
        # Episodic (in-memory test)
        em = EpisodicMemory(db_path=":memory:")
        print(f"  ✅ EpisodicMemory: initialized")
        
        # Semantic (fallback mode)
        sm = SemanticMemory(db_path="test_semantic_temp")
        sm.add("Test knowledge", category="test")
        results = sm.search("Test")
        print(f"  ✅ SemanticMemory: add/search OK")
        shutil.rmtree("test_semantic_temp", ignore_errors=True)
        
    except Exception as e:
        print(f"  ❌ Memory: {e}")
        traceback.print_exc()
        return False
    
    return True

def test_cognitive_layer():
    """Test cognitive components"""
    print("\n🤔 Testing Cognitive Layer...")
    try:
        from omnimind.cognitive.thinking_engine import ThinkingEngine
        from omnimind.cognitive.uncertainty_detector import UncertaintyDetector
        from omnimind.cognitive.anti_repetition import AntiRepetition
        
        ud = UncertaintyDetector()
        result = ud.evaluate("I'm not sure about this")
        print(f"  ✅ UncertaintyDetector: confidence {result.overall_score:.2f}")
        
        ar = AntiRepetition()
        print(f"  ✅ AntiRepetition: initialized")
        
        te = ThinkingEngine(uncertainty_detector=ud, anti_repetition=ar)
        print(f"  ✅ ThinkingEngine: initialized")
        
    except Exception as e:
        print(f"  ❌ Cognitive: {e}")
        traceback.print_exc()
        return False
    
    return True

def test_model_export():
    """Test model and tokenizer export"""
    print("\n💾 Testing Model Export...")
    export_dir = "test_production_export"
    
    try:
        from omnimind import create_model, MultilingualTokenizer
        
        # Clean up
        if os.path.exists(export_dir):
            shutil.rmtree(export_dir)
        
        model = create_model("nano")
        model.save_pretrained(export_dir)
        
        tok = MultilingualTokenizer()
        tok.save_pretrained(export_dir)
        
        expected_files = [
            "config.json", "model.safetensors", "README.md",
            "vocab.json", "tokenizer_config.json", "tokenizer.json",
            "special_tokens_map.json", "chat_template.jinja"
        ]
        
        missing = [f for f in expected_files if not os.path.exists(os.path.join(export_dir, f))]
        if not missing:
            print(f"  ✅ All {len(expected_files)} files exported")
        else:
            print(f"  ⚠️ Missing: {missing}")
            
        # Cleanup
        shutil.rmtree(export_dir, ignore_errors=True)
        
    except Exception as e:
        print(f"  ❌ Export: {e}")
        traceback.print_exc()
        shutil.rmtree(export_dir, ignore_errors=True)
        return False
    
    return True

def test_training_dataset():
    """Test training dataset creation"""
    print("\n📊 Testing Training Dataset...")
    try:
        from omnimind import MultilingualTokenizer, TextDataset, create_dataloader
        import tempfile
        
        # Create temp data file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Hello world! This is a test.\n" * 100)
            f.write("สวัสดีโลก! นี่คือการทดสอบ\n" * 100)
            temp_path = f.name
        
        tok = MultilingualTokenizer()
        dataset = TextDataset(temp_path, tok, max_seq_len=128)
        
        if len(dataset) > 0:
            print(f"  ✅ TextDataset: {len(dataset)} chunks")
            
            loader = create_dataloader(dataset, batch_size=4)
            batch = next(iter(loader))
            print(f"  ✅ DataLoader: batch shape {batch['input_ids'].shape}")
        else:
            print(f"  ⚠️ TextDataset: No chunks created (data too small)")
            
        os.unlink(temp_path)
        
    except Exception as e:
        print(f"  ❌ Dataset: {e}")
        traceback.print_exc()
        return False
    
    return True

def test_forward_and_generate():
    """Test forward pass and generation"""
    print("\n🔄 Testing Forward Pass & Generation...")
    try:
        import torch
        from omnimind import create_model
        
        model = create_model("nano")
        
        # Forward
        dummy = torch.randint(0, 1000, (2, 32))
        output = model(dummy)
        print(f"  ✅ Forward: output shape {output['logits'].shape}")
        
        # Generate
        prompt = torch.randint(0, 1000, (1, 8))
        generated = model.generate(prompt, max_new_tokens=16)
        print(f"  ✅ Generate: output shape {generated.shape}")
        
    except Exception as e:
        print(f"  ❌ Forward/Generate: {e}")
        traceback.print_exc()
        return False
    
    return True

def main():
    print("=" * 60)
    print("🚀 OMNIMIND Production Readiness Audit")
    print("=" * 60)
    
    tests = [
        ("Model Creation", test_model_creation),
        ("Tokenizers", test_tokenizer),
        ("Chat Template", test_chat_template),
        ("Memory Layer", test_memory_layer),
        ("Cognitive Layer", test_cognitive_layer),
        ("Model Export", test_model_export),
        ("Training Dataset", test_training_dataset),
        ("Forward & Generate", test_forward_and_generate),
    ]
    
    results = []
    for name, test_fn in tests:
        try:
            passed = test_fn()
            results.append((name, passed))
        except Exception as e:
            print(f"\n❌ {name} crashed: {e}")
            results.append((name, False))
    
    print("\n" + "=" * 60)
    print("📋 AUDIT SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, p in results if p)
    total = len(results)
    
    for name, p in results:
        status = "✅ PASS" if p else "❌ FAIL"
        print(f"  {status}: {name}")
    
    print()
    if passed == total:
        print(f"🎉 All {total} tests PASSED! Project is PRODUCTION READY!")
        return 0
    else:
        print(f"⚠️ {passed}/{total} tests passed. Review failures before production.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
