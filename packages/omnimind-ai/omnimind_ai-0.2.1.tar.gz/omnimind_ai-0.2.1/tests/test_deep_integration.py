#!/usr/bin/env python3
"""
OMNIMIND Deep Integration Test - ตรวจสอบ runtime conflicts และ class instantiation
"""

import sys
import traceback
from typing import Dict, List, Any

# Test results storage
RESULTS: Dict[str, Dict[str, Any]] = {}
CONFLICTS: List[str] = []

def test_with_traceback(name: str, test_func, *args, **kwargs):
    """Run a test with full traceback capture"""
    try:
        result = test_func(*args, **kwargs)
        RESULTS[name] = {"success": True, "result": str(result)[:100] if result else "OK"}
        return True, result
    except Exception as e:
        tb = traceback.format_exc()
        RESULTS[name] = {
            "success": False, 
            "error": str(e)[:200],
            "type": type(e).__name__,
            "traceback": tb[-500:]  # Last 500 chars of traceback
        }
        return False, e

def run_deep_tests():
    print("=" * 70)
    print("🔬 OMNIMIND Deep Integration Tests")
    print("=" * 70)
    
    # Test 1: Config Creation
    print("\n🧪 Test 1: Config Creation & Validation")
    print("-" * 50)
    
    try:
        from omnimind import OmnimindConfig, get_config, list_available_sizes
        
        # Test all model sizes
        sizes = list_available_sizes()
        print(f"  Available sizes: {sizes}")
        
        for size in ["nano", "tiny", "small", "medium"]:
            success, result = test_with_traceback(
                f"config_{size}",
                get_config,
                size
            )
            status = "✅" if success else "❌"
            print(f"  {status} get_config('{size}'): {result if isinstance(result, Exception) else 'OK'}")
        
        # Custom config
        success, result = test_with_traceback(
            "custom_config",
            lambda: OmnimindConfig(
                d_model=256,
                n_layers=4,
                d_state=16,
                vocab_size=50257
            )
        )
        status = "✅" if success else "❌"
        print(f"  {status} Custom OmnimindConfig: {result if isinstance(result, Exception) else 'OK'}")
        
    except Exception as e:
        print(f"  ❌ Config tests failed: {e}")
    
    # Test 2: Model Creation
    print("\n🧪 Test 2: Model Creation")
    print("-" * 50)
    
    try:
        from omnimind import create_model, OmnimindModel, OmnimindConfig
        
        # Create nano model
        success, model = test_with_traceback(
            "create_nano_model",
            create_model,
            "nano"
        )
        status = "✅" if success else "❌"
        print(f"  {status} create_model('nano'): {model if isinstance(model, Exception) else 'Created'}")
        
        if success:
            # Check model properties
            print(f"    - Model type: {type(model).__name__}")
            print(f"    - Parameter count: {sum(p.numel() for p in model.parameters()):,}")
            
    except Exception as e:
        print(f"  ❌ Model creation failed: {e}")
        traceback.print_exc()
    
    # Test 3: Hybrid Model (REMOVED - Pure SSM only)
    # print("\n🧪 Test 3: Hybrid Model (SSM + Attention)")
    # print("-" * 50)
    
    # Test 4: Training Components
    print("\n🧪 Test 4: Training Components")
    print("-" * 50)
    
    try:
        from omnimind import Trainer, TrainingConfig, FineTuner, FineTuneConfig
        from omnimind import TurboFineTuner, TurboConfig
        from omnimind import Distiller, DistillationConfig
        
        # TrainingConfig
        success, config = test_with_traceback(
            "training_config",
            lambda: TrainingConfig(
                learning_rate=1e-4,
                batch_size=2,
                num_epochs=1
            )
        )
        status = "✅" if success else "❌"
        print(f"  {status} TrainingConfig: {config if isinstance(config, Exception) else 'OK'}")
        
        # FineTuneConfig
        success, config = test_with_traceback(
            "finetune_config",
            lambda: FineTuneConfig(
                learning_rate=1e-5,
                lora_r=8
            )
        )
        status = "✅" if success else "❌"
        print(f"  {status} FineTuneConfig: {config if isinstance(config, Exception) else 'OK'}")
        
        # TurboConfig
        success, config = test_with_traceback(
            "turbo_config",
            lambda: TurboConfig()
        )
        status = "✅" if success else "❌"
        print(f"  {status} TurboConfig: {config if isinstance(config, Exception) else 'OK'}")
        
        # DistillationConfig
        success, config = test_with_traceback(
            "distillation_config",
            lambda: DistillationConfig()
        )
        status = "✅" if success else "❌"
        print(f"  {status} DistillationConfig: {config if isinstance(config, Exception) else 'OK'}")
        
    except Exception as e:
        print(f"  ❌ Training components failed: {e}")
    
    # Test 5: Inference Components
    print("\n🧪 Test 5: Inference Components")
    print("-" * 50)
    
    try:
        from omnimind import MobileConfig, MobileInference
        from omnimind import GPUConfig, OptimizedInference
        
        # MobileConfig
        success, config = test_with_traceback(
            "mobile_config",
            lambda: MobileConfig()
        )
        status = "✅" if success else "❌"
        print(f"  {status} MobileConfig: {config if isinstance(config, Exception) else 'OK'}")
        
        # GPUConfig
        success, config = test_with_traceback(
            "gpu_config",
            lambda: GPUConfig()
        )
        status = "✅" if success else "❌"
        print(f"  {status} GPUConfig: {config if isinstance(config, Exception) else 'OK'}")
        
    except Exception as e:
        print(f"  ❌ Inference components failed: {e}")
    
    # Test 6: Conversion Components
    print("\n🧪 Test 6: Conversion Components")
    print("-" * 50)
    
    try:
        from omnimind import WeightTransfer, TransferConfig, AdvancedWeightTransfer
        from omnimind import export_to_gguf
        
        # TransferConfig
        success, config = test_with_traceback(
            "transfer_config",
            lambda: TransferConfig()
        )
        status = "✅" if success else "❌"
        print(f"  {status} TransferConfig: {config if isinstance(config, Exception) else 'OK'}")
        
        print(f"  ✅ export_to_gguf: Available")
        
    except Exception as e:
        print(f"  ❌ Conversion components failed: {e}")
    
    # Test 7: Storage Components
    print("\n🧪 Test 7: Storage Components")
    print("-" * 50)
    
    try:
        from omnimind import SQLiteWeightStorage, WeightStorageConfig
        from omnimind import create_weight_storage
        
        # WeightStorageConfig uses compression and cache settings, not db_path
        success, config = test_with_traceback(
            "storage_config",
            lambda: WeightStorageConfig(compression="zstd", cache_size_mb=256)
        )
        status = "✅" if success else "❌"
        print(f"  {status} WeightStorageConfig: {config if isinstance(config, Exception) else 'OK'}")
        
    except Exception as e:
        print(f"  ❌ Storage components failed: {e}")
    
    # Test 8: Cognitive Components
    print("\n🧪 Test 8: Cognitive Components")
    print("-" * 50)
    
    try:
        from omnimind import ToolAgent, ToolRegistry
        from omnimind import RealtimeAgent, RealtimeConfig
        from omnimind import get_standard_tools
        
        # ToolRegistry
        success, registry = test_with_traceback(
            "tool_registry",
            ToolRegistry
        )
        status = "✅" if success else "❌"
        print(f"  {status} ToolRegistry: {registry if isinstance(registry, Exception) else 'OK'}")
        
        # RealtimeConfig
        success, config = test_with_traceback(
            "realtime_config",
            lambda: RealtimeConfig()
        )
        status = "✅" if success else "❌"
        print(f"  {status} RealtimeConfig: {config if isinstance(config, Exception) else 'OK'}")
        
        # Standard tools
        success, tools = test_with_traceback(
            "standard_tools",
            get_standard_tools
        )
        status = "✅" if success else "❌"
        print(f"  {status} get_standard_tools(): {tools if isinstance(tools, Exception) else f'{len(tools)} tools'}")
        
    except Exception as e:
        print(f"  ❌ Cognitive components failed: {e}")
    
    # Test 9: Generation Components
    print("\n🧪 Test 9: Generation Components")
    print("-" * 50)
    
    try:
        from omnimind import DocumentGenerator, DocumentConfig
        from omnimind import OmnimindCreativeLab, get_creative_tools
        
        # DocumentConfig
        success, config = test_with_traceback(
            "document_config",
            lambda: DocumentConfig()
        )
        status = "✅" if success else "❌"
        print(f"  {status} DocumentConfig: {config if isinstance(config, Exception) else 'OK'}")
        
    except Exception as e:
        print(f"  ❌ Generation components failed: {e}")
    
    # Test 10: Workflow Components
    print("\n🧪 Test 10: Workflow Components")
    print("-" * 50)
    
    try:
        from omnimind import OmnimindWorkflow, WorkflowConfig
        
        # WorkflowConfig
        success, config = test_with_traceback(
            "workflow_config",
            lambda: WorkflowConfig()
        )
        status = "✅" if success else "❌"
        print(f"  {status} WorkflowConfig: {config if isinstance(config, Exception) else 'OK'}")
        
    except Exception as e:
        print(f"  ❌ Workflow components failed: {e}")
    
    # Test 11: Unified Model
    print("\n🧪 Test 11: Unified Model")
    print("-" * 50)
    
    try:
        from omnimind import Omnimind, OmnimindLite, load_omnimind
        
        print(f"  ✅ Omnimind class: Available")
        print(f"  ✅ OmnimindLite class: Available")
        print(f"  ✅ load_omnimind function: Available")
        RESULTS["unified_imports"] = {"success": True}
        
    except Exception as e:
        print(f"  ❌ Unified model failed: {e}")
        RESULTS["unified_imports"] = {"success": False, "error": str(e)}
    
    # Test 12: Cross-component Conflict Check
    print("\n🧪 Test 12: Cross-Component Conflict Detection")
    print("-" * 50)
    
    conflict_tests = [
        (
            "Config+Model",
            """
from omnimind import OmnimindConfig, OmnimindModel
config = OmnimindConfig(d_model=128, n_layers=2, d_state=8, vocab_size=1000)
model = OmnimindModel(config)
            """
        ),
        (
            "Model+Training",
            """
from omnimind import create_model, TrainingConfig
model = create_model("nano")
config = TrainingConfig()
            """
        ),
        # (
        #     "Hybrid+SSM",
        #     """
        # from omnimind import HybridOmnimind, SelectiveSSM, OmnimindConfig
        # config = OmnimindConfig(d_model=128, n_layers=2, d_state=8, vocab_size=1000)
        # ssm = SelectiveSSM(config)
        #     """
        # ),
        (
            "Conversion+Storage",
            """
from omnimind import WeightStorageConfig, TransferConfig, AdvancedWeightTransfer
            """
        ),
        (
            "Multimodal+Base",
            """
from omnimind import OmnimindMultimodal, MultimodalConfig, OmnimindModel
            """
        ),
        (
            "Music+Base",
            """
from omnimind import OmnimindMusic, MusicConfig, OmnimindModel
            """
        ),
    ]
    
    for name, code in conflict_tests:
        try:
            exec(code, {})
            print(f"  ✅ {name}: No conflict")
            RESULTS[f"conflict_{name}"] = {"success": True}
        except Exception as e:
            print(f"  ❌ {name}: CONFLICT! {type(e).__name__}: {str(e)[:100]}")
            RESULTS[f"conflict_{name}"] = {"success": False, "error": str(e)}
            CONFLICTS.append(f"{name}: {e}")
    
    # Test 13: Utils Consistency
    print("\n🧪 Test 13: Utils Consistency")
    print("-" * 50)
    
    try:
        from omnimind import (
            get_device_type, get_optimal_device, get_optimal_dtype,
            DEVICE_TYPE, HAS_CUDA, HAS_MPS, HAS_TRITON,
            check_dependencies, print_system_info
        )
        
        device_type = get_device_type()
        optimal_device = get_optimal_device()
        optimal_dtype = get_optimal_dtype()
        
        print(f"  ✅ Device Type: {device_type}")
        print(f"  ✅ Optimal Device: {optimal_device}")
        print(f"  ✅ Optimal Dtype: {optimal_dtype}")
        print(f"  ✅ HAS_CUDA: {HAS_CUDA}, HAS_MPS: {HAS_MPS}, HAS_TRITON: {HAS_TRITON}")
        
        RESULTS["utils_consistency"] = {"success": True}
        
    except Exception as e:
        print(f"  ❌ Utils consistency failed: {e}")
        RESULTS["utils_consistency"] = {"success": False, "error": str(e)}
    
    # Test 14: Quantization Components
    print("\n🧪 Test 14: Quantization Components")
    print("-" * 50)
    
    try:
        from omnimind.quantization.advanced_quantization import (
            QuantType, QuantConfig, ModelQuantizer
        )
        
        success, config = test_with_traceback(
            "quant_config",
            lambda: QuantConfig(quant_type=QuantType.INT8)
        )
        status = "✅" if success else "❌"
        print(f"  {status} QuantConfig: {config if isinstance(config, Exception) else 'OK'}")
        
    except ImportError as e:
        print(f"  ⚠️ Quantization (optional): {e}")
    except Exception as e:
        print(f"  ❌ Quantization failed: {e}")
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 DEEP TEST SUMMARY")
    print("=" * 70)
    
    total = len(RESULTS)
    passed = sum(1 for r in RESULTS.values() if r.get("success", False))
    failed = total - passed
    
    print(f"\nTotal tests:  {total}")
    print(f"Passed:       {passed} ✅")
    print(f"Failed:       {failed} ❌")
    
    if CONFLICTS:
        print(f"\n⚠️ CONFLICTS DETECTED ({len(CONFLICTS)}):")
        for conflict in CONFLICTS:
            print(f"   - {conflict}")
    
    if failed > 0:
        print("\n❌ FAILED TESTS:")
        for key, result in RESULTS.items():
            if not result.get("success", False):
                print(f"   - {key}: {result.get('type', 'Error')}: {result.get('error', 'Unknown')}")
    
    print("\n" + "=" * 70)
    
    return failed == 0 and len(CONFLICTS) == 0

if __name__ == "__main__":
    success = run_deep_tests()
    sys.exit(0 if success else 1)
