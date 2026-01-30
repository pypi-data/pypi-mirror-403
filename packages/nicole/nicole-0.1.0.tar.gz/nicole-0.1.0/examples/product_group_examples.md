# ProductGroup: Multiple Abelian Symmetries

The `ProductGroup` class enables tensors with multiple independent conserved quantities, such as particle number and spin, or multiple U(1) symmetries.

## Basic Usage

### Creating a ProductGroup

```python
from nicole import ProductGroup, U1Group, Z2Group

# U(1) × U(1) for particle number and spin
group = ProductGroup([U1Group(), U1Group()])
print(group.name)  # "U1×U1"
print(group.neutral)  # (0, 0)

# U(1) × Z(2) for particle number and parity
group = ProductGroup([U1Group(), Z2Group()])
print(group.name)  # "U1×Z2"
print(group.neutral)  # (0, 0)
```

### Charge Operations

With ProductGroup, charges are tuples where each component corresponds to one symmetry:

```python
group = ProductGroup([U1Group(), U1Group()])

# Fuse charges component-wise
charge1 = (2, -1)  # particle=2, spin=-1
charge2 = (1, 3)   # particle=1, spin=3
fused = group.fuse(charge1, charge2)
print(fused)  # (3, 2)

# Inverse
inv = group.inverse((5, -2))
print(inv)  # (-5, 2)

# Equality
print(group.equal((1, 0), (1, 0)))  # True
print(group.equal((1, 0), (0, 1)))  # False
```

## Creating Tensors with ProductGroup

### Index Construction

```python
from nicole import Index, Sector, Direction, ProductGroup, U1Group

group = ProductGroup([U1Group(), U1Group()])

# Create an index with composite charge sectors
# Each sector has a tuple charge (particle, spin) and a dimension
left = Index(
    Direction.OUT,
    group,
    sectors=(
        Sector((0, 0), 2),   # neutral state, dim=2
        Sector((1, 0), 1),   # particle=1, spin=0, dim=1
        Sector((0, 1), 1),   # particle=0, spin=1, dim=1
    )
)

right = Index(
    Direction.IN,
    group,
    sectors=(
        Sector((0, 0), 3),   # neutral state, dim=3
        Sector((1, 0), 2),   # particle=1, spin=0, dim=2
        Sector((0, 1), 1),   # particle=0, spin=1, dim=1
    )
)
```

### Tensor Construction

```python
from nicole import Tensor

# Create zero tensor
tensor = Tensor.zeros([left, right], itags=["L", "R"])

# Create random tensor
tensor = Tensor.random([left, right], seed=42, itags=["L", "R"])

# Charge conservation: OUT charges must equal IN charges
# Valid blocks: ((0,0), (0,0)), ((1,0), (1,0)), ((0,1), (0,1))
print(f"Number of blocks: {len(tensor.data)}")
for key in tensor.data:
    print(f"Block {key}: shape {tensor.data[key].shape}")
```

## Tensor Operations with ProductGroup

### Arithmetic Operations

```python
# Addition and subtraction
A = Tensor.random([left], seed=1, itags=["x"])
B = Tensor.random([left], seed=2, itags=["x"])

C = A + B  # Block-wise addition
D = A - B  # Block-wise subtraction

# Scalar multiplication
E = 2.5 * A
```

### Contraction

```python
from nicole import contract

group = ProductGroup([U1Group(), U1Group()])

# Create compatible indices
idx_out = Index(Direction.OUT, group, sectors=(
    Sector((0, 0), 2),
    Sector((1, -1), 1),
))
idx_in = Index(Direction.IN, group, sectors=(
    Sector((0, 0), 2),
    Sector((1, -1), 1),
))

A = Tensor.random([idx_out, idx_out], seed=10, itags=["a", "mid"])
B = Tensor.random([idx_in, idx_out], seed=11, itags=["mid", "b"])

# Automatic contraction on matching tags with opposite directions
result = contract(A, B)
print(result.itags)  # ('a', 'b')

# Manual contraction
result = contract(A, B, pairs=[(1, 0)])
```

### Trace Operations

```python
from nicole import trace

group = ProductGroup([U1Group(), Z2Group()])

left = Index(Direction.OUT, group, sectors=(
    Sector((0, 0), 2),
    Sector((1, 1), 1),
))
right = Index(Direction.IN, group, sectors=(
    Sector((0, 0), 2),
    Sector((1, 1), 1),
))

T = Tensor.random([left, right], seed=99, itags=["i", "j"])

# Trace over both indices
scalar = trace(T, pairs=[(0, 1)])
print(f"Trace result has {len(scalar.indices)} indices")  # 0 (scalar)
```

## Use Cases

### 1. Spin-1/2 Systems with Conservation

```python
# U(1) for particle number, U(1) for S_z (spin projection)
group = ProductGroup([U1Group(), U1Group()])

# States: |particle number, spin⟩
idx = Index(Direction.OUT, group, sectors=(
    Sector((0, 0), 1),     # vacuum
    Sector((1, 1), 1),     # one particle, spin up
    Sector((1, -1), 1),    # one particle, spin down
    Sector((2, 0), 1),     # two particles, total spin 0
))
```

### 2. Fermions with Parity

```python
# U(1) for particle number, Z(2) for fermion parity
group = ProductGroup([U1Group(), Z2Group()])

idx = Index(Direction.OUT, group, sectors=(
    Sector((0, 0), 1),   # vacuum, even parity
    Sector((1, 1), 2),   # one particle, odd parity
    Sector((2, 0), 3),   # two particles, even parity
))
```

### 3. Multiple U(1) Symmetries

```python
# U(1) × U(1) × U(1) for three independent conserved quantities
group = ProductGroup([U1Group(), U1Group(), U1Group()])

idx = Index(Direction.OUT, group, sectors=(
    Sector((0, 0, 0), 1),
    Sector((1, 0, 0), 2),
    Sector((0, 1, 0), 2),
    Sector((0, 0, 1), 2),
))
```

## Index Fusion with ProductGroup

```python
from nicole.index import combine_indices, split_index

group = ProductGroup([U1Group(), Z2Group()])

idx1 = Index(Direction.OUT, group, sectors=(
    Sector((0, 0), 2),
    Sector((1, 1), 1)
))
idx2 = Index(Direction.OUT, group, sectors=(
    Sector((0, 0), 1),
    Sector((1, 0), 2)
))

# Combine indices (tensor product)
combined = combine_indices(Direction.OUT, idx1, idx2)

# Sectors in combined index:
# (0,0) ⊗ (0,0) → (0,0) with dim 2*1=2
# (0,0) ⊗ (1,0) → (1,0) with dim 2*2=4
# (1,1) ⊗ (0,0) → (1,1) with dim 1*1=1
# (1,1) ⊗ (1,0) → (2,1) with dim 1*2=2

# Split back to verify
recovered = split_index(combined, [idx1, idx2])
assert recovered == (idx1, idx2)
```

## Display

Tensors with ProductGroup charges are displayed with tuple charges:

```python
group = ProductGroup([U1Group(), U1Group()])
idx = Index(Direction.OUT, group, sectors=(Sector((0, 0), 2), Sector((1, -1), 1)))
T = Tensor.random([idx], itags=["x"])
print(T)
```

Output:
```
  info:  1x { 1 x 2 }  having 'U1×U1'  Tensor,  { x* }
  data:  1-D float64 (24 B)    2 => 3 @ norm = 1.45621

     1.  2       |  1       [ 0 0 ]     16 B
     2.  1       |  1       [ 1 -1 ]    8 B
```

## Technical Notes

### Architecture

- `ProductGroup` inherits directly from `SymmetryGroup` (not `AbelianGroup`)
- Currently restricted to Abelian component groups
- Future extension will support non-Abelian groups in products

### Charge Representation

- Single symmetry groups: charges are integers (e.g., `2`, `-1`, `0`)
- ProductGroup: charges are tuples (e.g., `(2, -1)`, `(0, 0, 1)`)

### Charge Conservation

For a tensor with ProductGroup, charge conservation is enforced component-wise:
```
∑ OUT_charges - ∑ IN_charges = (0, 0, ..., 0)
```

Each component must independently conserve to the neutral element of its group.
