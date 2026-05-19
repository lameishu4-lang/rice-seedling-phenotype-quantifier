@echo off
chcp 65001

echo Building Rice Seedling Phenotype Quantifier...

pyinstaller ^
  --noconfirm ^
  --windowed ^
  --name RiceSeedlingPhenotypeQuantifier ^
  main.py

echo Build finished.
pause