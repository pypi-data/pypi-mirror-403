from setuptools import setup, find_packages

setup(
    name="hand_gesture_engine",
    version="0.1.1",
    description="A lightweight hand gesture recognition engine",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="Karan Vishwakarma",
    author_email="vishwakarmakaran625@gmail.com",
    url="https://github.com/KaranVishwakarma-1807/hand-gesture-engine",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "opencv-python",
        "mediapipe",
        "numpy",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
