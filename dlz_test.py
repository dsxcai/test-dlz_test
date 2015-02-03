#!/bin/usr/env python

import sys, os
import argparse
import subprocess

def Printf(*objects, **kwargs):
  sep = kwargs.get('sep', ' ')
  end = kwargs.get('end', '\n')
  out = kwargs.get('file', sys.stdout)
  out.write(sep.join(objects) + end)

def init_args(args):
  # Init argparse
  parser = argparse.ArgumentParser()

  parser.add_argument('current', help='current device ROM image')
  parser.add_argument('test', help='to-be-test device ROM image')
  parser.add_argument('--fastboot-path', '-f', metavar='PATH', default=None, help='Google fastboot tool path')
  parser.add_argument('--htc-fastboot-path', '-F', metavar='PATH', default=None, help='HTC fastboot tool path')
  
  return parser.parse_args(args)

G_FASTBOOT = 'fastboot'
H_FASTBOOT = 'htc_fastboot'
CURR_ROM = None
TEST_ROM = None

def set_tools_path(google, htc):
  global G_FASTBOOT, H_FASTBOOT
  if google: G_FASTBOOT = google
  if htc: H_FASTBOOT = htc

def set_roms_path(curr, test):
  global CURR_ROM, TEST_ROM
  CURR_ROM, TEST_ROM = curr, test

def Start_test(*tests, **kwargs):
  for i in tests:
    i(kwargs)

#Tests
def up_down_test(kwargs):
  print '3.1.1 Upgrade-Downgrade'
  print kwargs

def test2(kwargs):
  print 'test2'
  print kwargs

def main(args):
  Opts = init_args(args)
  
  if not Opts.current or not Opts.test:
    parser.error('incorrect number of arguments')

  set_tools_path(Opts.fastboot_path, Opts.htc_fastboot_path)
  set_roms_path(Opts.current, Opts.test)

  Start_test(test1, test2)

if __name__ == '__main__':
  main(sys.argv[1:])

