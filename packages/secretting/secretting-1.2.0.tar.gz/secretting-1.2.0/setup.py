from io import open
from setuptools import setup, find_packages

name = 'secretting'
version = '1.2.0'


setup(
    name=name,
    version=version,
    description='More secrets and randoms!',
    long_description='''# More secrets and randoms!
# Installation:
```bash
pip install secretting
```
## If wont work:
```bash
pip3 install secretting
```
## Or:
```bash
pip install --upgrade secretting
```

# Example:
```python
salt() # Returns random salt
sha256("a") # Output: ca978...
secure256("a") # Output: ("generated hash", "generated salt")
# And more nice tools!
```''',
    long_description_content_type='text/markdown',
    install_requires=[],
    packages=find_packages(),
)
