from setuptools import setup, find_packages
from pathlib import Path

# 读取 README.md 作为长描述
readme_file = Path(__file__).parent / "README.md"
if readme_file.exists():
    with open(readme_file, "r", encoding="utf-8") as fh:
        long_description = fh.read()
else:
    long_description = "Kox - A simple code management tool for version control"

setup(
    name='kox',
    version='1.0.0',
    description='Kox - A simple code management tool for version control',
    long_description=long_description,
    long_description_content_type="text/markdown",
    author='Kox Team',
    author_email='',
    url='https://github.com/decrule/kox',
    project_urls={
        'Bug Reports': 'https://github.com/decrule/kox/issues',
        'Source': 'https://github.com/decrule/kox',
        'Documentation': 'https://github.com/decrule/kox#readme',
    },
    packages=find_packages(),
    install_requires=[
        'requests>=2.31.0',
        'tqdm>=4.66.0',
        'click>=8.0.0',
    ],
    python_requires='>=3.7',
    # 关键配置：定义命令行工具入口点
    # 安装后会自动创建 kox 命令，指向 kox.cli:cli 函数
    entry_points={
        'console_scripts': [
            'kox=kox.cli:cli',
        ],
    },
    keywords='version-control, code-management, git-alternative, code-versioning',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Version Control',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
    ],
    include_package_data=True,
    zip_safe=False,
)
