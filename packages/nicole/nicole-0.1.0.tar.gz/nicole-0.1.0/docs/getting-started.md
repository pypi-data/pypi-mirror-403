# Getting Started

This guide will help you get up and running with Nicole, from installation to creating your first symmetry-aware tensors.

## Installation

### From Source (Development)

Currently, Nicole is available for installation from source:

```bash
# Clone the repository
git clone https://github.com/Ideogenesis-AI/Nicole.git
cd Nicole

# Install in development mode
pip install -e .

# Optional: Install with testing dependencies
pip install -e ".[test]"

# Optional: Install with documentation dependencies
pip install -e ".[docs]"
```

### Requirements

- Python 3.11 or higher
- NumPy 2.0 or higher

## Core Concepts

Before diving into code, let's understand the key concepts in Nicole:

### Symmetry Groups

Nicole supports Abelian symmetry groups that represent conserved quantum numbers:

- **U(1)**: Continuous symmetry with integer charges (e.g., particle number, magnetization)
- **Z(2)**: Binary symmetry with charges 0 or 1 (e.g., parity)
- **ProductGroup**: Combines multiple symmetries (e.g., U(1) × Z(2) for particle number and parity)

### Charges

Charges are quantum numbers that label sectors of a tensor:

- For U(1): integers like -2, -1, 0, 1, 2
- For Z(2): 0 or 1
- For ProductGroup: tuples like (1, 0) or (2, 1)

### Sectors

A **Sector** pairs a charge with a dimension, representing a subspace of the tensor:

```python
from nicole import Sector

# A sector with charge 1 and dimension 3 (3 states with charge +1)
sector = Sector(charge=1, dim=3)
```

### Indices

An **Index** defines a tensor leg with:

- **Direction**: `Direction.OUT` or `Direction.IN` (for charge conservation rules)
- **Symmetry Group**: The group governing the charge structure
- **Sectors**: Available charge sectors and their dimensions

### Charge Conservation

Nicole automatically enforces charge conservation:

```
∑ OUT_charges - ∑ IN_charges = 0 (neutral element)
```

Only tensor blocks satisfying this rule are created and stored.

## Your First Tensor

Let's create a simple U(1) symmetric tensor:

```python
from nicole import Tensor, Index, Sector, Direction, U1Group

# 1. Create a U(1) symmetry group
group = U1Group()

# 2. Define an outgoing index with three sectors
index_out = Index(
    Direction.OUT,
    group,
    sectors=(
        Sector(charge=0, dim=2),   # neutral sector with 2 states
        Sector(charge=1, dim=1),   # charge +1 with 1 state
        Sector(charge=-1, dim=1),  # charge -1 with 1 state
    )
)

# 3. Define an incoming index (charge conjugate)
index_in = Index(
    Direction.IN,
    group,
    sectors=(
        Sector(charge=0, dim=3),
        Sector(charge=1, dim=2),
        Sector(charge=-1, dim=1),
    )
)

# 4. Create a zero tensor
tensor_zero = Tensor.zeros([index_out, index_in], itags=["i", "j"])
print("Zero tensor:")
print(tensor_zero)

# 5. Create a random tensor
tensor_random = Tensor.random([index_out, index_in], itags=["i", "j"], seed=42)
print("\nRandom tensor:")
print(tensor_random)
```

### Understanding the Output

When you print a tensor, Nicole displays:

```
  info:  2x { 3 x 1 }  having 'U1'  Tensor,  { i* j }
  data:  2-D float64 (88 B)    4 => 10 @ norm = 2.34567

     1.  2  3    |  6       [ 0 0 ]     48 B
     2.  1  2    |  2       [ 1 1 ]     16 B
     3.  1  1    |  1       [-1 -1 ]    8 B
```

- **info**: Tensor shape, symmetry type, and index tags (* marks OUT direction)
- **data**: Data type, total bytes, total multiplets => total states, Frobenius norm
- **Blocks**: Each line shows block dimensions, charges, and memory usage

## Basic Operations

### Arithmetic

Tensors with the same index structure support arithmetic:

```python
from nicole import Tensor, Index, Sector, Direction, U1Group

group = U1Group()
index = Index(Direction.OUT, group, sectors=(Sector(0, 2), Sector(1, 1)))

A = Tensor.random([index, index.flip()], itags=["i", "j"], seed=1)
B = Tensor.random([index, index.flip()], itags=["i", "j"], seed=2)

# Addition and subtraction
C = A + B
D = A - B

# Scalar multiplication
E = 2.5 * A

# Norm
print(f"Norm of A: {A.norm()}")
```

### Tensor Contraction

Contract two tensors along matching indices:

```python
from nicole import contract, Tensor, Index, Sector, Direction, U1Group

group = U1Group()

# Create compatible indices
idx_out = Index(Direction.OUT, group, sectors=(Sector(0, 2), Sector(1, 1)))
idx_in = Index(Direction.IN, group, sectors=(Sector(0, 2), Sector(1, 1)))

# Create tensors
A = Tensor.random([idx_out, idx_out], itags=["i", "mid"], seed=10)
B = Tensor.random([idx_in, idx_out], itags=["mid", "j"], seed=11)

# Contract automatically on matching tags with opposite directions
result = contract(A, B)
print(f"Result has indices: {result.itags}")  # ('i', 'j')

# Or specify contraction pairs explicitly
result2 = contract(A, B, axes=(1, 0))
```

### Trace

Take the trace of a tensor:

```python
from nicole import trace, Tensor, Index, Sector, Direction, U1Group

group = U1Group()
left = Index(Direction.OUT, group, sectors=(Sector(0, 2), Sector(1, 1)))
right = Index(Direction.IN, group, sectors=(Sector(0, 2), Sector(1, 1)))

T = Tensor.random([left, right], itags=["i", "j"], seed=99)

# Trace over both indices
scalar = trace(T, axes=(0, 1))
print(f"Trace result: {scalar.norm()}")
```

### Permutation and Transpose

Reorder tensor axes:

```python
from nicole import permute, transpose, Tensor, Index, Sector, Direction, U1Group

group = U1Group()
idx = Index(Direction.OUT, group, sectors=(Sector(0, 2),))

T = Tensor.random([idx, idx.flip(), idx], itags=["i", "j", "k"], seed=5)

# Permute axes
T_perm = permute(T, [2, 0, 1])  # k, i, j
print(f"Permuted tags: {T_perm.itags}")

# Transpose (reverses axis order by default)
T_trans = transpose(T)  # k, j, i
print(f"Transposed tags: {T_trans.itags}")
```

### Decomposition (SVD)

Decompose a tensor using SVD:

```python
from nicole import decomp, Tensor, Index, Sector, Direction, U1Group

group = U1Group()
idx = Index(Direction.OUT, group, sectors=(Sector(0, 3), Sector(1, 2)))

T = Tensor.random([idx, idx.flip()], itags=["i", "j"], seed=7)

# Perform SVD: T ≈ U @ S @ Vh
U, S, Vh = decomp(T, axes=0, mode="SVD")

print(f"U shape: {U.itags}")   # ('i', '_bond_')
print(f"S shape: {S.itags}")   # ('_bond_', '_bond_')
print(f"Vh shape: {Vh.itags}") # ('_bond_', 'j')
```

## Working with Multiple Symmetries

Use `ProductGroup` to combine multiple symmetries:

```python
from nicole import ProductGroup, U1Group, Z2Group, Index, Sector, Direction, Tensor

# Create U(1) × Z(2) group (particle number and parity)
group = ProductGroup([U1Group(), Z2Group()])

# Create index with composite charges (particle, parity)
index = Index(
    Direction.OUT,
    group,
    sectors=(
        Sector((0, 0), 1),  # vacuum: no particles, even parity
        Sector((1, 1), 2),  # one particle, odd parity
        Sector((2, 0), 1),  # two particles, even parity
    )
)

# Create and manipulate tensors as before
T = Tensor.random([index, index.flip()], itags=["i", "j"], seed=42)
print(T)
```

## Next Steps

Now that you understand the basics, explore:

- **[API Reference](api/index.md)**: Detailed documentation of all classes and functions
- **[Examples](examples/index.md)**: More complex use cases and patterns
- **[Tutorials](tutorials/index.md)**: In-depth guides for specific applications

## Common Patterns

### Creating Identity Tensors

```python
from nicole import identity, Index, Sector, Direction, U1Group

group = U1Group()
idx = Index(Direction.OUT, group, sectors=(Sector(0, 2), Sector(1, 1)))

# Create identity tensor
I = identity(idx, itags=("i", "j"))
```

### Accessing Specific Blocks

```python
# Access blocks by integer index (1-indexed)
first_block = tensor.block(1)

# Get block key
key = tensor.key(1)

# Access blocks via data dictionary
for key, block_array in tensor.data.items():
    print(f"Block {key}: shape {block_array.shape}")
```

### Conjugation

```python
from nicole import conj

# Conjugate tensor (flips all index directions)
T_conj = conj(T)
```

## Tips

1. **Index Tags**: Use descriptive tags for indices to make contractions more intuitive
2. **Seeds**: Use seeds with `Tensor.random()` for reproducible results
3. **Display**: Call `print(tensor)` to see the block structure and validate charge conservation
4. **Direction**: Remember that OUT and IN directions must match for valid contractions
5. **Performance**: Nicole automatically handles only admissible blocks, saving memory and computation

## Troubleshooting

### ValueError: Sector dim must be positive

Ensure all sector dimensions are positive integers when creating indices.

### ValueError: Duplicate sector charge

Each charge can appear only once per index. Check your sector definitions.

### Contraction fails

Verify that:
- Tags match between tensors
- Directions are opposite (OUT ↔ IN)
- Symmetry groups are compatible

## Getting Help

- **Documentation**: Browse the [API Reference](api/index.md)
- **Issues**: Report bugs on [GitHub](https://github.com/Ideogenesis-AI/Nicole/issues)
- **Examples**: Check the [Examples](examples/index.md) section
