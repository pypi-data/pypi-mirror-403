# Decomposition Examples

SVD and tensor decomposition.

## Basic SVD

```python
from nicole import decomp, Tensor, Index, Sector, Direction, U1Group

group = U1Group()
idx = Index(Direction.OUT, group, sectors=(Sector(0, 3), Sector(1, 2)))

# Create a tensor
T = Tensor.random([idx, idx.flip()], itags=["i", "j"], seed=7)

# Perform SVD: T ≈ U @ S @ Vh
U, S, Vh = decomp(T, axes=0, mode="SVD")

print(f"U indices: {U.itags}")   # ('i', '_bond_L')
print(f"S indices: {S.itags}")   # ('_bond_L', '_bond_R')
print(f"Vh indices: {Vh.itags}") # ('_bond_R', 'j')

# Verify reconstruction
from nicole import contract
US = contract(U, S)  # U @ S
T_reconstructed = contract(US, Vh)  # (U @ S) @ Vh
error = (T - T_reconstructed).norm() / T.norm()
print(f"Reconstruction error: {error:.2e}")
```

## UR Decomposition

```python
# Get U and R = S @ Vh combined
U, R = decomp(T, axes=0, mode="UR")

print(f"U indices: {U.itags}")  # ('i', '_bond_')
print(f"R indices: {R.itags}")  # ('_bond_', 'j')

# Verify
T_reconstructed = contract(U, R)
error = (T - T_reconstructed).norm() / T.norm()
print(f"Reconstruction error: {error:.2e}")
```

## LV Decomposition

```python
# Get L = U @ S and V combined
L, V = decomp(T, axes=0, mode="LV")

print(f"L indices: {L.itags}")  # ('i', '_bond_')
print(f"V indices: {V.itags}")  # ('_bond_', 'j')

# Verify
T_reconstructed = contract(L, V)
error = (T - T_reconstructed).norm() / T.norm()
print(f"Reconstruction error: {error:.2e}")
```

## Truncation: Keep N Values

```python
# Keep at most 10 singular values globally
U_trunc, S_trunc, Vh_trunc = decomp(T, axes=0, mode="SVD", trunc=("nkeep", 10))

print(f"Original bond dim: {U.indices[1].dim}")
print(f"Truncated bond dim: {U_trunc.indices[1].dim}")

# Compare norms
print(f"Original norm: {T.norm():.4f}")
US_trunc = contract(U_trunc, S_trunc)
T_trunc = contract(US_trunc, Vh_trunc)
print(f"Truncated norm: {T_trunc.norm():.4f}")

# Truncation error
error = (T - T_trunc).norm() / T.norm()
print(f"Relative error: {error:.4f}")
```

## Truncation: Threshold

```python
# Keep singular values >= 1e-10
U_thresh, S_thresh, Vh_thresh = decomp(T, axes=0, mode="SVD", trunc=("thresh", 1e-10))

print(f"Threshold truncated bond dim: {U_thresh.indices[1].dim}")
```

## Multi-Index Decomposition

```python
# Decompose 4-index tensor
idx = Index(Direction.OUT, group, sectors=(Sector(0, 2), Sector(1, 1)))
T4 = Tensor.random([idx, idx.flip(), idx, idx.flip()], itags=["a", "b", "c", "d"], seed=42)

# Partition: (a, b) | (c, d)
U, S, Vh = decomp(T4, axes=1, mode="SVD")

print(f"U indices: {U.itags}")   # ('a', 'b', '_bond_')
print(f"Vh indices: {Vh.itags}") # ('_bond_', 'c', 'd')
```

## Examining Singular Values

```python
from nicole.decomp import svd

# Low-level SVD for singular value access
U, S_dict, Vh = svd(T, axes=0)

# S_dict maps block keys to 1D singular value arrays
for key, s_values in S_dict.items():
    print(f"Block {key}:")
    print(f"  Number of singular values: {len(s_values)}")
    print(f"  Largest: {s_values[0]:.4f}")
    print(f"  Smallest: {s_values[-1]:.4f}")
    print(f"  Ratio: {s_values[0] / s_values[-1]:.2e}")
```

## See Also

- API Reference: [decomp](../../api/decomposition/decomp.md)
- API Reference: [svd](../../api/decomposition/svd.md)
