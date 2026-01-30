from setuptools import setup
from pathlib import Path
import os
import shutil

# -------------------------------------------------------------------
# 1) Paket klasörünü hazırla (build-time)
# -------------------------------------------------------------------
PACKAGE_IMPORT_NAME = "fycore"        # import fycore
PACKAGE_DIST_NAME = "fycore-sdk"      # pip/pypi ismi
VERSION = "1.0.2"

BASE_DIR = Path(__file__).parent.resolve()
DIST_DIR = BASE_DIR / "dist"

OBFUSCATED_MODULE = DIST_DIR / "fycore_sdk.py"
PYARMOR_RUNTIME_SRC = DIST_DIR / "pyarmor_runtime_000000"

PACKAGE_DIR = BASE_DIR / PACKAGE_IMPORT_NAME

# Eski klasörü temizle
if PACKAGE_DIR.exists():
    shutil.rmtree(PACKAGE_DIR)
# PACKAGE_DIR.mkdir(exist_ok=True)  <-- ARTIK GEREK YOK

# -------------------------------------------------------------------
# 2) README'den uzun açıklama çek
# -------------------------------------------------------------------
readme_path = BASE_DIR / "README.md"
if readme_path.exists():
    long_description = readme_path.read_text(encoding="utf-8")
else:
    long_description = ""

# -------------------------------------------------------------------
# 3) Setup config (Flat Layout: fycore_sdk.py + runtime paketi)
# -------------------------------------------------------------------
# setup() fonksiyonu dist/ klasöründeki dosyaları package_dir ile bulacak.

setup(
    name=PACKAGE_DIST_NAME,               # pip install fycore-sdk
    version=VERSION,
    description="Consciousness-aware AI orchestration SDK built on the CCFy framework (PyArmor protected).",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Fatih Yenen",
    author_email="research@sonra.art",
    url="https://github.com/fthynn/fycore-sdk",

    # Flat Layout:
    # 1. pyarmor_runtime_000000 bir pakettir.
    # 2. fycore_sdk bir modüldür (.py).
    
    # Kaynak dosyaların yeri: dist/
    package_dir={"": "dist"},
    
    packages=["pyarmor_runtime_000000"],  # Runtime paketi
    py_modules=["fycore_sdk"],            # Ana modül (import fycore_sdk)

    # Runtime içindeki (alt klasörlerdeki) .pyd/.so/.dll dosyalarını pakete dahil et
    package_data={
        "pyarmor_runtime_000000": ["*", "**/*"], # Tüm dosyaları (linux/windows klasörleri dahil) al
    },
    include_package_data=True,
    zip_safe=False,        # PyArmor runtime + binary içerdiği için zip'ten çalıştırma güvenli değil

    python_requires=">=3.10",
    install_requires=[
        # SDK kullanırken gereken bağımlılıkları buraya eklersin
    ],
    extras_require={
        "dev": [
            "build>=1.0.0",
            "twine>=5.0.0",
        ]
    },
    license="Proprietary",
    keywords=(
        "ai artificial-intelligence sdk agents orchestration "
        "multi-agent llm framework consciousness ccfy fycore"
    ),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: 3 :: Only",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: Other/Proprietary License",
    ],
    project_urls={
        "Source": "https://github.com/fthynn/fycore-sdk",
        "Tracker": "https://github.com/fthynn/fycore-sdk/issues",
    },
)
