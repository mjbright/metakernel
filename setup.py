try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup
import sys


svem_flag = '--single-version-externally-managed'
if svem_flag in sys.argv:
    # Die, setuptools, die.
    sys.argv.remove(svem_flag)


with open('metakernel/__init__.py', 'rb') as fid:
    for line in fid:
        line = line.decode('utf-8')
        if line.startswith('__version__'):
            version = line.strip().split()[-1][1:-1]
            break


setup(name='metakernel',
      version=version,
      description='Metakernel for Jupyter [forked from https://github.com/Calysto/metakernel]',
      long_description=open('README.rst', 'rb').read().decode('utf-8'),
      author='Steven Silvester',
      author_email='steven.silvester@ieee.org',
      url="https://github.com/mjbright/metakernel",
      install_requires=['IPython>=3.0'],
      packages=['metakernel', 'metakernel.magics', 'metakernel.utils',
                'metakernel.tests', 'metakernel.magics.tests'],
      include_data_files = True,
      data_files = [("./metakernel/images", ["metakernel/images/logo-64x64.png", 
                                           "metakernel/images/logo-32x32.png"]),
                    ("rcfiles", ["metakernel_bash/metakernelrc", "metakernel_bash/metakernelrc.user",
                                 "metakernel_bash/alert.js.template",
                                 "metakernel_bash/d3_pie.js.template"
                                ])
                   ],
      classifiers=[
          'Framework :: IPython',
          'License :: OSI Approved :: BSD License',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 2',
          'Programming Language :: Scheme',
          'Topic :: System :: Shells',
      ]
      )
