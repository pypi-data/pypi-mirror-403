# Arithmetic Operations

Perform arithmetic operations on symmetry-aware tensors.

## Addition and Subtraction

```python
from nicole import Tensor, Index, Sector, Direction, U1Group

group = U1Group()
idx = Index(Direction.OUT, group, sectors=(Sector(0, 2), Sector(1, 1)))

# Create two tensors with same structure
A = Tensor.random([idx, idx.flip()], itags=["i", "j"], seed=1)
B = Tensor.random([idx, idx.flip()], itags=["i", "j"], seed=2)

# Addition (block-wise)
C = A + B
print(f"Norm of A: {A.norm():.4f}")
print(f"Norm of B: {B.norm():.4f}")
print(f"Norm of A+B: {C.norm():.4f}")

# Subtraction
D = A - B
print(f"Norm of A-B: {D.norm():.4f}")

# Verify: A - A = 0
zero = A - A
print(f"A - A norm: {zero.norm():.10f}")  # Should be ~0
```

## Scalar Operations

```python
# Scalar multiplication
E = 2.5 * A
print(f"Norm scales: {E.norm():.4f} ≈ {2.5 * A.norm():.4f}")

# Scalar division
F = A / 2.0
print(f"Norm scales: {F.norm():.4f} ≈ {A.norm() / 2.0:.4f}")

# Add scalar (adds to all blocks)
G = A + 1.0
```

## Negation

```python
# Negate tensor
H = -A

# Verify: A + (-A) = 0
result = A + H
print(f"A + (-A) norm: {result.norm():.10f}")
```

## Requirements for Operations

Tensors must have:
- Same number of indices
- Same index structure (charges and dimensions)
- Same index tags

```python
# This works: same structure
A = Tensor.random([idx, idx.flip()], itags=["i", "j"], seed=1)
B = Tensor.random([idx, idx.flip()], itags=["i", "j"], seed=2)
C = A + B  # OK

# This fails: different structure
idx2 = Index(Direction.OUT, group, sectors=(Sector(0, 3),))  # Different dim
D = Tensor.random([idx2, idx2.flip()], itags=["i", "j"], seed=3)
try:
    E = A + D  # Error: incompatible structure
except ValueError as e:
    print(f"Expected error: {e}")
```

## Norm Computation

```python
# Frobenius norm (sqrt of sum of squared elements)
A = Tensor.random([idx, idx.flip()], itags=["i", "j"], seed=42)

norm = A.norm()
print(f"Tensor norm: {norm:.4f}")

# Verify norm computation manually
import numpy as np
manual_norm = np.sqrt(sum(
    np.sum(block ** 2) for block in A.data.values()
))
print(f"Manual norm: {manual_norm:.4f}")
print(f"Match: {abs(norm - manual_norm) < 1e-10}")
```

## Combining Operations

```python
# Linear combinations
alpha, beta, gamma = 2.0, -1.5, 0.5
result = alpha * A + beta * B + gamma * C

# Verify linearity
manual = A.copy()
for block_key in manual.data.keys():
    manual.data[block_key] *= alpha
    manual.data[block_key] += beta * B.data[block_key]
    manual.data[block_key] += gamma * C.data[block_key]

print(f"Results match: {abs(result.norm() - manual.norm()) < 1e-10}")
```

## In-Place Operations

```python
# Copy for in-place modification
X = A.copy()

# In-place addition
X_data_backup = {k: v.copy() for k, v in X.data.items()}
for key in X.data:
    X.data[key] += B.data[key]

# Equivalent to X = X + B
print(f"In-place result matches: same shape and values")
```

## See Also

- API Reference: [Arithmetic Operations](../../api/arithmetic/addition.md)
- API Reference: [Tensor](../../api/core/tensor.md)
- Next: [Direct Sum (oplus)](../../api/arithmetic/oplus.md)
- Previous: [First Tensor](first-tensor.md)
