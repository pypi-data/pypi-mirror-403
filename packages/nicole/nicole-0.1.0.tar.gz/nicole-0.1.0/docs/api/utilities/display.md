# Display Utilities

Pretty-printing for symmetry-aware tensors.

## Description

Nicole tensors have built-in display functionality accessed via `print(tensor)` or `tensor.show()`.

### Display Format

```
  info:  2x { 3 x 1 }  having 'U1'  Tensor,  { i* j }
  data:  2-D float64 (48 B)    3 => 6 @ norm = 2.34567

     1.  2  2    |  4       [ 0 0 ]     32 B
     2.  1  1    |  1       [ 1 1 ]     8 B
     3.  1  1    |  1       [-1 -1 ]    8 B
```

### Components

- **info**: 
  - `2x` - tensor order (2 indices)
  - `{ 3 x 1 }` - 3 blocks with 1 charge component each
  - `'U1'` - symmetry group name
  - `{ i* j }` - index tags (* marks OUT direction)
- **data**: Dimensionality, dtype, memory, multiplets => states, norm
- **blocks**: Per-block dimensions, charges, memory

## Methods

### print(tensor)

Standard print with line limit (default 10 blocks).

### tensor.show(block_indices=None)

Show specific blocks or all blocks without limit.

## See Also

- [Tensor](../core/tensor.md): Main tensor class
- [Examples: First Tensor](../../examples/basic/first-tensor.md)

## Notes

- Block indices are 1-based in display
- Memory usage shown per block and total
- `*` marks outgoing (OUT) directions
