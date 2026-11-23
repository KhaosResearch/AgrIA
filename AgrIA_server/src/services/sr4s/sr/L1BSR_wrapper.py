import os

import numpy as np
import torch
from safetensors.torch import load_file as load_safetensors

from .RCAN_wrapper import RCAN
from .utils import from_torch_to_u16, to_torch_4ch


class L1BSR:
    def __init__(self, weights_path: str, device: str | None = None):
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = torch.device(device)
        self.model = RCAN(n_colors=4).to(self.device).eval()
        if not os.path.isfile(weights_path):
            raise FileNotFoundError(f"Model file not found: {weights_path}")
        state = load_safetensors(weights_path, device="cpu")
        self.model.load_state_dict(state, strict=False)
        torch.set_grad_enabled(False)

    @torch.inference_mode()
    def super_resolve(self, img_bgrn_u16: np.ndarray) -> np.ndarray:
        ten = to_torch_4ch(img_bgrn_u16, self.device)
        sr = self.model(ten)
        out = from_torch_to_u16(sr)
        return out
