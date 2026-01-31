from pathlib import Path

def check_poscar_format(poscar_path: Path):
    """
    Checks if the POSCAR file is in VASP 5 format (includes element symbols).
    Raises ValueError if VASP 4 format (missing element symbols) is detected.
    """
    try:
        with open(poscar_path, 'r') as f:
            lines = [l.strip() for l in f.readlines() if l.strip()]
        
        # Basic length check
        if len(lines) < 6:
            # Let pymatgen handle extremely broken files, or pass
            return

        # Check line 6 (0-indexed 5)
        # In VASP 5, this line contains element symbols (e.g., "Al O").
        # In VASP 4, this line contains atom counts (e.g., "4 12").
        line6_parts = lines[5].split()
        
        is_integers = True
        for part in line6_parts:
            if not part.isdigit():
                is_integers = False
                break
        
        if is_integers:
            # If line 6 is all integers, it's likely the atom counts line of a VASP 4 file
            # (unless someone named their elements "1", "2" which is invalid).
            raise ValueError(
                f"The POSCAR file '{poscar_path}' appears to be in VASP 4 format (missing element symbols).\n"
                "Macer requires VASP 5 format which includes the element symbols line before the atom counts.\n"
                "Please add the element symbols to line 6 of your POSCAR file.\n"
                "Example VASP 5 Format:\n"
                "  Al    <-- Element symbols line\n"
                "   4    <-- Atom counts line"
            )

    except FileNotFoundError:
        # File existence should be checked before calling this
        pass
    except ValueError as e:
        raise e
    except Exception:
        # For any other parsing errors, let pymatgen handle it later
        pass
