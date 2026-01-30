# API Reference

Welcome to the Nicole API Reference. This documentation is organized by functionality for quick access.

## Core Classes

The fundamental building blocks:

| Class | Description |
|-------|-------------|
| [Tensor](core/tensor.md) | Block-sparse tensor with symmetry |
| [Index](core/index-class.md) | Tensor leg with charge structure |
| [Sector](core/sector.md) | Charge-dimension pair |
| [Direction](core/direction.md) | Index orientation (IN/OUT) |

## Creating Tensors

Functions to create new tensors:

| Function | Description |
|----------|-------------|
| [zeros](creation/zeros.md) | Zero-filled tensor |
| [random](creation/random.md) | Random-filled tensor |
| [identity](creation/identity.md) | 2-leg identity tensor |
| [isometry](creation/isometry.md) | 2-to-1 fusion isometry |
| [isometry_n](creation/isometry_n.md) | N-to-1 fusion isometry |

## Manipulation

Transform and rearrange tensors:

| Function | Description |
|----------|-------------|
| [conj](manipulation/conjugate.md) | Conjugate + flip directions |
| [permute](manipulation/permute.md) | Permute axes |
| [transpose](manipulation/transpose.md) | Transpose axes |
| [retag](manipulation/retag.md) | Change index tags |
| [subsector](manipulation/subsector.md) | Extract block subset |
| [merge_axes](manipulation/merge_axes.md) | Merge multiple axes into one |

## Arithmetic

Mathematical operations:

| Topic | Description |
|-------|-------------|
| [Basic Operations](arithmetic/addition.md) | +, -, *, /, negation |
| [oplus](arithmetic/oplus.md) | Direct sum |
| [diag](arithmetic/diag.md) | Create diagonal tensor |
| [inv](arithmetic/inv.md) | Matrix inversion |

## Contraction

Contract and trace tensors:

| Function | Description |
|----------|-------------|
| [contract](contraction/contract.md) | General tensor contraction |
| [trace](contraction/trace.md) | Trace over index pairs |

## Decomposition

SVD and related operations:

| Function | Description |
|----------|-------------|
| [decomp](decomposition/decomp.md) | High-level decomposition |
| [svd](decomposition/svd.md) | Low-level SVD |

## Symmetry Groups

Define and use symmetries:

| Group | Description |
|-------|-------------|
| [Overview](symmetry/overview.md) | Symmetry system introduction |
| [U1Group](symmetry/u1-group.md) | Integer charge symmetry |
| [Z2Group](symmetry/z2-group.md) | Binary symmetry |
| [ProductGroup](symmetry/product-group.md) | Multiple symmetries |

## Utilities

Supporting functionality:

| Topic | Description |
|-------|-------------|
| [Display](utilities/display.md) | Pretty-printing tensors |
| [Blocks](utilities/blocks.md) | Block structure utilities |
| [load_space](utilities/load_space.md) | Load physical spaces and operators |

## Usage Patterns

For practical examples and complete working code, see:

- [Examples: Basic Usage](../examples/basic/first-tensor.md)
- [Examples: Symmetries](../examples/symmetries/u1-examples.md)
- [Examples: Operations](../examples/operations/contraction-examples.md)
- [Examples: Advanced](../examples/advanced/custom-operators.md)

## Quick Links by Task

### I want to...

**Create a tensor**
→ [zeros](creation/zeros.md), [random](creation/random.md), [identity](creation/identity.md)

**Contract tensors**
→ [contract](contraction/contract.md), [trace](contraction/trace.md)

**Decompose a tensor**
→ [decomp](decomposition/decomp.md), [svd](decomposition/svd.md)

**Merge tensor axes**
→ [merge_axes](manipulation/merge_axes.md), [isometry_n](creation/isometry_n.md)

**Use multiple symmetries**
→ [ProductGroup](symmetry/product-group.md)

**Build quantum operators**
→ [load_space](utilities/load_space.md)

**See working examples**
→ [Examples](../examples/index.md)

## API Design

Nicole follows these principles:

- **Functional operations** return new tensors (e.g., `conj()`)
- **In-place methods** modify existing tensors (e.g., `Tensor.conj()`)
- **Charge conservation** enforced automatically
- **NumPy-style** API for familiarity

## See Also

- [Getting Started](../getting-started.md): Tutorial introduction
- [Examples](../examples/index.md): Practical code examples
- [Tutorials](../tutorials/index.md): In-depth guides
