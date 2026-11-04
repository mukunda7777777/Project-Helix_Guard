# model_engine.py
import os
import torch
import numpy as np
from train import GenoCorrectCNN

class MLDrivenSequentialOptimizer:
    def __init__(self, model_path="genocorrect_cnn.pt"):
        self.nuc_map = {'A': 0, 'C': 1, 'G': 2, 'T': 3}
        self.idx_to_nuc = {0: 'A', 1: 'C', 2: 'G', 3: 'T'}
        self.model = GenoCorrectCNN()
        
        if os.path.exists(model_path):
            self.model.load_state_dict(torch.load(model_path))
            self.model.eval()
            print("✅ Loaded trained Residual CNN weights.")
        else:
            print("⚠️ Weights file missing! Train the model first with `python train.py`.")

    def predict_pathogenicity(self, matrix):
        tensor_in = torch.tensor(matrix, dtype=torch.float32).unsqueeze(0)
        with torch.no_grad():
            score = float(self.model(tensor_in).item())
        return score

    def auto_optimize_sequence(self, matrix, target_region=(10, 90)):
        """Scans single-base substitutions and ranks them by pathogenicity drop."""
        initial_score = self.predict_pathogenicity(matrix)
        candidates = []

        start_pos, end_pos = target_region
        for pos in range(start_pos, min(end_pos, matrix.shape[1])):
            current_base_idx = np.argmax(matrix[:, pos])
            
            for alt_base, b_idx in self.nuc_map.items():
                if b_idx == current_base_idx:
                    continue
                
                test_matrix = matrix.copy()
                test_matrix[:, pos] = 0.0
                test_matrix[b_idx, pos] = 1.0
                
                new_score = self.predict_pathogenicity(test_matrix)
                score_drop = initial_score - new_score
                
                if score_drop > 0:
                    candidates.append({
                        "position": pos,
                        "original_base": self.idx_to_nuc[current_base_idx],
                        "suggested_base": alt_base,
                        "new_score": new_score,
                        "score_drop": score_drop
                    })

        candidates = sorted(candidates, key=lambda x: x["score_drop"], reverse=True)
        return initial_score, candidates[:5]

    def generate_perfected_sequence(self, raw_seq, best_edit):
        """Applies the optimal recommended edit to produce the finalized gene string."""
        if not best_edit:
            return raw_seq
        
        pos = best_edit['position']
        new_base = best_edit['suggested_base']
        
        seq_list = list(raw_seq)
        if 0 <= pos < len(seq_list):
            seq_list[pos] = new_base
            
        return "".join(seq_list)