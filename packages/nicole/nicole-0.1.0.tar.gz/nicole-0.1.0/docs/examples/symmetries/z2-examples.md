# Z(2) Symmetry Examples

Working with Z(2) symmetry (parity, fermion number).

## Basic Z(2) Tensor

```python
from nicole import Tensor, Index, Sector, Direction, Z2Group

# Z(2) group for parity
group = Z2Group()

# Create index with even/odd sectors
idx = Index(
    Direction.OUT,
    group,
    sectors=(
        Sector(charge=0, dim=3),  # even parity (3 states)
        Sector(charge=1, dim=2),  # odd parity (2 states)
    )
)

T = Tensor.random([idx, idx.flip()], itags=["i", "j"], seed=42)
print(T)
```

## Charge Operations

```python
# Z(2) operations
print(f"Group name: {group.name}")
print(f"Neutral element: {group.neutral}")  # 0

# Fusion (XOR for Z2)
print(f"0 ⊕ 0 = {group.fuse(0, 0)}")  # 0 (even + even = even)
print(f"0 ⊕ 1 = {group.fuse(0, 1)}")  # 1 (even + odd = odd)
print(f"1 ⊕ 0 = {group.fuse(1, 0)}")  # 1 (odd + even = odd)
print(f"1 ⊕ 1 = {group.fuse(1, 1)}")  # 0 (odd + odd = even)

# Self-inverse
print(f"Inverse of 0: {group.inverse(0)}")  # 0
print(f"Inverse of 1: {group.inverse(1)}")  # 1
```

## Fermion Parity

```python
# Fermion parity: even = bosonic, odd = fermionic
idx_fermion = Index(
    Direction.OUT,
    group,
    sectors=(
        Sector(charge=0, dim=1),  # 0 or 2 fermions (even)
        Sector(charge=1, dim=2),  # 1 fermion (odd, 2 spin states)
    )
)

# Fermionic operator (must preserve parity)
F = Tensor.random([idx_fermion, idx_fermion.flip()], itags=["out", "in"], seed=99)

# Check blocks
print("Fermion operator blocks:")
for key in F.data.keys():
    parity_in, parity_out = key
    print(f"  {key}: parity_out ⊕ parity_in = {group.fuse(parity_out, parity_in)}")
```

## Spatial Inversion

```python
# States with definite parity under spatial inversion
idx_spatial = Index(
    Direction.OUT,
    group,
    sectors=(
        Sector(charge=0, dim=5),  # symmetric (even parity)
        Sector(charge=1, dim=5),  # antisymmetric (odd parity)
    )
)

# Parity operator (diagonal in parity basis)
P = Tensor.random([idx_spatial, idx_spatial.flip()], itags=["out", "in"], seed=7)
print(f"Parity operator has {len(P.data)} blocks")
```

## Combining Parities

```python
# Multiple fusion
parities = [1, 1, 1]  # Three odd objects
total_parity = group.fuse(*parities)
print(f"Three odd objects: {parities} → parity {total_parity}")  # 1 (odd)

parities2 = [1, 1, 1, 1]  # Four odd objects
total_parity2 = group.fuse(*parities2)
print(f"Four odd objects: {parities2} → parity {total_parity2}")  # 0 (even)
```

## Validation

```python
# Z2 only allows charges 0 or 1
try:
    bad_sector = Sector(charge=2, dim=1)  # Invalid!
    bad_index = Index(Direction.OUT, group, sectors=(bad_sector,))
except ValueError as e:
    print(f"Expected error: {e}")
```

## See Also

- API Reference: [Z2Group](../../api/symmetry/z2-group.md)
- Previous: [U1 Examples](u1-examples.md)
- Next: [Product Groups](product-examples.md)
