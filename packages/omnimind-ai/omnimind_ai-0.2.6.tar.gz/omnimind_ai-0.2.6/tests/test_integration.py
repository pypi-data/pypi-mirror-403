#!/usr/bin/env python3
"""
OMNIMIND Integration Test - ตรวจสอบว่าทุกส่วนทำงานประสานกัน
"""

import sys
import traceback
from typing import Dict, List, Tuple, Any
import importlib
import inspect

# Test results storage
RESULTS: Dict[str, Dict[str, Any]] = {}

def test_import(module_path: str, items: List[str] = None) -> Tuple[bool, str]:
    """Test importing a module and optionally specific items"""
    try:
        if items:
            module = importlib.import_module(module_path)
            missing = []
            for item in items:
                if not hasattr(module, item):
                    missing.append(item)
            if missing:
                return False, f"Missing items: {missing}"
        else:
            importlib.import_module(module_path)
        return True, "OK"
    except Exception as e:
        return False, f"{type(e).__name__}: {str(e)[:200]}"

def check_callable(obj, name: str) -> Tuple[bool, str]:
    """Check if an object is callable or a valid class"""
    if obj is None:
        return False, "None (optional import failed)"
    if callable(obj) or isinstance(obj, type):
        return True, "OK"
    return True, f"Not callable (type: {type(obj).__name__})"

def run_integration_tests():
    """Run comprehensive integration tests"""
    print("=" * 70)
    print("🔍 OMNIMIND Integration Test Suite")
    print("=" * 70)
    
    # Test 1: Core imports from main package
    print("\n📦 Test 1: Main Package Imports")
    print("-" * 50)
    
    core_imports = [
        ("omnimind", [
            "__version__", "OmnimindConfig", "get_config", "ModelSize",
            "OmnimindModel", "OmnimindForCausalLM", "create_model",
            "SelectiveSSM", "OmnimindBlock"
        ]),
    ]
    
    for module_path, items in core_imports:
        success, msg = test_import(module_path, items)
        status = "✅" if success else "❌"
        print(f"  {status} {module_path}: {msg}")
        RESULTS[f"import_{module_path}"] = {"success": success, "message": msg}
    
    # Test 2: Submodule imports
    print("\n📁 Test 2: Submodule Imports")
    print("-" * 50)
    
    submodules = [
        "omnimind.model.config",
        "omnimind.model.omnimind_model",
        "omnimind.model.ssm_layer",
        # "omnimind.model.hybrid",  # Removed: Pure SSM only
        "omnimind.model.fast_base",
        "omnimind.model.multimodal",
        "omnimind.model.music",
        "omnimind.model.lite",
        "omnimind.training.trainer",
        "omnimind.training.finetune",
        "omnimind.training.turbo",
        "omnimind.training.distillation",
        "omnimind.training.dpo",
        "omnimind.training.evaluator",
        "omnimind.training.dataset",
        "omnimind.training.multilingual_tokenizer",
        "omnimind.inference.mobile",
        "omnimind.inference.gpu_optimization",
        "omnimind.conversion.gguf_export",
        "omnimind.conversion.weight_transfer",
        "omnimind.conversion.advanced_conversion",
        "omnimind.conversion.low_memory",
        "omnimind.storage",
        "omnimind.cognitive.realtime",
        "omnimind.cognitive.tool_use",
        "omnimind.cognitive.standard_tools",
        "omnimind.generation.document_generator",
        "omnimind.generation.media_generator",
        "omnimind.utils",
        "omnimind.utils.loader",
        "omnimind.utils.chat_template",
        "omnimind.workflow",
        "omnimind.unified",
    ]
    
    failures = []
    for submod in submodules:
        success, msg = test_import(submod)
        status = "✅" if success else "❌"
        print(f"  {status} {submod}: {msg}")
        RESULTS[f"submodule_{submod}"] = {"success": success, "message": msg}
        if not success:
            failures.append((submod, msg))
    
    # Test 3: Optional submodules (should not crash)
    print("\n🔧 Test 3: Optional Submodules")
    print("-" * 50)
    
    optional_submodules = [
        "omnimind.quantization.advanced_quantization",
        "omnimind.inference.disk_streaming",
        "omnimind.inference.ultra_fast",
        "omnimind.model.turbo_streaming",
        "omnimind.model.sparse_experts",
        "omnimind.memory.memory_manager",
        "omnimind.memory.working_memory",
        "omnimind.cognitive.thinking_engine",
        "omnimind.cognitive.uncertainty_detector",
        "omnimind.server",
        "omnimind.cli",
    ]
    
    for submod in optional_submodules:
        success, msg = test_import(submod)
        status = "✅" if success else "⚠️"
        print(f"  {status} {submod}: {msg}")
        RESULTS[f"optional_{submod}"] = {"success": success, "message": msg, "optional": True}
    
    # Test 4: Class Instantiation Tests (without actual computation)
    print("\n🏗️ Test 4: Class Signature Checks")
    print("-" * 50)
    
    try:
        import omnimind
        
        classes_to_check = [
            ("OmnimindConfig", omnimind.OmnimindConfig),
            ("OmnimindModel", omnimind.OmnimindModel),
            ("SelectiveSSM", omnimind.SelectiveSSM),
            # ("HybridOmnimind", omnimind.HybridOmnimind),  # Removed
            ("Trainer", omnimind.Trainer),
            ("FineTuner", omnimind.FineTuner),
            ("Distiller", omnimind.Distiller),
            ("MobileInference", omnimind.MobileInference),
            ("ToolAgent", omnimind.ToolAgent),
            ("RealtimeAgent", omnimind.RealtimeAgent),
            ("DocumentGenerator", omnimind.DocumentGenerator),
        ]
        
        for name, cls in classes_to_check:
            try:
                sig = inspect.signature(cls)
                params = list(sig.parameters.keys())
                print(f"  ✅ {name}: params={params[:5]}{'...' if len(params) > 5 else ''}")
                RESULTS[f"class_{name}"] = {"success": True, "params": params}
            except Exception as e:
                print(f"  ❌ {name}: {type(e).__name__}: {str(e)[:100]}")
                RESULTS[f"class_{name}"] = {"success": False, "error": str(e)}
    except Exception as e:
        print(f"  ❌ Failed to import omnimind for class checks: {e}")
    
    # Test 5: Function Availability
    print("\n📋 Test 5: Function Availability")
    print("-" * 50)
    
    try:
        import omnimind
        
        functions_to_check = [
            "create_model",
            "get_config",
            # "create_hybrid_model",  # Removed
            "export_to_gguf",
            "transfer_to_omnimind",
            "from_qwen",
            "from_llama",
            "from_gemma",
            "convert_model",
            "stream_convert_to_gguf",
            "quick_optimize",
            "turbo_finetune",
            "distill_model",
            "quantize_model",
            "load_omnimind",
            "save_lite",
            "load_lite",
        ]
        
        for func_name in functions_to_check:
            if hasattr(omnimind, func_name):
                func = getattr(omnimind, func_name)
                success, msg = check_callable(func, func_name)
                status = "✅" if success else "❌"
                print(f"  {status} {func_name}: {msg}")
                RESULTS[f"function_{func_name}"] = {"success": success, "message": msg}
            else:
                print(f"  ❌ {func_name}: Not found in omnimind module")
                RESULTS[f"function_{func_name}"] = {"success": False, "message": "Not found"}
    except Exception as e:
        print(f"  ❌ Failed to check functions: {e}")
    
    # Test 6: Cross-module dependencies
    print("\n🔗 Test 6: Cross-Module Dependencies")
    print("-" * 50)
    
    dependency_tests = [
        # (description, test_code)
        ("Config → Model", "from omnimind import OmnimindConfig, OmnimindModel; c = OmnimindConfig(); print(type(c))"),
        ("Model → Training", "from omnimind import OmnimindModel, Trainer"),
        ("Model → Inference", "from omnimind import OmnimindModel, MobileInference"),
        ("Conversion → Storage", "from omnimind import convert_model, SQLiteWeightStorage"),
        # ("Hybrid → SSM", "from omnimind import HybridOmnimind, SelectiveSSM"),  # Removed
        ("Utils → All", "from omnimind import get_device_type, get_optimal_device, HAS_CUDA"),
    ]
    
    for desc, code in dependency_tests:
        try:
            exec(code)
            print(f"  ✅ {desc}: OK")
            RESULTS[f"dep_{desc}"] = {"success": True}
        except Exception as e:
            print(f"  ❌ {desc}: {type(e).__name__}: {str(e)[:100]}")
            RESULTS[f"dep_{desc}"] = {"success": False, "error": str(e)}
    
    # Test 7: __all__ consistency
    print("\n📝 Test 7: __all__ Consistency")
    print("-" * 50)
    
    try:
        import omnimind
        missing_in_module = []
        for item in omnimind.__all__:
            if not hasattr(omnimind, item):
                missing_in_module.append(item)
        
        if missing_in_module:
            print(f"  ❌ Items in __all__ but not importable: {missing_in_module}")
            RESULTS["all_consistency"] = {"success": False, "missing": missing_in_module}
        else:
            print(f"  ✅ All {len(omnimind.__all__)} items in __all__ are importable")
            RESULTS["all_consistency"] = {"success": True, "count": len(omnimind.__all__)}
    except Exception as e:
        print(f"  ❌ Failed to check __all__: {e}")
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 SUMMARY")
    print("=" * 70)
    
    total = len(RESULTS)
    passed = sum(1 for r in RESULTS.values() if r.get("success", False))
    failed = total - passed
    
    # Count optional failures separately
    optional_failed = sum(1 for k, r in RESULTS.items() 
                         if k.startswith("optional_") and not r.get("success", False))
    
    required_failed = failed - optional_failed
    
    print(f"\nTotal tests:     {total}")
    print(f"Passed:          {passed} ✅")
    print(f"Required failed: {required_failed} ❌")
    print(f"Optional failed: {optional_failed} ⚠️")
    
    if required_failed > 0:
        print("\n❌ CRITICAL FAILURES:")
        for key, result in RESULTS.items():
            if not key.startswith("optional_") and not result.get("success", False):
                print(f"   - {key}: {result.get('message', result.get('error', 'Unknown'))}")
    
    print("\n" + "=" * 70)
    
    return required_failed == 0

if __name__ == "__main__":
    success = run_integration_tests()
    sys.exit(0 if success else 1)
