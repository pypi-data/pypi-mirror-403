# Custom Operators

Build physical operators with symmetries.

## Identity Operator

```python
from nicole import identity, Index, Sector, Direction, U1Group

group = U1Group()
idx = Index(Direction.OUT, group, sectors=(Sector(0, 2), Sector(1, 1)))

# Create identity operator
I = identity(idx, itags=("i", "j"))

print(f"Identity has {len(I.data)} blocks")
print("Identity blocks:")
for key, block in I.data.items():
    print(f"  {key}: {block.shape}, diag = {np.diag(block) if block.shape[0] == block.shape[1] else 'N/A'}")
```

## Fusion Isometry

```python
from nicole import isometry

# Fuse two indices into one
idx1 = Index(Direction.OUT, group, sectors=(Sector(0, 2), Sector(1, 1)))
idx2 = Index(Direction.OUT, group, sectors=(Sector(0, 1), Sector(1, 2)))

# Create fusion tensor
iso = isometry(idx1, idx2, itags=("i", "j", "ij"))

print(f"Isometry indices: {iso.itags}")
print(f"Fused index dim: {iso.indices[2].dim}")
```

## Number Operator

```python
# Diagonal operator that returns the charge value
group = U1Group()
idx = Index(Direction.OUT, group, sectors=(Sector(0, 1), Sector(1, 1), Sector(2, 1)))

# Manually construct number operator
import numpy as np
N_data = {}
for sector in idx.sectors:
    charge = sector.charge
    dim = sector.dim
    # Diagonal matrix with charge values
    N_data[(charge, charge)] = np.eye(dim) * charge

from nicole import Tensor
N = Tensor(indices=(idx, idx.flip()), itags=("out", "in"), data=N_data)

print("Number operator:")
for key, block in N.data.items():
    print(f"  Block {key}: {np.diag(block) if block.shape[0] == block.shape[1] else block}")
```

## Ladder Operators

```python
# Creation and annihilation operators for bosons
# a†|n⟩ = √(n+1)|n+1⟩
# a|n⟩ = √n|n-1⟩

group = U1Group()
n_max = 3
idx = Index(Direction.OUT, group, sectors=tuple(Sector(n, 1) for n in range(n_max + 1)))

# Creation operator a†
a_dag_data = {}
for n in range(n_max):
    # Connects |n⟩ to |n+1⟩
    a_dag_data[(n + 1, n)] = np.array([[np.sqrt(n + 1)]])

a_dag = Tensor(indices=(idx, idx.flip()), itags=("out", "in"), data=a_dag_data)

print(f"Creation operator has {len(a_dag.data)} blocks")

# Annihilation operator a
a_data = {}
for n in range(1, n_max + 1):
    # Connects |n⟩ to |n-1⟩
    a_data[(n - 1, n)] = np.array([[np.sqrt(n)]])

a = Tensor(indices=(idx, idx.flip()), itags=("out", "in"), data=a_data)

print(f"Annihilation operator has {len(a.data)} blocks")
```

## Spin Operators

```python
# Sz operator for spin-1/2
# |↓⟩ has Sz = -1/2, |↑⟩ has Sz = +1/2
# Using units where 2*Sz is an integer

group = U1Group()
idx_spin = Index(Direction.OUT, group, sectors=(Sector(-1, 1), Sector(1, 1)))

# Sz is diagonal
Sz_data = {
    (-1, -1): np.array([[-0.5]]),  # |↓⟩
    (1, 1): np.array([[0.5]]),     # |↑⟩
}

Sz = Tensor(indices=(idx_spin, idx_spin.flip()), itags=("out", "in"), data=Sz_data)
print("Sz operator blocks:", list(Sz.data.keys()))
```

## See Also

- API Reference: [identity](../../api/creation/identity.md)
- API Reference: [isometry](../../api/creation/isometry.md)
- Next: [Performance Tips](performance.md)
