#!/usr/bin/env python
import sys, os
import argparse
import subprocess
import time
import shutil
import tempfile

OKAY = 0

def Print(*objects, **kwargs):
    sep = kwargs.get('sep', ' ')
    end = kwargs.get('end', '\n')
    out = kwargs.get('file', sys.stderr)
    t = time.strftime('[%F %R:%S] ', time.localtime())
    out.write(t + sep.join(objects) + end)
    os.write(TEMP_LOG_FD, t + sep.join(objects) + end)

def init_args(args):
    # Init argparse
    parser = argparse.ArgumentParser()

    parser.add_argument('initial', nargs='?', help='initial device ROM image, ensure that can boot to home and download mode')
    parser.add_argument('test', nargs='*', help='to-be-test device ROM images, ensure those updates can boot to home and download mode')
    parser.add_argument('-c', metavar='command', default=None, help='Fastboot commands')
    parser.add_argument('-s', metavar='serialno', default=None, help='Device\'s serial number')
    parser.add_argument('--title', '-t', default='The test', help='Test title string')
    parser.add_argument('--fastboot-path', '-f', metavar='PATH', default=None, help='Google fastboot tool path')
    parser.add_argument('--htc-fastboot-path', '-F', metavar='PATH', default=None, help='HTC fastboot tool path')
    parser.add_argument('--adb-path', '-a', metavar='PATH', default=None, help='Google adb tool path')

    return parser.parse_args(args)

G_FASTBOOT = 'fastboot'
H_FASTBOOT = 'htc_fastboot'
G_ADB = 'adb'
X_PARAMS = []
LOG_PATH = None
TEMP_LOG_FD = None
TEMP_LOG_PATH = None

def init_logger():
    global LOG_PATH, TEMP_LOG_FD, TEMP_LOG_PATH
    LOG_PATH = time.strftime('%Y-%m-%d_%H-%M-%S', time.localtime()) + '_dlz_test.txt'
    TEMP_LOG_FD, TEMP_LOG_PATH = tempfile.mkstemp()

def finalized_logger():
    global LOG_PATH, TEMP_LOG_PATH
    os.close(TEMP_LOG_FD)
    shutil.move(TEMP_LOG_PATH, LOG_PATH)

def setup_tools(google, htc, adb, sn):
    global G_FASTBOOT, H_FASTBOOT
    if google: G_FASTBOOT = google
    if htc: H_FASTBOOT = htc
    if adb: G_ADB = adb
    if sn: X_PARAMS += sn

def assert_process(title, func, *args):
    Print('>>> ' + title)
    assert func(*args) == OKAY, 'Failed: ' + title
    Print('<<< Passed: ' + title)

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

def _reboot_with_params(tool, params, **kwargs):
    command = [tool]
    command.extend(X_PARAMS)
    command.extend(params)
    timeout = kwargs.get('timeout', 2)
    log, ret = _run(command)
    if ret == OKAY:
        time.sleep(timeout)
    return ret

def _a_reboot_download():
    return _reboot_with_params(G_ADB, ['reboot', 'oem-e0'], timeout=5)

def _f_reboot_download():
    return _reboot_with_params(H_FASTBOOT, ['oem', 'reboot-download'])

def _reboot_download():
    ret = OKAY
    if _a_reboot_download() != OKAY:
        ret = _f_reboot_download()
    return ret

def _f_reboot_os():
    return _reboot_with_params(H_FASTBOOT, ['reboot'])

def _do_flash(partition, rom):
    command = [H_FASTBOOT]
    command.extend(X_PARAMS)
    command.extend(['-d', 'flash', partition, rom])

    log, ret = _run(command)
    if 'hboot pre-update!' in log:
        Print('Automatically restart fastboot for preupdating ...');
        time.sleep(10)
        return _do_flash(partition, rom)
    return ret

def _do_command(cmds):
    command = [G_FASTBOOT]
    command.extend(X_PARAMS)
    command.extend(cmds)

    log, ret = _run(command)
    return ret

def _wait_for_boot():
    command = [G_ADB]
    command.extend(X_PARAMS)
    command.extend(['wait-for-device', 'logcat', '-d', 'ActivityManager:I'])

    log, ret = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT).communicate()
    if 'android.intent.action.BOOT_COMPLETED' in log:
        return OKAY
    else:
        time.sleep(2)
    return _wait_for_boot()

def get_partition_name(rom):
    if rom.endswith('zip'):
        return 'zip'
    return os.path.split(os.path.splitext(rom)[0])[1]

#Tests
def update(title, rom, partition, **kwargs):
    reboot = kwargs.get('reboot', False)
    reboot_download = kwargs.get('reboot_download', False)

    Print('### ' + title)

    assert_process('Flash %s %s' % (partition, rom), _do_flash, partition, rom)

    if reboot:
        assert_process('Reboot to OS', _f_reboot_os)
        assert_process('Waiting boot completed...', _wait_for_boot)
    if reboot_download:
        assert_process('Reboot to HTC DLM', _reboot_download)

    return OKAY

def main(args):
    Opts = init_args(args)

    setup_tools(Opts.fastboot_path, Opts.htc_fastboot_path, Opts.s, Opts.adb_path)

    init_logger()

    Print("*** Reboot Device")
    _reboot_download()

    if Opts.c:
        _do_command(Opts.c.split(' '))

    if Opts.initial:
        update(Opts.title, Opts.initial, get_partition_name(Opts.initial), reboot=True, reboot_download=True)

    if Opts.test and len(Opts.test) > 0:
        for rom in Opts.test[0:-1]:
            update(Opts.title, rom, get_partition_name(rom), reboot=False, reboot_download=False)
        rom = Opts.test[-1]
        update(Opts.title, rom, get_partition_name(rom), reboot=True, reboot_download=True)

    finalized_logger();

if __name__ == '__main__':
    main(sys.argv[1:])
