# U(1) Symmetry Examples

Working with U(1) symmetry (particle number, magnetization).

## Basic U(1) Tensor

```python
from nicole import Tensor, Index, Sector, Direction, U1Group

# U(1) group for particle number conservation
group = U1Group()

# Create index with various charges
idx = Index(
    Direction.OUT,
    group,
    sectors=(
        Sector(charge=0, dim=2),   # vacuum-like states
        Sector(charge=1, dim=1),   # one particle
        Sector(charge=2, dim=1),   # two particles
    )
)

T = Tensor.random([idx, idx.flip()], itags=["i", "j"], seed=42)
print(T)
```

## Charge Operations

```python
# U(1) operations
print(f"Group name: {group.name}")
print(f"Neutral element: {group.neutral}")

# Fusion (addition for U1)
charge1, charge2 = 2, 3
fused = group.fuse(charge1, charge2)
print(f"{charge1} + {charge2} = {fused}")  # 5

# Inverse (negation)
inv = group.inverse(5)
print(f"Inverse of 5: {inv}")  # -5

# Multiple fusion
result = group.fuse(1, 2, -1, 3)
print(f"1 + 2 + (-1) + 3 = {result}")  # 5
```

## Charge Conservation Verification

```python
# Only blocks with total charge = 0 exist
from nicole.blocks import BlockSchema

T = Tensor.random([idx, idx.flip(), idx], itags=["a", "b", "c"], seed=7)

print("Checking charge conservation:")
for key in T.data.keys():
    # key = (charge_a, charge_b, charge_c)
    # a is OUT, b is IN, c is OUT
    total = key[0] - key[1] + key[2]  # OUT - IN + OUT
    conserved = (total == 0)
    print(f"Block {key}: total = {total}, conserved = {conserved}")
```

## Particle Number States

```python
# System with 0, 1, or 2 particles
idx_fock = Index(
    Direction.OUT,
    group,
    sectors=(
        Sector(charge=0, dim=1),  # |0⟩ (vacuum)
        Sector(charge=1, dim=2),  # |1⟩ (two different single-particle states)
        Sector(charge=2, dim=1),  # |2⟩ (two particles)
    )
)

# State represented as density matrix
psi = Tensor.random([idx_fock, idx_fock.flip()], itags=["bra", "ket"], seed=11)
print(f"State has {len(psi.data)} charge sectors")

# Operator that conserves particle number
H = Tensor.random([idx_fock, idx_fock.flip()], itags=["out", "in"], seed=22)
print(f"Hamiltonian has {len(H.data)} blocks")
```

## See Also

- API Reference: [U1Group](../../api/symmetry/u1-group.md)
- Next: [Z2 Examples](z2-examples.md)
- Next: [Product Groups](product-examples.md)
