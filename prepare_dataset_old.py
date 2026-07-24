from pathlib import Path
import random
import shutil

random.seed(42)

# ----------------------------
# CHANGE THESE PATHS IF NEEDED
# ----------------------------

REAL_SOURCE = Path(r"C:\Users\LENOVO\Downloads\train2017\train2017")

ADM_SOURCE = Path(
    r"C:\Users\LENOVO\Downloads\ADM-20260704T111833Z-3-013\ADM\imagenet_ai_0508_adm\train\ai"
)

GLIDE_SOURCE = Path(
    r"C:\Users\LENOVO\Downloads\glide-20260704T111826Z-3-011\glide\imagenet_glide\train\ai"
)

OUTPUT = Path("dataset")

# Number of images
REAL_IMAGES = 30000
ADM_IMAGES = 15000
GLIDE_IMAGES = 15000

TRAIN_RATIO = 0.8
VAL_RATIO = 0.1
TEST_RATIO = 0.1


def copy_split(files, label):
    random.shuffle(files)

    n = len(files)

    train = files[:int(n * TRAIN_RATIO)]
    val = files[int(n * TRAIN_RATIO):int(n * (TRAIN_RATIO + VAL_RATIO))]
    test = files[int(n * (TRAIN_RATIO + VAL_RATIO)):]

    for split, subset in zip(
        ["train", "val", "test"],
        [train, val, test]
    ):

        dst = OUTPUT / split / label
        dst.mkdir(parents=True, exist_ok=True)

        for f in subset:
            shutil.copy2(f, dst / f.name)

real_files = list(REAL_SOURCE.glob("*.jpg"))
adm_files = list(ADM_SOURCE.rglob("*"))
glide_files = list(GLIDE_SOURCE.rglob("*"))

adm_files = [f for f in adm_files if f.suffix.lower() in [".png", ".jpg", ".jpeg", ".webp"]]
glide_files = [f for f in glide_files if f.suffix.lower() in [".png", ".jpg", ".jpeg", ".webp"]]

print("Real images found :", len(real_files))
print("ADM images found  :", len(adm_files))
print("GLIDE images found:", len(glide_files))

real = random.sample(real_files, REAL_IMAGES)
adm = random.sample(adm_files, ADM_IMAGES)
glide = random.sample(glide_files, GLIDE_IMAGES)

copy_split(real, "real")
copy_split(adm + glide, "ai")

print("Dataset created successfully!")