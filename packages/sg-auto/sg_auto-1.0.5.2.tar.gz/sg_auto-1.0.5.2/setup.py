from setuptools import setup, find_packages

setup(
    name="sg_auto",  # 包名
    version="1.0.5.2",  # 版本号
    author="sg",  # 作者名字
    author_email="543091200@qq.com",  # 作者邮箱
    description="A short description of this project",  # 描述
    long_description="A longer description of this project",  # 详细描述
    url="https://github.com/yourusername/example",  # 主页 URL
    # packages=["crossPlat","tnu",],
    packages=find_packages(),  # 包列表
    # packages=find_packages(exclude=["A", "B"])		# 打包除了指定模块的全部模块
    install_requires=["numpy", "scipy"],  # 运行时依赖关系
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],  # 分类标签

    # include_package_data = True,						# 打包路径下的其他文件

)