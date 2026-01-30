# Manipulation Examples

Permute, transpose, and conjugate tensors.

## Conjugation

```python
from nicole import conj, Tensor, Index, Sector, Direction, U1Group
import numpy as np

group = U1Group()
idx = Index(Direction.OUT, group, sectors=(Sector(0, 2), Sector(1, 1)))

# Complex tensor
T = Tensor.random([idx, idx.flip()], itags=["i", "j"], dtype=np.complex128, seed=42)

# Conjugate (flips directions + conjugates data)
T_conj = conj(T)

print(f"Original directions: {[i.direction for i in T.indices]}")
print(f"Conjugated directions: {[i.direction for i in T_conj.indices]}")
```

## Permutation

```python
from nicole import permute

# 3-index tensor
T = Tensor.random([idx, idx.flip(), idx], itags=["i", "j", "k"], seed=7)
print(f"Original tags: {T.itags}")

# Permute to (k, i, j)
T_perm = permute(T, [2, 0, 1])
print(f"Permuted tags: {T_perm.itags}")

# Original unchanged (functional operation)
print(f"Original still: {T.itags}")
```

## Transpose

```python
from nicole import transpose

# Default: reverse all axes
T_trans = transpose(T)
print(f"Transposed tags: {T_trans.itags}")  # ('k', 'j', 'i')

# Custom order
T_trans2 = transpose(T, 1, 0, 2)
print(f"Custom transpose: {T_trans2.itags}")  # ('j', 'i', 'k')
```

## In-Place vs Functional

```python
# In-place modification
T_inplace = T.copy()
T_inplace.permute([2, 0, 1])
print(f"After in-place permute: {T_inplace.itags}")

# Functional (returns new tensor)
T_functional = permute(T, [2, 0, 1])
print(f"Original unchanged: {T.itags}")
print(f"New tensor: {T_functional.itags}")
```

## Hermitian Conjugate

```python
# For matrices: A† = (A*)ᵀ
A = Tensor.random([idx, idx.flip()], itags=["i", "j"], dtype=np.complex128, seed=11)

# Method 1: conj then transpose
A_dag1 = transpose(conj(A))

# Method 2: transpose then conj
A_dag2 = conj(transpose(A))

# Both give same result
error = (A_dag1 - A_dag2).norm()
print(f"Methods match: {error < 1e-10}")
```

## Cyclic Permutation

```python
# Move first axis to last
n = len(T.indices)
T_cycle = permute(T, list(range(1, n)) + [0])
print(f"Cycled: {T.itags}")  # e.g., ('j', 'k', 'i') from ('i', 'j', 'k')
```

## See Also

- API Reference: [conj](../../api/manipulation/conjugate.md)
- API Reference: [permute](../../api/manipulation/permute.md)
- API Reference: [transpose](../../api/manipulation/transpose.md)
