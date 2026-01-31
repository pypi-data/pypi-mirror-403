# Set __version__ in the setup.py
with open('scinstr/version.py') as f: exec(f.read())

from setuptools import setup

setup(name='scinstr',
      description='Drivers to handle various scientific instruments (DMM, frequency counter, DAQ, VNA...). Include also some cli script.',
      version=__version__,
      packages=['scinstr.cnt',
                'scinstr.compressor',
                'scinstr.daq',
                'scinstr.daq.labjack',
                'scinstr.dmm',
                'scinstr.lockin',
                'scinstr.phimeter',
                'scinstr.tctrl',
                'scinstr.vacuum',
                'scinstr.vna'],
      install_requires=['pyusb',
                        'PyVISA',
                        'PyVISA-py',
                        'pyserial',
                        'python-usbtmc',
                        'pymodbus'],
      extras_require={
          'Pure_Python_signalslot_facilities': ["signalslot"],
      },
      url='https://gitlab.com/bendub/scinstr',
      author='Benoit Dubois',
      author_email='benoit.dubois@femto-engineering.fr',
      classifiers=[
          'Development Status :: 4 - Beta',
          'Environment :: Console',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: GNU Lesser General Public License v3 or later (LGPLv3+)',
          'Natural Language :: English',
          'Operating System :: POSIX :: Linux',
          'Programming Language :: Python',
          'Topic :: Scientific/Engineering'
          ]
)
