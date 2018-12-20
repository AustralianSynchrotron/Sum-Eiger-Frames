#!/usr/bin/env python3.6
__author__='Daniel Eriksson'
__copyright__='2018 ANSTO'
__licence__='BSD3'
__version__='0.9'
__email__='daniel.eriksson@ansto.gov.au'


from plot_eiger_sums import Plotter
import subprocess

if __name__ == '__main__':
  '''Sum Eiger frames'''
  command = './sum_eiger_frames.py'
  subprocess.call(command)

  '''Plot results'''
  p = Plotter()
  p.run()

