import argparse
import os
from .core import AdeptAnalyzer

def main():
    parser = argparse.ArgumentParser(description='ADEPT | Dynamics-Aware Evolutionary Profiling CLI')
    
    # Inputs
    parser.add_argument('--name', type=str, default='Protein', help='Project name')
    parser.add_argument('--mode', type=str, choices=['conservation', 'coupling'], default='conservation')
    
    # Files
    parser.add_argument('--combined', type=str, help='Path to combined CSV')
    parser.add_argument('--rmsf', type=str, help='Path to RMSF CSV/TSV')
    parser.add_argument('--data', type=str, help='Path to Conservation/Enrichment CSV/TSV')
    parser.add_argument('--pdb', type=str, help='Path to PDB file')
    parser.add_argument('--out_dir', type=str, default='.', help='Output directory')
    
    # Weights
    parser.add_argument('--w_cons', type=float, default=1.0, help='Weight for Conservation')
    parser.add_argument('--w_dyn', type=float, default=1.0, help='Weight for Dynamics')

    # Parse arguments (supports Colab/Jupyter safely)
    args, _ = parser.parse_known_args()

    # Ensure output directory exists
    if args.out_dir != '.' and not os.path.exists(args.out_dir):
        os.makedirs(args.out_dir)

    # Initialize Analyzer
    analyzer = AdeptAnalyzer(
        mode=args.mode,
        w_cons=args.w_cons,
        w_dyn=args.w_dyn,
        out_dir=args.out_dir,
        name=args.name
    )
    
    # Run Pipeline
    if args.combined or (args.rmsf and args.data):
        analyzer.load_data(args.combined, args.rmsf, args.data)
        analyzer.calculate_scores()
        analyzer.export_csv()
        if args.pdb:
            analyzer.map_structure(args.pdb)
        print("--- ADEPT Analysis Complete ---")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
