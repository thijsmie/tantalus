from setuptools import setup


setup(
    name='holdmybeer',
    version='0.0.2',
    author='Thijs Miedema',
    author_email='mail@tmiedema.com',
    url='http://tmiedema.com',
    packages=['holdmybeer',],
    license="MIT",
    description="Formalize managing inventory as product buckets.",
    long_description="Formalize managing inventory as product buckets.",
    setup_requires=['pytest-runner'],
    tests_require=['pytest'],
)
