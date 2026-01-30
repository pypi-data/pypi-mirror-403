"""Infinite Time-Evolving Block Decimation (iTEBD) for spin chain (Heisenberg model).

This module implements the iTEBD algorithm in Vidal's Γ-Λ canonical form for
computing the ground state energy of an infinite Heisenberg spin chain.
"""

import numpy as np
from typing import Tuple, List, Dict
from nicole import load_space, contract, identity, conj, decomp
from nicole.operators import inv, diag, permute
from nicole.index import Direction, Index, Sector
from nicole.tensor import Tensor
import time

# Try to import scipy, fall back to numpy if not available
try:
    from scipy.linalg import expm as matrix_expm
except ImportError:
    # Fallback: use numpy's implementation or series expansion
    def matrix_expm(A):
        """Matrix exponential using eigenvalue decomposition."""
        # For Hermitian matrices, we can use eigendecomposition
        eigvals, eigvecs = np.linalg.eigh(A)
        return eigvecs @ np.diag(np.exp(eigvals)) @ eigvecs.T.conj()


def disptime(msg: str) -> None:
    """Display message with timestamp."""
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")


def build_gate(Op: Dict[str, Tensor], Spc: Index, J: float, tau: float) -> Tensor:
    """Build two-site Heisenberg gate U = exp(-tau * H_bond).
    
    Parameters
    ----------
    Op : dict
        Dictionary of spin operators from load_space
    Spc : Index
        Physical space index
    J : float
        Coupling constant
    tau : float
        Imaginary time step
    
    Returns
    -------
    Tensor
        Two-site gate with itags ("sA", "sB", "sA", "sB")
    """
    # Step 1: Construct single-site spin operator S = Sp + Sm + Sz
    # Insert index for Sz to match Sp and Sm structure (if not already done)
    if len(Op["Sz"].indices) == 2:
        Op["Sz"].insert_index(2, direction=Direction.OUT)
    
    S = Op["Sp"] + Op["Sm"] + Op["Sz"]
    
    # Contract auxiliary index with conjugate: H_site = S · S†
    # S has 3 indices: (phys-IN, phys-OUT, aux-OUT)
    # conj(S) has: (phys-OUT, phys-IN, aux-IN) after conjugation
    # Result after contraction on aux: (phys-IN-A, phys-OUT-A, phys-IN-B, phys-OUT-B)
    # Note: The naming "output/input" refers to the role after gate application, not direction
    # "output" = new state (direction IN), "input" = old state (direction OUT)
    H_site = contract(S, conj(S), axes=(2, 2), perm=[0,1,3,2])
    
    # Step 2: Create identity operator with auxiliary index
    # This ensures all charge blocks are present
    I = identity(Spc)
    I.insert_index(2, direction=Direction.OUT)
    
    # Create Id ⊗ Id term
    Id_Id = contract(I, conj(I), axes=(2, 2), perm=[0,1,3,2])
    
    # Step 3: Add Id ⊗ Id * 0 to ensure all blocks present
    H_bond = J * H_site + 0.0 * Id_Id
    
    # Permute H_bond from (phys-IN-A, phys-OUT-A, phys-IN-B, phys-OUT-B) 
    # to (phys-IN-A, phys-IN-B, phys-OUT-A, phys-OUT-B)
    # This groups input and output states together
    H_bond_perm = permute(H_bond.copy(), [0, 2, 1, 3])
    
    # Step 4: Use merge_axes to properly combine indices into a matrix structure
    from nicole.operators import merge_axes
    
    # Merge the input indices (sA-IN, sB-IN) -> merged-IN
    H_temp, iso_in = merge_axes(H_bond_perm, [0, 1])
    # H_temp now has indices: (merged-IN, phys-OUT-A, phys-OUT-B)
    # iso_in is the isometry to unmerge: (sA-IN, sB-IN, merged-IN)
    
    # Merge the output indices (sA-OUT, sB-OUT) -> merged-OUT  
    H_matrix, iso_out = merge_axes(H_temp, [1, 2])
    # H_matrix is now a proper 2-index tensor: (merged-IN, merged-OUT)
    # iso_out is the isometry to unmerge: (sA-OUT, sB-OUT, merged-OUT)
    
    # Exponentiate each charge block
    U_matrix_data = {}
    for key, H_block in H_matrix.data.items():
        # H_block is a 2D matrix for this charge sector
        U_mat = matrix_expm(-tau * H_block)
        U_matrix_data[key] = U_mat
    
    # Create exponentiated matrix tensor
    U_matrix = Tensor(
        indices=H_matrix.indices,
        itags=H_matrix.itags,
        data=U_matrix_data,
        dtype=H_matrix.dtype
    )
    
    # Unmerge back to 4-index structure using the isometries
    # First unmerge the output index: U_matrix * iso_out
    U_temp = contract(U_matrix, iso_out, axes=(1, 2))
    # Result: (merged-IN, sA-OUT, sB-OUT)
    
    # Then unmerge the input index: iso_in * U_temp
    U = contract(iso_in, U_temp, axes=(2, 0))
    # Result: (sA-IN, sB-IN, sA-OUT, sB-OUT)
    
    # Retag to have matching itags for contraction
    U.retag(("sA", "sB", "sA", "sB"))
    
    return U


def compute_energy(Gamma_A: Tensor, Lambda_A: Tensor, Gamma_B: Tensor, 
                   Lambda_B: Tensor, H_bond: Tensor) -> float:
    """Compute energy expectation value for A-B bond.
    
    Parameters
    ----------
    Gamma_A, Gamma_B : Tensor
        Gamma tensors
    Lambda_A, Lambda_B : Tensor
        Lambda matrices (diagonal)
    H_bond : Tensor
        Two-site Hamiltonian operator
    
    Returns
    -------
    float
        Energy per site
    """
    # Form state Ψ = Λ[B] - Γ[A] - Λ[A] - Γ[B] - Λ[B]
    # Use explicit axes (same pattern as update_bond)
    Psi = contract(Lambda_B, Gamma_A, axes=(1, 0))
    Psi = contract(Psi, Lambda_A, axes=(1, 0))
    Psi = contract(Psi, Gamma_B, axes=(2, 0))
    Psi = contract(Psi, Lambda_B, axes=(2, 0))
    # Result: (bondB-IN-left, sA-IN, sB-IN, bondB-IN-right)
    
    # Compute <Ψ|H|Ψ>
    # H_bond: (sA-IN, sA-OUT, sB-IN, sB-OUT)
    # Psi: (bondB-left, sA-IN, sB-IN, bondB-right)
    # First: H|Ψ> - contract H's output indices with Psi's physical
    H_Psi = contract(H_bond, Psi, axes=([2, 3], [1, 2]))
    # Result: (sA-IN-new, sB-IN-new, bondB-left, bondB-right)
    
    # Then: <Ψ|H|Ψ> - contract all indices
    # conj(Psi): (bondB-left, sA-OUT, sB-OUT, bondB-right)
    # H_Psi: (sA-IN, sB-IN, bondB-left, bondB-right)
    E_num_tensor = contract(conj(Psi), H_Psi, axes=([0, 1, 2, 3], [2, 0, 1, 3]))
    E_num = E_num_tensor.item()
    
    # Compute <Ψ|Ψ>
    norm_sq_tensor = contract(conj(Psi), Psi, axes=([0, 1, 2, 3], [0, 1, 2, 3]))
    norm_sq = norm_sq_tensor.item()
    
    # Energy per bond = energy per site for 2-site unit cell
    E_per_site = E_num / norm_sq
    
    return E_per_site


def update_bond(Gamma_left: Tensor, Lambda_mid: Tensor, Gamma_right: Tensor,
                Lambda_left: Tensor, Lambda_right: Tensor, U: Tensor,
                Nkeep: int) -> Tuple[Tensor, Tensor, Tensor]:
    """Update a single bond using iTEBD step.
    
    Parameters
    ----------
    Gamma_left, Gamma_right : Tensor
        Gamma tensors on left and right
    Lambda_mid : Tensor
        Lambda matrix in the middle (to be updated)
    Lambda_left, Lambda_right : Tensor
        Lambda matrices on far left and right (environment)
    U : Tensor
        Two-site gate
    Nkeep : int
        Maximum bond dimension
    
    Returns
    -------
    tuple
        (Gamma_left_new, Lambda_mid_new, Gamma_right_new)
    """
    # Form Θ with environment: Λ_left - Γ_left - Λ_mid - Γ_right - Λ_right
    # Direction conventions:
    # Lambda_left: (bondB-IN[0], bondB-IN[1])
    # Gamma_left: (bondB-OUT[0], bondA-OUT[1], sA-IN[2])
    # Lambda_mid: (bondA-IN[0], bondA-IN[1])
    # Gamma_right: (bondA-OUT[0], bondB-OUT[1], sB-IN[2])
    # Lambda_right: (bondB-IN[0], bondB-IN[1])
    
    # Use explicit axes for contractions
    from nicole.operators import permute
    
    # Step 1: Λ_left[i,j] * Γ_left[j,k,s]  - contract on index 1 of Lambda with index 0 of Gamma
    Theta = contract(Lambda_left, Gamma_left, axes=(1, 0))
    # Result: (bondB-IN, bondA-OUT, sA-IN)
    
    # Step 2: Theta[i,j,s] * Λ_mid[j,k] - contract on index 1 of Theta with index 0 of Lambda_mid
    Theta = contract(Theta, Lambda_mid, axes=(1, 0))
    # Result: (bondB-IN, sA-IN, bondA-IN)
    
    # Step 3: Theta[i,s_a,j] * Γ_right[j,k,s_b] - contract on index 2 of Theta with index 0 of Gamma
    Theta = contract(Theta, Gamma_right, axes=(2, 0))
    # Result: (bondB-IN, sA-IN, bondB-OUT, sB-IN)
    
    # Step 4: Theta[i,s_a,j,s_b] * Λ_right[j,k] - contract on index 2 of Theta with index 0 of Lambda
    Theta = contract(Theta, Lambda_right, axes=(2, 0))
    # Result: (bondB-IN-left, sA-IN, sB-IN, bondB-IN-right)
    
    # Apply gate: Θ' = U · Θ
    # U: (sA-IN, sB-IN, sA-OUT, sB-OUT)
    # Theta: (bondB-IN-left, sA-IN, sB-IN, bondB-IN-right)
    # Contract U's output indices (2,3) with Theta's physical indices (1,2)
    Theta_prime = contract(U, Theta, axes=([2, 3], [1, 2]))
    # Result: (sA-IN-new, sB-IN-new, bondB-IN-left, bondB-IN-right)
    
    # Permute to (bondB-left, sA-new, sB-new, bondB-right) for SVD
    Theta_prime = permute(Theta_prime, [2, 0, 1, 3])
    
    # SVD: decompose along (left-bond, phys-A) vs (phys-B, right-bond)
    U_svd, S, Vh = decomp(Theta_prime, axes=[0, 1], mode="SVD",
        trunc={"nkeep": Nkeep, "thresh": 1e-14})
    
    # Extract new Gamma tensors by dividing out Lambda
    Lambda_left_inv = inv(Lambda_left)
    Lambda_right_inv = inv(Lambda_right)
    
    # Γ_left_new = Λ_left^(-1) · U_svd
    # Lambda_left_inv: (bondB-OUT, bondB-OUT) after inv
    # U_svd: (bondB-IN, sA-IN, bond-new-OUT)
    # Contract on bondB: axes (1, 0)
    Gamma_left_new = contract(Lambda_left_inv, U_svd, axes=(1, 0), perm=[0,2,1])
    # Result: (bondB-OUT, bond-new-OUT, sA-IN)
    
    # Γ_right_new = Vh · Λ_right^(-1)
    # Vh: (bond-new-IN, sB-IN, bondB-IN)
    # Lambda_right_inv: (bondB-OUT, bondB-OUT)
    # Contract on bondB: axes (2, 0)
    Gamma_right_new = contract(Vh, Lambda_right_inv, axes=(2, 0), perm=[0,2,1])
    # Result: (bond-new-IN, bondB-OUT, sB-IN)
    
    # Update Lambda with new singular values S
    Lambda_mid_new = S

    Gamma_left_new *= 1/Gamma_left_new.norm()
    Gamma_right_new *= 1/Gamma_right_new.norm()
    Lambda_mid_new *= 1/Lambda_mid_new.norm()
    
    return Gamma_left_new, Lambda_mid_new, Gamma_right_new


def inf_tebd_spin(
    dt_list: List[float] = [0.1, 0.01, 0.001, 0.0001],
    Nkeep: int = 100,
    J: float = 1.0,
    spin: float = 0.5,
    tol: float = 1e-10,
    max_iter: int = 1000,
    verbose: bool = True
) -> Tuple[float, np.ndarray, float]:
    """Run iTEBD for infinite spin chain (Heisenberg model).
    
    Parameters
    ----------
    dt_list : list of float, optional
        List of imaginary time steps for multi-scale evolution (default: [0.1, 0.01, 0.001, 0.0001])
    Nkeep : int, optional
        Maximum bond dimension (default: 100)
    J : float, optional
        Spin-spin coupling constant (default: 1.0)
    spin : float, optional
        Total spin quantum number for each site (default: 0.5 for spin-1/2)
    tol : float, optional
        Convergence tolerance for energy (default: 1e-10)
    max_iter : int, optional
        Maximum iterations per time step (default: 1000)
    verbose : bool, optional
        Print progress messages (default: True)
    
    Returns
    -------
    E_final : float
        Final ground state energy per site
    E_history : np.ndarray
        Energy history during evolution
    E_exact : float
        Exact ground state energy per site for infinite chain (spin-1/2 only)
    
    Notes
    -----
    Implements iTEBD in Vidal's Γ-Λ canonical form:
        ...Γ[A]-Λ[A]-Γ[B]-Λ[B]-Γ[A]-Λ[A]-Γ[B]-Λ[B]-...
    
    Ground state found via imaginary time evolution with exp(-τH) gates.
    
    For spin-1/2, exact result:
        E_exact = 1/4 - ln(2) ≈ -0.443147
    
    Examples
    --------
    >>> # Run with default parameters
    >>> E_final, E_history, E_exact = inf_tebd_spin()
    
    >>> # Larger bond dimension
    >>> E_final, E_history, E_exact = inf_tebd_spin(Nkeep=200)
    
    >>> # Spin-1 chain
    >>> E_final, E_history, E_exact = inf_tebd_spin(spin=1.0)
    """
    if verbose:
        disptime(f"Starting iTEBD: spin={spin}, J={J}, Nkeep={Nkeep}")
        disptime(f"Time steps: {dt_list}")
    
    # Get local spin space and operators
    Spc, Op = load_space("Spin", "U1", {"J": spin})
    
    # Build Hamiltonian operator (without time step)
    # This will be used for energy calculation
    # Insert index for Sz to match Sp and Sm structure
    Op["Sz"].insert_index(2, direction=Direction.OUT)
    S = Op["Sp"] + Op["Sm"] + Op["Sz"]
    H_bond = contract(S, conj(S), axes=(2, 2), perm=[0,3,1,2])
    H_bond = J * H_bond
    H_bond.retag(("sA", "sB", "sA", "sB"))
    
    # Initialize Γ-Λ state
    # Start with small bond dimension
    init_chi = 1
    group = Spc.group
    
    # Create bond indices with neutral charge and small dimension
    # Convention: Lambda matrices have all IN directions
    #             Gamma tensors have all OUT directions except physical (which is IN)
    bond_sectors = [Sector(charge=-1, dim=init_chi), Sector(charge=1, dim=init_chi), Sector(charge=0, dim=init_chi)]
    bond_index_in = Index(direction=Direction.IN, group=group, sectors=tuple(bond_sectors))
    bond_index_out = Index(direction=Direction.OUT, group=group, sectors=tuple(bond_sectors))
    
    # Initialize Gamma tensors with random values
    # Γ[A]: (bondB-OUT, bondA-OUT, sA-IN)
    Gamma_A = Tensor.random(
        [bond_index_out, bond_index_out, Spc],
        itags=["bondB", "bondA", "sA"],
        seed=42
    )
    
    # Γ[B]: (bondA-OUT, bondB-OUT, sB-IN)
    Gamma_B = Tensor.random(
        [bond_index_out, bond_index_out, Spc],
        itags=["bondA", "bondB", "sB"],
        seed=43
    )
    
    # Initialize Lambda matrices with uniform values (all IN directions)
    # Create diagonal tensors with uniform singular values (normalized)
    lambda_val = 1.0 / np.sqrt(init_chi)
    
    Lambda_A_data = {
        (0, 0): np.eye(init_chi) * lambda_val,
        (1, -1): np.eye(init_chi) * lambda_val,
        (-1, 1): np.eye(init_chi) * lambda_val,
    }
    Lambda_A = Tensor(
        indices=(bond_index_in, bond_index_in),
        itags=("bondA", "bondA"),
        data=Lambda_A_data,
        dtype=np.float64
    )
    
    Lambda_B_data = {
        (0, 0): np.eye(init_chi) * lambda_val,
        (1, -1): np.eye(init_chi) * lambda_val,
        (-1, 1): np.eye(init_chi) * lambda_val,
    }
    Lambda_B = Tensor(
        indices=(bond_index_in, bond_index_in),
        itags=("bondB", "bondB"),
        data=Lambda_B_data,
        dtype=np.float64
    )
    
    # Track energy history
    E_history = []
    
    # Multi-scale time evolution
    for dt in dt_list:
        if verbose:
            disptime(f"Time step dt = {dt}")
        
        # Build gate for this time step
        U_AB = build_gate(Op, Spc, J, dt)
        U_BA = U_AB.copy()
        U_BA.retag(["sB", "sA", "sB", "sA"])
        
        E_old = 0.0
        converged = False
        
        for it in range(max_iter):
            # Update A-B bond
            Gamma_A, Lambda_A, Gamma_B = update_bond(
                Gamma_A, Lambda_A, Gamma_B, Lambda_B, Lambda_B, U_AB, Nkeep
            )

            Gamma_A.retag(["bondB", "bondA", "sA"])
            Gamma_B.retag(["bondA", "bondB", "sB"])
            Lambda_A.retag(["bondA", "bondA"])
            
            # Update B-A bond
            Gamma_B, Lambda_B, Gamma_A = update_bond(
                Gamma_B, Lambda_B, Gamma_A, Lambda_A, Lambda_A, U_BA, Nkeep
            )

            Gamma_B.retag(["bondA", "bondB", "sB"])
            Gamma_A.retag(["bondB", "bondA", "sA"])
            Lambda_B.retag(["bondB", "bondB"])
            
            # Compute energy
            E = compute_energy(Gamma_A, Lambda_A, Gamma_B, Lambda_B, H_bond)
            E_history.append(E)
            
            # Check convergence
            dE = abs(E - E_old)
            if dE < tol:
                if verbose:
                    disptime(f"  Converged at iteration {it+1}: E = {E:.10f}, dE = {dE:.2e}")
                converged = True
                break
            
            E_old = E
            
            # Print progress
            if verbose and (it + 1) % 100 == 0:
                bond_dim_A = Lambda_A.indices[0].dim
                bond_dim_B = Lambda_B.indices[0].dim
                disptime(f"  Iter {it+1}/{max_iter}: E = {E:.10f}, dE = {dE:.2e}, χ = ({bond_dim_A}, {bond_dim_B})")
        
        if not converged and verbose:
            disptime(f"  Warning: Did not converge after {max_iter} iterations (dE = {dE:.2e})")
    
    # Final energy
    E_final = E_history[-1] if E_history else 0.0
    
    # Exact result for spin-1/2
    if spin == 0.5:
        E_exact = 0.25 - np.log(2)
    else:
        E_exact = np.nan
    
    if verbose:
        if not np.isnan(E_exact):
            disptime(f"\nExact ground state energy per site: {E_exact:.10f}")
        disptime(f"Final iTEBD estimate: {E_final:.10f}")
        if not np.isnan(E_exact):
            error = abs(E_final - E_exact)
            disptime(f"Error: {error:.2e}")
    
    return E_final, np.array(E_history), E_exact


def main():
    """Command-line interface for iTEBD."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run iTEBD for Heisenberg spin chain")
    parser.add_argument("--Nkeep", type=int, default=100, help="Maximum bond dimension")
    parser.add_argument("--J", type=float, default=1.0, help="Coupling constant")
    parser.add_argument("--spin", type=float, default=0.5, help="Spin value (0.5, 1.0, etc.)")
    parser.add_argument("--tol", type=float, default=1e-10, help="Convergence tolerance")
    parser.add_argument("--max_iter", type=int, default=1000, help="Max iterations per time step")
    parser.add_argument("--quiet", action="store_true", help="Suppress output")
    
    args = parser.parse_args()
    
    E_final, E_history, E_exact = inf_tebd_spin(
        Nkeep=args.Nkeep,
        J=args.J,
        spin=args.spin,
        tol=args.tol,
        max_iter=args.max_iter,
        verbose=not args.quiet
    )
    
    return E_final, E_history, E_exact


if __name__ == "__main__":
    main()
