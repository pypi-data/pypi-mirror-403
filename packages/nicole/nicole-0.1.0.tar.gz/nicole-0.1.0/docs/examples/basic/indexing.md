# Indexing and Block Access

Access and manipulate tensor blocks and indices.

## Accessing Blocks

```python
from nicole import Tensor, Index, Sector, Direction, U1Group

group = U1Group()
idx = Index(Direction.OUT, group, sectors=(Sector(0, 2), Sector(1, 1), Sector(-1, 1)))
T = Tensor.random([idx, idx.flip()], itags=["i", "j"], seed=42)

# Display tensor to see block structure
print(T)

# Access blocks by integer index (1-based, matching display)
first_block = T.block(1)
print(f"First block shape: {first_block.shape}")

# Get block key (charges)
key_1 = T.key(1)
print(f"First block charges: {key_1}")

# Access blocks directly via data dictionary
if (0, 0) in T.data:
    block_00 = T.data[(0, 0)]
    print(f"Block (0,0) shape: {block_00.shape}")
```

## Iterating Over Blocks

```python
# Method 1: Using sorted_keys property
for key in T.sorted_keys:
    block = T.data[key]
    print(f"Block {key}: shape {block.shape}, norm {np.linalg.norm(block):.4f}")

# Method 2: Using integer indices
for i in range(1, len(T.data) + 1):
    key = T.key(i)
    block = T.block(i)
    print(f"Block {i} has charges {key}")

# Method 3: Direct dictionary iteration
for key, block in T.data.items():
    print(f"Charges {key}: {block.shape}")
```

## Extracting Block Subsets

```python
from nicole import subsector

# Get a single block (using integer)
T_single = subsector(T, 1)
print(f"Single block: {len(T_single.data)}")

# Get multiple blocks (using list)
T_sub = subsector(T, [1, 2])
print(f"Original blocks: {len(T.data)}")
print(f"Subset blocks: {len(T_sub.data)}")

# Note: subsector automatically removes unused sectors from indices

# Extract specific charge sectors
# Find blocks with positive charges only
positive_blocks = []
for i in range(1, len(T.data) + 1):
    key = T.key(i)
    if all(q >= 0 for q in key):
        positive_blocks.append(i)

if positive_blocks:
    T_positive = subsector(T, positive_blocks)
    print(f"Positive charge blocks: {len(T_positive.data)}")
```

## Index Properties

```python
# Get index information
idx = T.indices[0]
print(f"Direction: {idx.direction}")
print(f"Group: {idx.group.name}")
print(f"Number of sectors: {len(idx.sectors)}")
print(f"Total dimension: {idx.dim}")

# List all sectors
for sector in idx.sectors:
    print(f"Charge {sector.charge}: dimension {sector.dim}")

# Get charges and dimensions
charges = idx.charges()
dim_map = idx.sector_dim_map()
print(f"Charges: {charges}")
print(f"Dimension map: {dim_map}")
```

## Modifying Index Tags

```python
# Change tags to make contractions clearer
T = Tensor.random([idx, idx.flip(), idx], itags=["i", "j", "k"], seed=99)
print(f"Original tags: {T.itags}")

# Retag by name
T.retag(i="left", k="right")
print(f"After retag by name: {T.itags}")

# Retag all at once
T.retag(["a", "b", "c"])
print(f"After retag all: {T.itags}")
```

## Flipping and Dualizing Indices

```python
# Flip: reverse direction only
idx_out = Index(Direction.OUT, group, sectors=(Sector(1, 2),))
idx_in = idx_out.flip()

print(f"Original: {idx_out.direction}")  # OUT
print(f"Flipped: {idx_in.direction}")    # IN
print(f"Charges unchanged: {idx_out.sectors == idx_in.sectors}")

# Dual: reverse direction AND conjugate charges
idx_dual = idx_out.dual()
print(f"Dual direction: {idx_dual.direction}")  # IN
# For U(1), charges are negated

# Check sectors
print("Original sectors:")
for s in idx_out.sectors:
    print(f"  Charge {s.charge}, dim {s.dim}")

print("Dual sectors:")
for s in idx_dual.sectors:
    print(f"  Charge {s.charge}, dim {s.dim}")
```

## Inserting Trivial Indices

```python
# Add a trivial index (neutral charge, dimension 1)
T = Tensor.random([idx, idx.flip()], itags=["i", "j"], seed=7)
print(f"Before: {len(T.indices)} indices")

T.insert_index(position=1, tag="trivial")
print(f"After: {len(T.indices)} indices")
print(f"New tags: {T.itags}")
```

## Block Memory Usage

```python
# Check memory usage per block
print("Block memory usage:")
for i in range(1, len(T.data) + 1):
    key = T.key(i)
    block = T.block(i)
    mem_bytes = block.nbytes
    mem_kb = mem_bytes / 1024
    print(f"Block {i} {key}: {block.shape} -> {mem_bytes} B ({mem_kb:.2f} KB)")

# Total memory
total_bytes = sum(block.nbytes for block in T.data.values())
print(f"\nTotal block memory: {total_bytes} B ({total_bytes/1024:.2f} KB)")
```

## See Also

- API Reference: [Tensor](../../api/core/tensor.md)
- API Reference: [Index](../../api/core/index-class.md)
- API Reference: [subsector](../../api/manipulation/subsector.md)
- Previous: [Arithmetic](arithmetic.md)
- Next: [Symmetry Examples](../symmetries/u1-examples.md)
