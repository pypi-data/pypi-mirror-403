# Contraction Examples

Contract, trace, and multiply tensors.

## Basic Contraction

```python
from nicole import contract, Tensor, Index, Sector, Direction, U1Group

group = U1Group()
idx_out = Index(Direction.OUT, group, sectors=(Sector(0, 2), Sector(1, 1)))
idx_in = Index(Direction.IN, group, sectors=(Sector(0, 2), Sector(1, 1)))

# Create two tensors
A = Tensor.random([idx_out, idx_out], itags=["i", "mid"], seed=10)
B = Tensor.random([idx_in, idx_out], itags=["mid", "j"], seed=11)

# Automatic contraction (matching tags with opposite directions)
C = contract(A, B)
print(f"Result indices: {C.itags}")  # ('i', 'j')
print(f"Result has {len(C.data)} blocks")
```

## Manual Pair Specification

```python
# Specify axes explicitly: (axis_in_A, axis_in_B)
result = contract(A, B, axes=(1, 0))
print(f"Same result: {result.itags}")  # ('i', 'j')
```

## Matrix-Vector Multiplication

```python
# Two matrices to contract
M = Tensor.random([idx_out, idx_in], itags=["i", "j"], seed=20)
v = Tensor.random([idx_out, idx_in], itags=["j", "k"], seed=21)

# Multiply: M @ v (contracts on "j")
result = contract(M, v)
print(f"Result indices: {result.itags}")  # ('i', 'k')
```

## Full Contraction (Scalar Result)

```python
# Two tensors that fully contract
T1 = Tensor.random([idx_out, idx_in], itags=["i", "j"], seed=1)
T2 = Tensor.random([idx_out, idx_in], itags=["i", "j"], seed=2)

# Full contraction: all indices contract
scalar = contract(T1, T2)
print(f"Scalar result: {scalar.norm():.4f}")
print(f"Number of indices: {len(scalar.indices)}")  # 0
```

## Trace

```python
from nicole import trace

# Square tensor
T = Tensor.random([idx_out, idx_in], itags=["i", "j"], seed=99)

# Compute trace (scalar result)
tr = trace(T, axes=(0, 1))
print(f"Trace: {tr.norm():.4f}")
print(f"Result is scalar: {len(tr.indices) == 0}")

# Can also specify by tags
tr2 = trace(T, axes=("i", "j"))
```

## Trace Operations

```python
from nicole import trace

# 4-index tensor with paired itags
idx = Index(Direction.OUT, group, sectors=(Sector(0, 2), Sector(1, 1)))
T = Tensor.random(
    [idx, idx.flip(), idx, idx.flip()],
    itags=["a", "a", "b", "b"],
    seed=77
)

# Automatic mode: trace all matching pairs
result = trace(T)
print(f"Result is scalar: {result.is_scalar()}")  # True (all pairs traced)

# Manual mode: trace specific pair only
partial = trace(T, axes=(0, 1))
print(f"Remaining indices: {partial.itags}")  # ('b', 'b')

# Exclusion mode: trace all except specified
partial2 = trace(T, excl=[0, 1])
print(f"Remaining indices: {partial2.itags}")  # ('a', 'a')
```

## Multiple Contractions

```python
# Contract three tensors: A-B-C
A = Tensor.random([idx_out, idx_out], itags=["i", "mid1"], seed=1)
B = Tensor.random([idx_in, idx_out], itags=["mid1", "mid2"], seed=2)
C = Tensor.random([idx_in, idx_out], itags=["mid2", "j"], seed=3)

# Contract step by step
AB = contract(A, B)
print(f"After A-B: {AB.itags}")  # ('i', 'mid2')

ABC = contract(AB, C)
print(f"After A-B-C: {ABC.itags}")  # ('i', 'j')
```

## See Also

- API Reference: [contract](../../api/contraction/contract.md)
- API Reference: [trace](../../api/contraction/trace.md)
