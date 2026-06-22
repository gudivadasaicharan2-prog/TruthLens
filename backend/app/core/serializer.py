import numpy as np
from typing import Any

try:
    import torch as _torch
    _TORCH_AVAILABLE = True
except ImportError:
    _torch = None
    _TORCH_AVAILABLE = False

def to_python(obj: Any) -> Any:
    if _TORCH_AVAILABLE and _torch is not None and isinstance(obj, _torch.Tensor):
        return to_python(obj.detach().cpu().numpy())
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        return float(obj)
    if isinstance(obj, np.bool_):
        return bool(obj)
    if isinstance(obj, np.ndarray):
        return [to_python(x) for x in obj.tolist()]
    if isinstance(obj, float):
        if np.isnan(obj) or np.isinf(obj):
            return 0.0
        return round(obj, 4)
    if isinstance(obj, dict):
        return {k: to_python(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [to_python(x) for x in obj]
    return obj

def safe_float(val, default=0.0) -> float:
    try:
        result = float(val)
        if np.isnan(result) or np.isinf(result):
            return default
        return round(result, 4)
    except:
        return default

def safe_int(val, default=0) -> int:
    try:
        return int(val)
    except:
        return default
