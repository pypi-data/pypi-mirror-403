
from .._type import SpatialTensor
import torch

def wave_1d(
    x: SpatialTensor["B C H ..."],
    min_k: int = 1,
    max_k: int = 5,
    min_amplitude: float = 0.5,
    max_amplitude: float = 1.0,
    n_polynomial: int = 5,
    zero_mean: bool = False,
    mean_shift_coef=0.3,
    batched: bool = False,
) -> SpatialTensor["B C H ..."]:
    r"""
    Generate a 1D wave field with multiple harmonics.

    Args:
        x (SpatialTensor["B C H ..."]): The input tensor.
        min_k (int): The minimum wave number. Default is 1.
        max_k (int): The maximum wave number. Default is 5.
        min_amplitude (float): The minimum amplitude. Default is 0.5.
        max_amplitude (float): The maximum amplitude. Default is 1.0.
        n_polynomial (int): The number of polynomial terms. Default is 5.
        zero_mean (bool): If True, the mean of the wave will be zero. Default is False.
        mean_shift_coef (float): The coefficient for mean shift. Default is 0.3.
        batched (bool): If True, the input tensor is batched. Default is False.
    
    Returns:
        SpatialTensor["B C H ..."]: The generated wave field.
    """
    x_new = x / x.max() * torch.pi * 2
    y = torch.zeros_like(x)
    if not batched:
        x_new = x_new.unsqueeze(0)
        y = y.unsqueeze(0)
    batch = x_new.shape[0]
    shape = [batch, n_polynomial] + [1] * (x_new.dim() - 2)
    k = torch.randint(min_k, max_k + 1, shape, device=x.device, dtype=x.dtype)
    amplitude = (
        torch.rand(*shape, device=x.device, dtype=x.dtype)
        * (max_amplitude - min_amplitude)
        + min_amplitude
    )
    shift = torch.rand(*shape, device=x.device, dtype=x.dtype) * torch.pi * 2
    for i in range(n_polynomial):
        y += amplitude[:, i : i + 1, ...] * torch.sin(
            k[:, i : i + 1, ...] * (x_new + shift[:, i : i + 1, ...])
        )
    if not zero_mean:
        value_shift = torch.rand(
            [batch] + [1] * (x_new.dim() - 1), device=x.device, dtype=x.dtype
        )
        value_shift = (value_shift - 0.5) * 2 * (
            max_amplitude - min_amplitude
        ) * mean_shift_coef + min_amplitude
        y += value_shift
    if not batched:
        y = y.squeeze(0)
    return y