from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="vitosa-speech-II", 
    version="0.0.1",
    
    author="Vy Le-Phuong Huynh, Huy Ba Do and Luan Thanh Nguyen", 
    author_email="luannt@uit.edu.vn",
    
    description="A library for Robust Vietnamese Audio-Based Toxic Span Detection and Censoring",
    long_description=long_description,
    long_description_content_type="text/markdown",
    
    # Link GitHub chính thức (quan trọng)
    # url="https://github.com/ViToSAResearch/PhoWhisper-BiLSTM-CRF",
    
    # Tạo các liên kết bổ sung ở cột bên trái trang PyPI
    project_urls={
        # "Bug Tracker": "https://github.com/ViToSAResearch/PhoWhisper-BiLSTM-CRF/issues",
        "Model (Hugging Face)": "https://huggingface.co/UIT-ViToSA/PhoWhisper-BiLSTM-CRF"
    },
    
    packages=find_packages(exclude=("tests", "docs")),
    
    install_requires=[
        "torch>=1.13.0",      
        "transformers>=4.28.0",
        "librosa",
        "pydub",
        "huggingface_hub",
        "pytorch-crf",     
        "numpy",
        "tqdm"
    ],
    
    keywords=[
        "audio-processing", 
        "toxic-span-detection", 
        "vietnamese", 
        "asr", 
        "speech-recognition", 
        "censoring",
        "phowhisper"
    ],
    
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Multimedia :: Sound/Audio :: Speech",
        "Natural Language :: Vietnamese",
    ],
    
    python_requires='>=3.7',
)