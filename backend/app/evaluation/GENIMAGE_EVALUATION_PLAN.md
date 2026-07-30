==========================================
GenImage Evaluation Plan
==========================================

Official Repository:
https://github.com/GenImage-Dataset/GenImage
Homepage: https://genimage-dataset.github.io/

Dataset Structure:
The GenImage dataset is organized by AI generator with train/val splits. Each generator folder contains:
- train/ai/ - AI-generated training images
- train/nature/ - Real images (duplicated across generators)
- val/ai/ - AI-generated validation images
- val/nature/ - Real images (duplicated across generators)

Original structure after extraction:
```
GenImage/
├── Midjourney/
│   ├── train/
│   │   ├── ai/
│   │   ├── nature/
│   ├── val/
│   │   ├── ai/
│   │   ├── nature/
├── VQDM/
│   ├── train/
│   │   ├── ai/
│   │   ├── nature/
│   ├── val/
│   │   ├── ai/
│   │   ├── nature/
├── Wukong/
│   ├── train/
│   │   ├── ai/
│   │   ├── nature/
│   ├── val/
│   │   ├── ai/
│   │   ├── nature/
├── Stable Diffusion V1.4/
│   ├── train/
│   │   ├── ai/
│   │   ├── nature/
│   ├── val/
│   │   ├── ai/
│   │   ├── nature/
├── Stable Diffusion V1.5/
│   ├── train/
│   │   ├── ai/
│   │   ├── nature/
│   ├── val/
│   │   ├── ai/
│   │   ├── nature/
├── GLIDE/
│   ├── train/
│   │   ├── ai/
│   │   ├── nature/
│   ├── val/
│   │   ├── ai/
│   │   ├── nature/
├── BigGAN/
│   ├── train/
│   │   ├── ai/
│   │   ├── nature/
│   ├── val/
│   │   ├── ai/
│   │   ├── nature/
├── ADM/
│   ├── train/
│   │   ├── ai/
│   │   ├── nature/
│   ├── val/
│   │   ├── ai/
│   │   ├── nature/
```

Available Generators:
1. Midjourney - Commercial AI art generator
2. Stable Diffusion V1.4 - Open-source diffusion model
3. Stable Diffusion V1.5 - Open-source diffusion model (improved)
4. ADM (Ablated Diffusion Model) - OpenAI guided diffusion
5. GLIDE - OpenAI text-to-image model
6. VQDM (VQ Diffusion Model) - Microsoft VQ-Diffusion
7. BigGAN - Large-scale GAN generator
8. Wukong - Chinese AI image generator

Recommended Evaluation Subset:
For a small evaluation subset (~1000 images total), recommend:

AI Images (500 total):
- Stable Diffusion V1.5: 200 images (from val/ai/)
- Midjourney: 200 images (from val/ai/)
- ADM: 100 images (from val/ai/)

Real Images (500 total):
- Nature images from val/nature/ folders (any generator, as they are duplicates)
- Select 500 unique real images

Rationale:
- Stable Diffusion and Midjourney represent the most widely used AI generators
- ADM provides diversity with a different generation approach
- Using validation split ensures images are not used in training
- 500 AI + 500 Real provides balanced evaluation

Expected Disk Usage:
- Full GenImage dataset: ~500 GB
- Recommended subset: ~50-100 MB (depending on image resolution)

Expected Folder Layout:
```
TruthLensDataset/evaluation/genimage/
├── ai/
│   ├── stable_diffusion/
│   │   ├── [200 images from SD V1.5 val/ai/]
│   ├── midjourney/
│   │   ├── [200 images from Midjourney val/ai/]
│   ├── adm/
│   │   ├── [100 images from ADM val/ai/]
└── real/
    ├── [500 images from val/nature/]
```

Alternative simplified structure (recommended for TruthLens):
```
TruthLensDataset/evaluation/genimage/
├── ai/
│   ├── [500 AI images from multiple generators]
└── real/
    ├── [500 real nature images]
```

Download Steps:
1. Access Google Drive: https://drive.google.com/drive/folders/1jGt10bwTbhEZuGXLyvrCuxOI0cBqQ1FS?usp=sharing
2. Download individual generator folders (not full dataset):
   - Stable Diffusion V1.5/
   - Midjourney/
   - ADM/
3. Extract downloaded archives
4. Navigate to val/ai/ folders for each generator
5. Copy sample images to TruthLensDataset/evaluation/genimage/ai/
6. Copy real images from val/nature/ to TruthLensDataset/evaluation/genimage/real/
7. Verify image counts match targets

Notes:
- The full dataset is very large (~500GB), so downloading only specific generators is recommended
- Real images are duplicated across all generators in the nature/ folders
- For evaluation purposes, using the validation split is recommended to avoid training data contamination
- Images are in various formats (JPG, PNG) - TruthLens supports both
- The dataset uses ImageNet class labels (1000 classes) but for binary classification we only need Real vs AI labels

==========================================
