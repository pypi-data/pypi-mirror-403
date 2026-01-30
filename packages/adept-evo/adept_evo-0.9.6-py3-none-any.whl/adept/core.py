import pandas as pd
import numpy as np
import os
import sys

class AdeptAnalyzer:
    def __init__(self, mode='conservation', w_cons=1.0, w_dyn=1.0, out_dir='.', name='Protein'):
        self.mode = mode
        self.w_cons = w_cons
        self.w_dyn = w_dyn
        self.out_dir = out_dir
        self.name = name
        self.df = None
        self.labels = self._get_labels()
        
    def _get_labels(self):
        if self.mode == 'coupling':
            return {'primary': 'DCopS', 'secondary': 'RCopS', 'val_col': 'enrichment'}
        else:
            return {'primary': 'DCS', 'secondary': 'RCS', 'val_col': 'conservation'}

    def load_data(self, combined_path=None, rmsf_path=None, data_path=None):
        """Loads and merges data from CSV files."""
        def find_col(columns, search_terms):
            for col in columns:
                if any(term in col.lower() for term in search_terms):
                    return col
            return None

        try:
            if combined_path:
                print(f"Loading combined file: {combined_path}")
                df_raw = pd.read_csv(combined_path, sep=None, engine='python')
                col_res = find_col(df_raw.columns, ['res', 'pos', 'index', 'i'])
                col_rmsf = find_col(df_raw.columns, ['rmsf', 'fluct', 'dyn'])
                col_val = find_col(df_raw.columns, ['cons', 'evol', 'entropy', 'enrich', 'coup'])
                
                if not all([col_res, col_rmsf, col_val]):
                    raise ValueError(f"Missing columns in combined file. Found: {df_raw.columns.tolist()}")
                
                self.df = df_raw[[col_res, col_rmsf, col_val]].copy()
                self.df.columns = ['residue', 'rmsf', 'base_val']

            elif rmsf_path and data_path:
                print(f"Loading separate files: {rmsf_path} & {data_path}")
                df_rmsf = pd.read_csv(rmsf_path, sep=None, engine='python')
                col_res_r = find_col(df_rmsf.columns, ['res', 'pos', 'index', 'i'])
                col_rmsf = find_col(df_rmsf.columns, ['rmsf', 'fluct', 'dyn'])
                
                df_data = pd.read_csv(data_path, sep=None, engine='python')
                col_res_d = find_col(df_data.columns, ['res', 'pos', 'index', 'i'])
                col_val = find_col(df_data.columns, ['cons', 'evol', 'entropy', 'enrich', 'coup'])

                if not all([col_res_r, col_rmsf, col_res_d, col_val]):
                     raise ValueError("Could not identify required columns.")

                df_rmsf = df_rmsf[[col_res_r, col_rmsf]].rename(columns={col_res_r: 'residue', col_rmsf: 'rmsf'})
                df_data = df_data[[col_res_d, col_val]].rename(columns={col_res_d: 'residue', col_val: 'base_val'})
                
                self.df = pd.merge(df_rmsf, df_data, on='residue', how='inner')
            else:
                raise ValueError("No input files provided.")

        except Exception as e:
            print(f"Error loading data: {e}")
            sys.exit(1)

    def calculate_scores(self):
        """Calculates DCS/RCS scores based on loaded data."""
        if self.df is None: return
        
        # Normalize RMSF (0 to 1)
        min_r, max_r = self.df['rmsf'].min(), self.df['rmsf'].max()
        r_range = max_r - min_r if max_r != min_r else 1.0
        
        self.df['norm_dyn'] = (self.df['rmsf'] - min_r) / r_range
        self.df['norm_rigid'] = 1.0 - self.df['norm_dyn']
        
        # Calculate Scores
        self.df['score1_raw'] = (self.df['base_val'] ** self.w_cons) * (self.df['norm_dyn'] ** self.w_dyn)
        self.df['score2_raw'] = (self.df['base_val'] ** self.w_cons) * (self.df['norm_rigid'] ** self.w_dyn)
        
        # Scale 0-10
        self.df[self.labels['primary']] = (self.df['score1_raw'] / (self.df['score1_raw'].max() or 1)) * 10
        self.df[self.labels['secondary']] = (self.df['score2_raw'] / (self.df['score2_raw'].max() or 1)) * 10

    def export_csv(self):
        """Saves the results to CSV."""
        if self.df is None: return
        out_path = os.path.join(self.out_dir, f"{self.name}_ADEPT_{self.mode}.csv")
        export = self.df[['residue', self.labels['primary'], self.labels['secondary'], 'rmsf', 'base_val']]
        export.columns = ['Residue', self.labels['primary'], self.labels['secondary'], 'Raw_RMSF', 'Raw_Data']
        export.to_csv(out_path, index=False)
        print(f"Saved CSV: {out_path}")

    def map_structure(self, pdb_path):
        """Maps scores to B-factor column of a PDB file."""
        if not pdb_path or self.df is None: return
        
        try:
            with open(pdb_path, 'r') as f: lines = f.readlines()
            
            map_prim = dict(zip(self.df['residue'], self.df[self.labels['primary']]))
            map_sec = dict(zip(self.df['residue'], self.df[self.labels['secondary']]))
            
            def write_pdb(score_map, suffix):
                new_lines = []
                for line in lines:
                    if line.startswith(('ATOM', 'HETATM')):
                        try:
                            res_id = int(line[22:26].strip())
                            if res_id in score_map:
                                line = line[:60] + "{:6.2f}".format(score_map[res_id]) + line[66:]
                            else:
                                line = line[:60] + "  0.00" + line[66:]
                        except: pass
                    new_lines.append(line)
                
                out_path = os.path.join(self.out_dir, f"{self.name}_Mapped_{suffix}.pdb")
                with open(out_path, 'w') as f: f.writelines(new_lines)
                print(f"Saved PDB: {out_path}")
                self._write_pymol(out_path, suffix)

            write_pdb(map_prim, self.labels['primary'])
            write_pdb(map_sec, self.labels['secondary'])
            
        except Exception as e:
            print(f"Error processing PDB: {e}")

    def _write_pymol(self, pdb_file, suffix):
        fname = os.path.basename(pdb_file)
        grad = "white_red" if suffix == self.labels['primary'] else "white_blue"
        script = f"""
reinitialize
load {fname}, protein
hide all
show cartoon, protein
cartoon putty
set cartoon_putty_scale_min, 0.5
set cartoon_putty_scale_max, 4.0
spectrum b, {grad}, protein, minimum=0, maximum=10
bg_color white
set specular, 0.5
zoom
"""
        out_path = os.path.join(self.out_dir, f"{self.name}_{suffix}_View.pml")
        with open(out_path, 'w') as f: f.write(script)
