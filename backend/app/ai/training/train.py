from pathlib import Path

from app.ai.training.dataset_loader import create_dataloaders
from app.ai.training.trainer import AIDetectionModel, AIDetectionTrainer

DATASET = r"C:\Users\LENOVO\Downloads\CIFAKE"

train_loader, val_loader, test_loader = create_dataloaders(
    dataset_root=DATASET,
    batch_size=16,
    image_size=224
)

model = AIDetectionModel(
    backbone_frozen=False
)

trainer = AIDetectionTrainer(
    model=model,
    train_loader=train_loader,
    val_loader=val_loader,
    checkpoint_dir="backend/app/ai/checkpoints"
)

# Resume from checkpoint if it exists
checkpoint = Path(
    "backend/app/ai/checkpoints/best_model.pth"
)
if checkpoint.exists():
   trainer.load_checkpoint(
    str(checkpoint),
    load_optimizer=False
)

trainer.train(
    num_epochs=5
)