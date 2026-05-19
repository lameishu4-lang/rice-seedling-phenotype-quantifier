# -*- coding: utf-8 -*-

"""
Rice Seedling Phenotype Quantifier

本软件采用传统图像处理方法，不包含深度学习训练、生成式人工智能服务、
云端推理或外部 AI 接口。
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from rice_phenotype.app import run_app


if __name__ == "__main__":
    run_app()