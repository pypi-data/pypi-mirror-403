import os
from setuptools import setup, find_packages

# 현재 폴더의 위치를 잡습니다.
here = os.path.abspath(os.path.dirname(__file__))

# EasyUI 폴더 내부의 README.md를 읽어옵니다.
readme_path = os.path.join(here, "EasyUI", "README.md")
with open(readme_path, "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="easyui-python",
    version="1.1.0",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        # 패키지 내부(EasyUI/)의 데이터들을 명시적으로 포함시킵니다.
        'EasyUI': ['README.md', 'styles/*.json'],
    },
    entry_points={
        'console_scripts': [
            'EasyUI-designer=EasyUI.library:run_designer',
        ],
    },
    author="kdh",
    description="Easy Python GUI Designers and Libraries",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/sjn8623-collab/EasyUI",
    install_requires=[
        "Pillow",
        "tkinterdnd2",
    ],
    python_requires='>=3.6',
)