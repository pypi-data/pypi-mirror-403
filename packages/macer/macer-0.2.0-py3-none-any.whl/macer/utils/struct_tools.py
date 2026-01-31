from pathlib import Path

def vasp4to5(input_path: str, symbols: str = None, output_path: str = None):
    """
    Convert VASP4 POSCAR to VASP5 by adding element symbols.
    """
    in_file = Path(input_path)
    if not in_file.exists():
        print(f"Error: File '{input_path}' not found.")
        return
    
    if output_path is None:
        output_path = f"{input_path}_v5"

    try:
        with open(in_file, 'r') as f:
            lines = f.readlines()
        
        if len(lines) < 6:
            print("Error: Invalid POSCAR file (too short).")
            return

        # Check if it's already VASP5
        line6 = lines[5].strip().split()
        if not all(p.isdigit() for p in line6):
            print(f"Info: '{input_path}' already appears to have element symbols (VASP5?).")
            # We can still proceed if symbols are provided to override
        
        if symbols is None:
            # Try to guess from the first line (comment)
            guess = lines[0].strip().split()
            print(f"No symbols provided. Guessing from comment line: {' '.join(guess)}")
            symbols = " ".join(guess)
            # Basic validation: symbols should not be digits
            if any(s.isdigit() for s in guess):
                print("Error: Could not guess symbols safely. Please provide them with -s \"El1 El2 ...\"")
                return

        # VASP5 structure:
        # 1. Comment
        # 2. Scale
        # 3-5. Lattice
        # 6. Element Symbols (NEW)
        # 7. Atom counts
        # ...
        
        new_lines = lines[:5]
        new_lines.append(f" {symbols}\n")
        new_lines.extend(lines[5:])
        
        with open(output_path, 'w') as f:
            f.writelines(new_lines)
        
        print(f"Successfully converted VASP4 -> VASP5: {output_path}")
        print(f"Added element line: {symbols}")

    except Exception as e:
        print(f"Error during conversion: {e}")
