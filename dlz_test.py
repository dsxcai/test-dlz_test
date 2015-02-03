#!/bin/usr/env python

import sys, os
import argparse
import subprocess
import time

def Print(*objects, **kwargs):
  sep = kwargs.get('sep', ' ')
  end = kwargs.get('end', '\n')
  out = kwargs.get('file', sys.stderr)
  t = time.strftime('[%F %R:%S] ', time.localtime())
  out.write(t + sep.join(objects) + end)

def init_args(args):
  # Init argparse
  parser = argparse.ArgumentParser()

  parser.add_argument('current', help='current device ROM image')
  parser.add_argument('test', help='to-be-test device ROM image')
  parser.add_argument('-s', metavar='SN', default=None, help='Device\'s serial number')
  parser.add_argument('--fastboot-path', '-f', metavar='PATH', default=None, help='Google fastboot tool path')
  parser.add_argument('--htc-fastboot-path', '-F', metavar='PATH', default=None, help='HTC fastboot tool path')
  parser.add_argument('--adb-path', '-a', metavar='PATH', default=None, help='Google adb tool path')
  
  return parser.parse_args(args)

G_FASTBOOT = 'fastboot'
H_FASTBOOT = 'htc_fastboot'
G_ADB = 'adb'
X_PARAMS = []
CURR_ROM = None
TEST_ROM = None

def setup_tools(google, htc, adb, sn):
  global G_FASTBOOT, H_FASTBOOT
  if google: G_FASTBOOT = google
  if htc: H_FASTBOOT = htc
  if adb: G_ADB = adb
  if sn: X_PARAMS += sn

def set_roms_path(curr, test):
  global CURR_ROM, TEST_ROM
  CURR_ROM, TEST_ROM = curr, test

def Start_test(*tests, **kwargs):
  ret = 0
  for i in tests:
    ret = i(kwargs) if ret == 0 else -1
  return ret

def _run(command):
  p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
  log = ''
  while True:
    l = p.stdout.readline()
    if l:
      log += l
      Print(l, end='')
    else:
      break
  out, err = p.communicate()
  if out:
    Print(out, end='')
  return (log, p.returncode)

def _reboot_with_params(params, **kwargs):
  command = [H_FASTBOOT]
  command.extend(X_PARAMS)
  command.extend(params)
  timeout = kwargs.get('timeout', 2)
  log, ret = _run(command)
  time.sleep(timeout)
  return ret

def _f_reboot_download():
  return _reboot_with_params(['oem', 'reboot-download'])

def _f_reboot_os():
  return _reboot_with_params(['reboot'])

def _do_flash(rom):
  command = [H_FASTBOOT]
  command.extend(X_PARAMS)
  command.extend(['-d', 'flash', 'zip', rom])
  log, ret = _run(command)
  if 'hboot pre-update!' in log:
    Print('Automatically restart fastboot for preupdating ...');
    time.sleep(10)
    return _do_flash(rom)
  return ret

def _wait_for_boot():
  command = [G_ADB]
  command.extend(X_PARAMS)
  command.extend(['wait-for-device', 'logcat', '-d', 'ActivityManager:I'])
  log, ret = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT).communicate()
  if 'android.intent.action.BOOT_COMPLETED' in log:
    return ret
  else:
    time.sleep(2)
    return _wait_for_boot()

#Tests
def up_down_test(kwargs):
  ret = 0
  Print('>>> 3.1.1 Upgrade-Downgrade')

  Print('>>> 3.1.1 Flash <CURRENT>')
  ret = _do_flash(CURR_ROM) if ret == 0 else -1
  Print('>>> 3.1.1 Reboot to OS')
  ret = _f_reboot_os() if ret == 0 else -1
  Print('>>> 3.1.1 Waiting boot completed...')
  ret = _wait_for_boot() if ret == 0 else -1
  Print('>>> 3.1.1 Boot completed')
  Print('>>> 3.1.1 Reboot to HTC DLM')
  ret = _f_reboot_download() if ret == 0 else -1

  Print('>>> 3.1.1 Flash <TEST>')
  ret = _do_flash(TEST_ROM) if ret == 0 else -1
  Print('>>> 3.1.1 Reboot to OS')
  ret = _f_reboot_os() if ret == 0 else -1
  Print('>>> 3.1.1 Waiting boot completed...')
  ret = _wait_for_boot() if ret == 0 else -1
  Print('>>> 3.1.1 Boot completed')
  Print('>>> 3.1.1 Reboot to HTC DLM')
  ret = _f_reboot_download() if ret == 0 else -1

  Print('>>> 3.1.1 Flash <CURRENT>')
  ret = _do_flash(CURR_ROM)
  Print('>>> 3.1.1 Reboot to OS')
  ret = _f_reboot_os()
  Print('>>> 3.1.1 Waiting boot completed...')
  ret = _wait_for_boot()
  Print('>>> 3.1.1 Boot completed')

  return ret

def dashboard_rom_test(kwargs):
  Print('>>> 3.1.2 Flash Current Dashboard ROM')
  Print('TBD')

def rcms_rom_test(kwargs):
  Print('>>> 3.1.3 Flash Current RCMS ROM')
  Print('TBD')
  exit(0)

def flash_partition_test(kwargs):
  Print('>>> 3.1.4 Flash Partition')
  Print('TBD')
  exit(0)

def ruu_mode_test(kwargs):
  Print('>>> RUU (ROM Update Utility) Mode')
  Print('TBD')
  exit(0)

def sd_update_test(kwargs):
  Print('>>> 3.2 SD Update')
  Print('TBD')
  exit(0)

def partition_crc_test(kwargs):
  Print('>>> 3.3 Partition Checksum')
  Print('TBD')
  exit(0)

def preupdate_test(kwargs):
  Print('>>> 3.5 OTA update')
  Print('TBD')
  exit(0)

def rcms_rom_test(kwargs):
  Print('>>> 3.6 Verified-Boot')
  Print('TBD')
  exit(0)

def rcms_rom_test(kwargs):
  Print('>>> 3.7 Android-info')
  Print('TBD')
  exit(0)

def main(args):
  Opts = init_args(args)
  
  if not Opts.current or not Opts.test:
    parser.error('incorrect number of arguments')

  setup_tools(Opts.fastboot_path, Opts.htc_fastboot_path, Opts.s, Opts.adb_path)
  set_roms_path(Opts.current, Opts.test)

  ret = Start_test(up_down_test, dashboard_rom_test)
  Print("Return is %d" & ret)

if __name__ == '__main__':
  main(sys.argv[1:])

