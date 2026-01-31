import os
import glob
import sys
import argparse

# ===============================
# PATHS
# ===============================

INPUT_PDBQT_DIR = "out_pdbqt"
LIGAND_POSES_DIR = "ligand_poses"
RECEPTOR_PDB = "receptor.pdb"
COMPLEX_DIR = "complexes"
LIGAND_ID_FILE = "ligands_catalog.txt"
POSE_LOG_FILE = "pose_generation.log"

os.makedirs(LIGAND_POSES_DIR, exist_ok=True)
os.makedirs(COMPLEX_DIR, exist_ok=True)

# ===============================
# STEP 1: PDBQT → PDB (poses)
# ===============================

def pdbqt_to_pdb_line(line):
    if line.startswith(("ATOM", "HETATM")):
        return line[:66] + "\n"
    return None

def extract_poses(pdbqt_file, outdir, log_handle):
    os.makedirs(outdir, exist_ok=True)

    with open(pdbqt_file) as f:
        lines = f.readlines()

    model_num = 0
    model_lines = []

    for line in lines:
        if line.startswith("MODEL"):
            if model_lines:
                outname = os.path.join(outdir, f"model_{model_num}.pdb")
                with open(outname, "w") as out:
                    out.writelines(model_lines)
                model_lines = []
            model_num += 1

        elif line.startswith(("ATOM", "HETATM")):
            pdb_line = pdbqt_to_pdb_line(line)
            if pdb_line:
                model_lines.append(pdb_line)

    if model_lines:
        outname = os.path.join(outdir, f"model_{model_num}.pdb")
        with open(outname, "w") as out:
            out.writelines(model_lines)

    log_handle.write(
        f"{os.path.basename(pdbqt_file)} > {model_num} poses\n"
    )

def generate_ligand_poses():
    pdbqt_files = glob.glob(os.path.join(INPUT_PDBQT_DIR, "*_out.pdbqt"))

    if not pdbqt_files:
        print("[ERROR] No *_out.pdbqt files found!")
        exit(1)

    with open(POSE_LOG_FILE, "w") as log:
        for f in pdbqt_files:
            base = os.path.splitext(os.path.basename(f))[0]
            ligand_id = base.replace("_out", "")
            outdir = os.path.join(LIGAND_POSES_DIR, ligand_id)

            extract_poses(f, outdir, log)

    print(f"\nSTATUS: Ligand poses generated (log saved to {POSE_LOG_FILE})")

# ===============================
# STEP 2: Generate ligand ID list
# ===============================

def generate_ligand_id_list():
    ligand_dirs = sorted(
        d for d in os.listdir(LIGAND_POSES_DIR)
        if os.path.isdir(os.path.join(LIGAND_POSES_DIR, d))
    )

    with open(LIGAND_ID_FILE, "w") as f:
        for ligand_id in ligand_dirs:
            f.write(ligand_id + "\n")

    print(f"\nSTATUS: Ligand(s) list generated and saved in: {LIGAND_ID_FILE}")

# ===============================
# STEP 3: User selection
# ===============================

def ask_user_for_ligands():
    print("\nMESSAGE: Choose your ligands from the ligands_catalog.txt file")
    print("Examples:")
    print("  Single:   Ligand_1")
    print("  Multiple: Ligand_1 Ligand_2 Ligand_3\n")

    return input("Your selection: ").split()

# ===============================
# STEP 4: Build complexes
# ===============================

def create_complex(receptor_pdb, ligand_pose_pdb, output_pdb):
    with open(output_pdb, "w") as out:

        with open(receptor_pdb) as r:
            for line in r:
                if line.startswith(("ATOM", "HETATM")):
                    out.write(line)

        with open(ligand_pose_pdb) as l:
            for line in l:
                if line.startswith(("ATOM", "HETATM")):
                    out.write(line)

        out.write("END\n")

def build_complexes(ligand_ids):
    for ligand_id in ligand_ids:
        ligand_dir = os.path.join(LIGAND_POSES_DIR, ligand_id)

        if not os.path.isdir(ligand_dir):
            print(f"[WARNING] Ligand not found: {ligand_id}")
            continue

        out_dir = os.path.join(COMPLEX_DIR, ligand_id)
        os.makedirs(out_dir, exist_ok=True)

        pose_files = sorted(glob.glob(os.path.join(ligand_dir, "model_*.pdb")))

        for pose in pose_files:
            pose_name = os.path.basename(pose).replace(".pdb", "")
            out_pdb = os.path.join(out_dir, f"{pose_name}_complex.pdb")
            create_complex(RECEPTOR_PDB, pose, out_pdb)

        print(f"[COMPLEX] {ligand_id}: {len(pose_files)} complexes created")

# ===============================
# MAIN
# ===============================

def print_header():
    header = r"""
   ####################################################################
   #                                                                  #
   #   _____             _                                            #
   #  |  __ \           | |                                           #
   #  | |  | | ___   ___| | ___ __   ___  ___  ___  __ _  ___ _ __    #
   #  | |  | |/ _ \ / __| |/ / '_ \ / _ \/ __|/ _ \/ _` |/ _ \ '_ \   # 
   #  | |__| | (_) | (__|   <| |_) | (_) \__ \  __/ (_| |  __/ | | |  #
   #  |_____/ \___/ \___|_|\_\ .__/ \___/|___/\___|\__, |\___|_| |_|  #
   #                         | |                    __/ |             #
   #                         |_|                   |___/              #
   #  [version: 1.0.0]                                                #
   #                                                                  #
   #  For more tools visit: https://github.com/alpha-horizon          #
   #                                                                  #
   ####################################################################
    """
    print(header)

def main():
    print_header()
    
    parser = argparse.ArgumentParser(description="Ligand Pose Extraction and Complex Assembly Workflow")
    parser.add_argument("-v", "--version", action="version", version="dockposegen 1.0.0")
    
    # Allows standard execution while supporting help/version flags
    parser.parse_known_args()

    # Safety Checks: Ensure required data exists before starting
    if not os.path.exists(INPUT_PDBQT_DIR):
        print(f"[ERROR] Input directory '{INPUT_PDBQT_DIR}' not found.")
        sys.exit(1)
        
    if not os.path.exists(RECEPTOR_PDB):
        print(f"[ERROR] '{RECEPTOR_PDB}' not found in current directory. This is required for complex assembly.")
        sys.exit(1)

    # Workflow execution
    generate_ligand_poses()
    generate_ligand_id_list()
    selected_ligands = ask_user_for_ligands()
    
    if not selected_ligands:
        print("No ligands selected. Exiting.")
        return

    build_complexes(selected_ligands)
    print("\nTask completed successfully!")

if __name__ == "__main__":
    main()
