from setuptools import setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name='abmeter',
    version='0.0.2',
    description='ABMeter - A/B testing and experimentation platform. Coming soon.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='ABMeter',
    author_email='info@abmeter.com',
    packages=[],
    classifiers=[
        'Development Status :: 1 - Planning',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
    ],
    python_requires='>=3.7',
    keywords='ab-testing experimentation feature-flags analytics',
)
