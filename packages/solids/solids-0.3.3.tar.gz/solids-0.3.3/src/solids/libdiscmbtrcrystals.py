import numpy as np
from dscribe.descriptors import MBTR
# ------------------------------------------------------------------------------------------
def build_mbtr(atoms_list):
    """This function builds an MBTR descriptor object configured for a set of structures.
    in: 
        atoms_list (list); list of Atoms objects to analyze.
    out: 
        mbtr (MBTR object); configured MBTR descriptor.
    """
    species = sorted(set(
        sym for atoms in atoms_list for sym in atoms.get_chemical_symbols()
    ))

    mbtr = MBTR(
        species=species,
        geometry={"function": "distance"},
        weighting={"function": "inverse_square", "r_cut": 10, "threshold": 1e-3},
        grid={"min": 0, "max": 10, "sigma": 1e-3, "n": 100},
        periodic=True,
        # normalization="none",
        normalization="l2",
        sparse=False,
        dtype="float64",
    )
    return mbtr

# ------------------------------------------------------------------------------------------
def descriptor_comparison_calculated(atoms_list_in, tolerance, nproc=2):
    """This function compares a list of Atoms objects against each other using MBTR similarity.
    It retains only those that are sufficiently different based on a similarity threshold.
    in:
        atoms_list_in (list); list of Atoms objects to compare.
        tolerance (float); similarity threshold above which structures are considered too similar.
        nproc (int); number of processors to use for descriptor calculation.
    out:
        atoms_list_out (list); list of Atoms objects from atoms_list_in that are sufficiently different.
    """
    mbtr = build_mbtr(atoms_list_in)
    descriptors = mbtr.create(atoms_list_in, n_jobs=nproc)
    atoms_list_out = []
    descriptors_out = []
    disc_count = 0
    for i, desc_i in enumerate(descriptors):
        is_unique = True
        for desc_j in descriptors_out:
            # Use L1-based similarity as provided:
            # S_ij = 1 / (1 + (1/d) * sum_l |X_i^l - X_j^l|)
            d = desc_i.size
            l1 = np.sum(np.abs(desc_i - desc_j))
            similarity = 1.0 / (1.0 + (1.0 / d) * l1)
            if similarity >= tolerance:
                print(f"{atoms_list_in[i].info['i']} removed, too similar to a lower-energy structure, similarity = {similarity:.5f}")
                disc_count += 1
                is_unique = False
                break
        if is_unique:
            atoms_list_out.append(atoms_list_in[i])
            descriptors_out.append(desc_i)

    print(f"\n{disc_count} structures removed by similarity in generation comparison")
    return atoms_list_out

# ------------------------------------------------------------------------------------------
def descriptor_comparison_calculated_vs_pool(atoms_calculated, atoms_pool, tolerance, nproc=2):
    """Compares generation structures against the pool of known structures using MBTR similarity.
    in:
        atoms_calculated (list); list of Atoms objects from the current generation to be compared.
        atoms_pool (list); list of Atoms objects from the pool of known structures.
        tolerance (float); similarity threshold above which structures are considered too similar.
        nproc (int); number of processors to use for descriptor calculation.
    out:
        different_calc (list); list of Atoms objects from atoms_calculated that are sufficiently different.
    """
    mbtr = build_mbtr(atoms_calculated + atoms_pool)
    descr_calc = mbtr.create(atoms_calculated, n_jobs=nproc)
    descr_pool = mbtr.create(atoms_pool, n_jobs=nproc)
    disc_count = 0
    different_calc = []
    for atoms_i, desc_i in zip(atoms_calculated, descr_calc):
        is_unique = True
        for j, desc_j in enumerate(descr_pool):
            d = desc_i.size
            l1 = np.sum(np.abs(desc_i - desc_j))
            similarity = 1.0 / (1.0 + (1.0 / d) * l1)
            if similarity >= tolerance:
                print(f"{atoms_i.info['i']} removed, too similar to {atoms_pool[j].info['i']}, similarity = {similarity:.5f}")
                disc_count += 1
                is_unique = False
                break
        if is_unique:
            different_calc.append(atoms_i)
    if different_calc:
        print(f"\n{disc_count} structures removed by similarity in Gen vs Pool comparison")
    else:
        print("\nZero structures removed by similarity in Gen vs Pool comparison")
    return different_calc

# ------------------------------------------------------------------------------------------
def remove_similar_by_energy(atoms_list, threshold=1e-3):
    """
    Removes Atoms objects whose energy difference is below a given threshold.
    Retains the first occurrence, removes subsequent ones, and prints which were removed and why.
    Args:
        atoms_list (list): List of Atoms objects with energy stored in info['energy'].
        threshold (float): Maximum allowed energy difference to consider as duplicate.
    Returns:
        list: Filtered list of Atoms objects.
    """
    kept = []
    energies = []
    removed_count = 0
    for i, atoms_i in enumerate(atoms_list):
        energy_i = atoms_i.info.get('e', None)
        if energy_i is None:
            print(f"Warning: Atoms object at index {i} missing energy in info. Skipping.")
            continue
        is_unique = True
        for j, energy_j in enumerate(energies):
            if abs(energy_i - energy_j) < threshold:
                print(f"Structure {atoms_i.info.get('i', i)} removed: |E({energy_i}) - E({energy_j})| < {threshold}")
                is_unique = False
                removed_count += 1
                break
        if is_unique:
            kept.append(atoms_i)
            energies.append(energy_i)
    print(f"\n{removed_count} structures removed by energy similarity.")
    return kept