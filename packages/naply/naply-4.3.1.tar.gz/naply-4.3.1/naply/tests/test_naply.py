"""
NAPLY Test Suite
================

Tests for the NAPLY library.
Run with: python -m pytest tests/ -v
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np


def test_tensor_creation():
    """Test tensor creation and basic operations."""
    from naply import Tensor
    
    # Create tensor
    t = Tensor([1, 2, 3])
    assert t.shape == (3,)
    
    # Create 2D tensor
    t2 = Tensor([[1, 2], [3, 4]])
    assert t2.shape == (2, 2)
    
    # Test requires_grad
    t3 = Tensor([1, 2, 3], requires_grad=True)
    assert t3.requires_grad == True
    
    print("✅ Tensor creation tests passed!")


def test_tensor_math():
    """Test tensor arithmetic."""
    from naply import Tensor
    
    a = Tensor([1, 2, 3], requires_grad=True)
    b = Tensor([4, 5, 6], requires_grad=True)
    
    # Addition
    c = a + b
    assert np.allclose(c.data, [5, 7, 9])
    
    # Multiplication
    d = a * b
    assert np.allclose(d.data, [4, 10, 18])
    
    # Subtraction
    e = b - a
    assert np.allclose(e.data, [3, 3, 3])
    
    print("✅ Tensor math tests passed!")


def test_tensor_backprop():
    """Test automatic differentiation."""
    from naply import Tensor
    
    x = Tensor([2.0], requires_grad=True)
    y = x * x * 3  # y = 3x^2
    y.backward()
    
    # dy/dx = 6x = 12
    assert np.allclose(x.grad, [12.0])
    
    print("✅ Backprop tests passed!")


def test_linear_layer():
    """Test linear layer."""
    from naply import Linear, Tensor
    
    layer = Linear(10, 5)
    x = Tensor(np.random.randn(2, 10).astype(np.float32))
    y = layer(x)
    
    assert y.shape == (2, 5)
    
    print("✅ Linear layer tests passed!")


def test_embedding():
    """Test embedding layer."""
    from naply import Embedding, Tensor
    
    embed = Embedding(100, 32)
    idx = Tensor(np.array([[1, 2, 3], [4, 5, 6]]))
    out = embed(idx)
    
    assert out.shape == (2, 3, 32)
    
    print("✅ Embedding tests passed!")


def test_layernorm():
    """Test layer normalization."""
    from naply import LayerNorm, Tensor
    
    norm = LayerNorm(64)
    x = Tensor(np.random.randn(2, 10, 64).astype(np.float32))
    y = norm(x)
    
    assert y.shape == (2, 10, 64)
    
    print("✅ LayerNorm tests passed!")


def test_attention():
    """Test multi-head attention."""
    from naply import MultiHeadAttention, Tensor
    
    attn = MultiHeadAttention(n_embd=64, n_head=4)
    x = Tensor(np.random.randn(2, 10, 64).astype(np.float32))
    y, _ = attn(x)
    
    assert y.shape == (2, 10, 64)
    
    print("✅ Attention tests passed!")


def test_transformer_block():
    """Test transformer block."""
    from naply import TransformerBlock, Tensor
    
    block = TransformerBlock(n_embd=64, n_head=4)
    x = Tensor(np.random.randn(2, 10, 64).astype(np.float32))
    y, _ = block(x)
    
    assert y.shape == (2, 10, 64)
    
    print("✅ Transformer block tests passed!")


def test_gpt():
    """Test GPT model."""
    from naply.transformer import GPT
    from naply import Tensor
    
    model = GPT(
        vocab_size=100,
        n_layer=2,
        n_head=2,
        n_embd=32,
        block_size=64
    )
    
    x = Tensor(np.array([[1, 2, 3, 4, 5]]))
    logits, _ = model(x)
    
    assert logits.shape == (1, 5, 100)
    
    print("✅ GPT tests passed!")


def test_tokenizer():
    """Test tokenizer."""
    from naply import CharTokenizer
    
    tok = CharTokenizer()
    tok.train(["hello world", "test data"])
    
    ids = tok.encode("hello")
    text = tok.decode(ids)
    
    assert "hello" in text.lower()
    
    print("✅ Tokenizer tests passed!")


def test_data_loader():
    """Test universal data loader."""
    from naply.data import UniversalLoader
    import tempfile
    import os
    
    # Create temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("Hello world!\nThis is a test.\n")
        temp_path = f.name
    
    try:
        loader = UniversalLoader(temp_path)
        texts = loader.load()
        assert len(texts) > 0
    finally:
        os.unlink(temp_path)
    
    print("✅ Data loader tests passed!")


def test_optimizer():
    """Test AdamW optimizer."""
    from naply import AdamW, Linear, Tensor
    
    layer = Linear(10, 5)
    optimizer = AdamW(layer.parameters(), lr=0.01)
    
    x = Tensor(np.random.randn(2, 10).astype(np.float32), requires_grad=True)
    y = layer(x)
    loss = y.sum()
    
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()
    
    # Check that weights were updated
    assert optimizer.t == 1
    
    print("✅ Optimizer tests passed!")


def test_model_class():
    """Test main Model class."""
    from naply import Model
    
    model = Model("tiny")
    
    assert model.count_params() > 0
    print(f"   Tiny model params: {model.count_params():,}")
    
    print("✅ Model class tests passed!")


def test_config():
    """Test configuration."""
    from naply import ModelConfig, PRESETS
    
    config = ModelConfig(n_layer=6, n_head=6, n_embd=384)
    assert config.n_layer == 6
    
    assert "tiny" in PRESETS
    assert "medium" in PRESETS
    assert "large" in PRESETS
    
    print("✅ Config tests passed!")


def test_methods():
    """Test training methods exist."""
    from naply import (
        CRCTrainer, DCLTrainer, ILCTrainer, MCUTrainer,
        P3Engine, PPLTrainer, RDLTrainer, S3LTrainer, SGLTrainer
    )
    
    print("✅ Training methods import tests passed!")


def run_all_tests():
    """Run all tests."""
    print("\n" + "=" * 50)
    print("NAPLY Library Test Suite")
    print("=" * 50 + "\n")
    
    tests = [
        test_tensor_creation,
        test_tensor_math,
        test_tensor_backprop,
        test_linear_layer,
        test_embedding,
        test_layernorm,
        test_attention,
        test_transformer_block,
        test_gpt,
        test_tokenizer,
        test_data_loader,
        test_optimizer,
        test_model_class,
        test_config,
        test_methods,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ {test.__name__} FAILED: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 50)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
