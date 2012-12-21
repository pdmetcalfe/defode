#! /usr/bin/python

from distutils.core import setup


def main():
    with open('README.md') as src:
        long_description = src.read()
    setup(name='defode',
          packages=['defode'],
          version='0.1',
          author='Paul Metcalfe',
          author_email='paul.metcalfe+defode@gmail.com',
          description='Declarative definition of systems of ordinary differential equations',
          long_description=long_description,
          classifiers=[
              "Development Status :: 4 - Beta",
              "Intended Audience :: Science/Research",
              "Operating System :: OS Independent",
              "Topic :: Scientific/Engineering :: Mathematics",
              "Topic :: Software Development :: Code Generators"
              ],
          license='License :: OSI Approved :: BSD License')


if __name__ == '__main__':
    main()
