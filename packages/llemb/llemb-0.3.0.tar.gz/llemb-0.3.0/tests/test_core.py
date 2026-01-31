import pytest

from llemb.backends.transformers_backend import TransformersBackend
from llemb.core import Encoder

try:
    from llemb.backends.vllm_backend import VLLMBackend
except ImportError:
    VLLMBackend = None


def test_encoder_init_transformers():
    enc = Encoder(model_name="sshleifer/tiny-gpt2", backend="transformers")
    assert isinstance(enc.backend_instance, TransformersBackend)

def test_encoder_init_vllm():
    try:
        enc = Encoder(model_name="sshleifer/tiny-gpt2", backend="vllm")
        if VLLMBackend:
            assert isinstance(enc.backend_instance, VLLMBackend)
    except (ImportError, ValueError, RuntimeError) as e:
        pytest.skip(f"vLLM backend not available or failed to init: {e}")

def test_encoder_invalid_backend():
    with pytest.raises(ValueError):
        Encoder(model_name="sshleifer/tiny-gpt2", backend="invalid")

def test_encoder_encode_transformers():
    enc = Encoder(model_name="sshleifer/tiny-gpt2", backend="transformers")
    res = enc.encode("hello")
    assert res is not None

def test_encoder_encode_vllm():
    try:
        enc = Encoder(model_name="sshleifer/tiny-gpt2", backend="vllm")
        res = enc.encode("hello")
        assert res is not None
    except (ImportError, ValueError, RuntimeError) as e:
        pytest.skip(f"vLLM backend not available or failed to init: {e}")