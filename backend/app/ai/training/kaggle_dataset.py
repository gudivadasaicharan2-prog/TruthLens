"""
Kaggle AI vs Human Dataset Loader
=================================
Supports the Women in AI Kaggle dataset.

Structure:
AI_vs_Human/
│
├── train.csv
├── train_data/
└── test_data_v2/
"""

import os
import pandas as pd
from PIL import Image

from sklearn.model_selection import train_test_split

import torch
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms


class KaggleAIDataset(Dataset):
    def __init__(
        self,
        dataframe,
        root_dir,
        image_size=224,
        train=True
    ):
        self.data = dataframe.reset_index(drop=True)
        self.root_dir = root_dir

        if train:
            self.transform = transforms.Compose([

                # Better than Resize
                transforms.RandomResizedCrop(
                    image_size,
                    scale=(0.80, 1.0)
                ),

                transforms.RandomHorizontalFlip(p=0.5),

                transforms.RandomRotation(10),

                

                transforms.ColorJitter(
                    brightness=0.20,
                    contrast=0.20,
                    saturation=0.20,
                    hue=0.05
                ),

             

                transforms.ToTensor(),

                transforms.Normalize(
                    mean=[0.485,0.456,0.406],
                    std=[0.229,0.224,0.225]
                ),

                transforms.RandomErasing(
                    p=0.25,
                    scale=(0.02,0.15)
                )

            ])

        else:

            self.transform = transforms.Compose([

                transforms.Resize(
                    (image_size,image_size)
                ),

                transforms.ToTensor(),

                transforms.Normalize(
                    mean=[0.485,0.456,0.406],
                    std=[0.229,0.224,0.225]
                )

            ])

    def __len__(self):
        return len(self.data)

    def __getitem__(self, index):

        row = self.data.iloc[index]

        image_path = os.path.join(
            self.root_dir,
            row["file_name"]
        )

        image = Image.open(image_path).convert("RGB")

        image = self.transform(image)

        label = int(row["label"])

        return image, label


def create_kaggle_dataloaders(
    csv_path,
    root_dir,
    batch_size=16,
    image_size=224,
    num_workers=4
):

    df = pd.read_csv(csv_path)

    train_df, val_df = train_test_split(
        df,
        test_size=0.10,
        random_state=42,
        stratify=df["label"]
    )

    train_dataset = KaggleAIDataset(
        train_df,
        root_dir=root_dir,
        image_size=image_size,
        train=True
    )

    val_dataset = KaggleAIDataset(
        val_df,
        root_dir=root_dir,
        image_size=image_size,
        train=False
    )

    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=4,
        pin_memory=True,
        persistent_workers=True,
        prefetch_factor=2
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=4,
        pin_memory=True,
        persistent_workers=True,
        prefetch_factor=2
    )

    print("=" * 60)
    print("Women in AI Dataset Loaded")
    print("=" * 60)
    print(f"Training Images   : {len(train_dataset)}")
    print(f"Validation Images : {len(val_dataset)}")
    print("=" * 60)

    return train_loader, val_loader