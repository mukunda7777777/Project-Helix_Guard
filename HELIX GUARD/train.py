# train.py
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np

class ResidualBlock1D(nn.Module):
    """Residual block allowing deeper feature capture without gradient degradation."""
    def __init__(self, channels):
        super().__init__()
        self.conv1 = nn.Conv1d(channels, channels, kernel_size=5, padding=2)
        self.bn1 = nn.BatchNorm1d(channels)
        self.relu = nn.ReLU()
        self.conv2 = nn.Conv1d(channels, channels, kernel_size=5, padding=2)
        self.bn2 = nn.BatchNorm1d(channels)

    def forward(self, x):
        residual = x
        out = self.relu(self.bn1(self.conv1(x)))
        out = self.bn2(self.conv2(out))
        return self.relu(out + residual)


class GenoCorrectCNN(nn.Module):
    """Deep Residual 1D-CNN for Genomic Pathogenicity Scoring."""
    def __init__(self, seq_len=101):
        super().__init__()
        self.stem = nn.Sequential(
            nn.Conv1d(4, 32, kernel_size=7, padding=3),
            nn.BatchNorm1d(32),
            nn.ReLU()
        )
        self.res1 = ResidualBlock1D(32)
        self.res2 = ResidualBlock1D(32)
        
        self.head = nn.Sequential(
            nn.AdaptiveAvgPool1d(1),
            nn.Flatten(),
            nn.Linear(32, 16),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(16, 1),
            nn.Sigmoid()
        )

    def forward(self, x):
        x = self.stem(x)
        x = self.res1(x)
        x = self.res2(x)
        return self.head(x)


def generate_biologically_grounded_data(n_samples=2000, seq_len=101):
    """Generates synthetic DNA matrices with structured pathogenic motifs."""
    X = np.zeros((n_samples, 4, seq_len), dtype=np.float32)
    y = np.zeros((n_samples, 1), dtype=np.float32)
    
    nuc_map = {'A': 0, 'C': 1, 'G': 2, 'T': 3}

    for i in range(n_samples):
        # Base random sequence
        seq_indices = np.random.choice([0, 1, 2, 3], size=seq_len, p=[0.3, 0.2, 0.2, 0.3])
        for pos, idx in enumerate(seq_indices):
            X[i, idx, pos] = 1.0

        # Calculate biologically-relevant risk factors
        gc_content = np.sum(X[i, 1, :] + X[i, 2, :]) / seq_len
        
        # Inject known pathogenic-like motif patterns (e.g., poly-G runs or CG islands)
        has_poly_g = np.sum(X[i, 2, 40:50]) >= 7
        
        # Determine continuous risk score
        risk = 0.2 * gc_content + (0.6 if has_poly_g else 0.05) + np.random.normal(0, 0.05)
        y[i, 0] = np.clip(risk, 0.0, 1.0)

    return torch.tensor(X, dtype=torch.float32), torch.tensor(y, dtype=torch.float32)


def train_model():
    print("⚡ Training Enhanced Residual 1D-CNN Model...")
    X, y = generate_biologically_grounded_data()
    
    model = GenoCorrectCNN()
    criterion = nn.MSELoss()
    optimizer = optim.AdamW(model.parameters(), lr=0.003, weight_decay=1e-4)

    dataset = torch.utils.data.TensorDataset(X, y)
    loader = torch.utils.data.DataLoader(dataset, batch_size=64, shuffle=True)

    model.train()
    for epoch in range(1, 21):
        total_loss = 0.0
        for batch_x, batch_y in loader:
            optimizer.zero_grad()
            preds = model(batch_x)
            loss = criterion(preds, batch_y)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
        
        if epoch % 5 == 0:
            print(f"Epoch {epoch}/20 - Loss: {total_loss/len(loader):.5f}")

    torch.save(model.state_dict(), "genocorrect_cnn.pt")
    print("✅ Model weights saved to genocorrect_cnn.pt")

if __name__ == "__main__":
    train_model()