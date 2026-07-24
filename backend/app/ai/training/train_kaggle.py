from pathlib import Path

from app.ai.training.kaggle_dataset import create_kaggle_dataloaders
from app.ai.training.trainer import (
    AIDetectionModel,
    AIDetectionTrainer,
)


def main():

    DATASET_ROOT = r"C:\Users\LENOVO\Downloads\AI_Datasets\AI_vs_Human"

    train_loader, val_loader = create_kaggle_dataloaders(
        csv_path=DATASET_ROOT + r"\train.csv",
        root_dir=DATASET_ROOT,
        batch_size=32,
        image_size=224
    )

    model = AIDetectionModel(backbone_frozen=False)

    trainer = AIDetectionTrainer(
        model=model,
        train_loader=train_loader,
        val_loader=val_loader,
        learning_rate=1e-5,
        checkpoint_dir="backend/app/ai/checkpoints",
        t_max=8
    )

    checkpoint = Path("backend/app/ai/checkpoints/best_model.pth")

    if checkpoint.exists():
        trainer.load_checkpoint(
            str(checkpoint),
            load_optimizer=False
        )

    trainer.train(
        num_epochs=8,
        early_stopping_patience=5,
        save_interval=1
    )


if __name__ == "__main__":
    main()