import os
import shutil
import sys
from pathlib import Path


def main() -> int:  
    img_path = Path(os.getcwd(), sys.argv[1])
    if img_path.exists():
        shutil.rmtree(img_path.resolve())


if __name__ == "__main__":
    main()