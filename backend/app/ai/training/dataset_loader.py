"""
Dataset Loader for CIFAKE
Loads CIFAKE directly without creating a copied dataset folder.
"""

from pathlib import Path
import random

from PIL import Image

import torch
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms


class AIDetectionDataset(Dataset):
    def __init__(self, samples, transform=None):
        self.samples = samples
        self.transform = transform

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, index):
        img_path, label = self.samples[index]

        image = Image.open(img_path).convert("RGB")

        if self.transform:
            image = self.transform(image)

        return image, label


def get_images(folder: Path):
    images = []

    for ext in ["*.jpg", "*.jpeg", "*.png", "*.JPG", "*.JPEG", "*.PNG"]:
        images.extend(folder.glob(ext))

    return images


def create_dataloaders(
    dataset_root,
    batch_size=16,
   num_workers=0,
    image_size=224,
    ai_sources=None
):
    random.seed(42)

    root = Path(dataset_root)

    train_real = get_images(root / "train" / "REAL")
    train_fake = get_images(root / "train" / "FAKE")

    test_real = get_images(root / "test" / "REAL")
    test_fake = get_images(root / "test" / "FAKE")

    random.shuffle(train_real)
    random.shuffle(train_fake)

    split_real = int(len(train_real) * 0.8)
    split_fake = int(len(train_fake) * 0.8)

    train_samples = (
        [(str(img), 0) for img in train_real[:split_real]]
        + [(str(img), 1) for img in train_fake[:split_fake]]
    )

    val_samples = (
        [(str(img), 0) for img in train_real[split_real:]]
        + [(str(img), 1) for img in train_fake[split_fake:]]
    )

    test_samples = (
        [(str(img), 0) for img in test_real]
        + [(str(img), 1) for img in test_fake]
    )

    normalize = transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225],
    )

    train_transform = transforms.Compose([
        transforms.Resize((image_size, image_size)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(10),
        transforms.ColorJitter(
            brightness=0.2,
            contrast=0.2,
            saturation=0.2,
        ),
        transforms.ToTensor(),
        normalize,
    ])

    test_transform = transforms.Compose([
        transforms.Resize((image_size, image_size)),
        transforms.ToTensor(),
        normalize,
    ])

    train_dataset = AIDetectionDataset(train_samples, train_transform)
    val_dataset = AIDetectionDataset(val_samples, test_transform)
    test_dataset = AIDetectionDataset(test_samples, test_transform)

    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=0,
        pin_memory=torch.cuda.is_available(),
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=0,
        pin_memory=torch.cuda.is_available(),
    )

    test_loader = DataLoader(
        test_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=0,
        pin_memory=torch.cuda.is_available(),
    )

    print("=" * 50)
    print("CIFAKE Dataset Loaded")
    print("=" * 50)
    print(f"Training images   : {len(train_dataset)}")
    print(f"Validation images : {len(val_dataset)}")
    print(f"Test images       : {len(test_dataset)}")
    print("=" * 50)

    return train_loader, val_loader, test_loader