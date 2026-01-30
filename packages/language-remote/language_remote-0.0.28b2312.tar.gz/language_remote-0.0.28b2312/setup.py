import setuptools  # type: ignore

PACKAGE_NAME = "language-remote"
package_dir = PACKAGE_NAME.replace("-", "_")

# with open('README.md') as f:
#   readme = f.read()

setuptools.setup(
    name=PACKAGE_NAME,  # https://pypi.org/project/language-remote
    version='0.0.28b2312',
    author="Circles",
    author_email="info@circles.life",
    url=f"https://github.com/circles-zone/{PACKAGE_NAME}-python-package",
    packages=[package_dir],
    package_dir={package_dir: f'{package_dir}/src'},
    package_data={package_dir: ['*.py']},
    long_description="Language Remote",
    long_description_content_type='text/markdown',
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        "langdetect>=1.0.9",
        "logger-local>=0.0.3"
    ]
)
