"""Normalize chat-template token IDs for tensor and BatchEncoding outputs.

No re-tokenization or prompt changes. Fail closed on ambiguous shapes.
"""
from __future__ import annotations
from collections.abc import Mapping

def chat_input_ids(encoded):
    """Return a 1 x N torch tensor of input IDs, preserving the emitted IDs."""
    import torch
    if isinstance(encoded, Mapping):
        if 'input_ids' not in encoded:
            raise RuntimeError('CHAT_ENCODING_MISSING_INPUT_IDS')
        ids = encoded['input_ids']
    else:
        ids = encoded
    if isinstance(ids, torch.Tensor):
        tensor=ids
    else:
        try:tensor=torch.as_tensor(ids)
        except (ValueError,TypeError,RuntimeError) as e:
            raise RuntimeError('CHAT_ENCODING_NOT_NUMERIC') from e
    if tensor.ndim == 1:
        tensor=tensor.unsqueeze(0)
    if tensor.ndim != 2 or tensor.shape[0] != 1 or tensor.shape[1] == 0:
        raise RuntimeError('CHAT_ENCODING_SHAPE '+str(tuple(tensor.shape)))
    if tensor.dtype not in (torch.int64,torch.int32,torch.int16,torch.int8,torch.uint8):
        raise RuntimeError('CHAT_ENCODING_NOT_INTEGER '+str(tensor.dtype))
    if (tensor < 0).any():
        raise RuntimeError('CHAT_ENCODING_NEGATIVE_ID')
    return tensor.to(dtype=torch.long)
