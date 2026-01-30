import setuptools

with open("README.md", "r", encoding='utf-8') as f:
    long_description = f.read()

setuptools.setup(
    name='zaishiyishihejipage',
    version='0.0.2',
    author='王梓明',
    author_email='1272660211@qq.com',
    description='一个存储王梓明做的网页的包',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='',
    packages=setuptools.find_packages(),
    include_package_data=True,
    package_data={
        'zaishiyishihejipage': ['data/main/**/*']
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
)