#!/usr/bin/env python
import logging
import logging.handlers
import re
import subprocess
import time


logging.getLogger(__name__).addHandler(logging.handlers.SysLogHandler('/dev/log'))
log = logging.getLogger(__name__)


WIRELESS_INTERFACES = ('wlan0', )
WIRED_INTERFACES = ('eth0', 'eth1', 'eth2')
ETHTOOL_CMD = subprocess.Popen(
    'which \ethtool', shell=True, stdout=subprocess.PIPE).communicate()[0].strip()
DHCLIENT_CMD = subprocess.Popen(
    'which \dhcpcd', shell=True, stdout=subprocess.PIPE).communicate()[0].strip()
IFCONFIG_CMD = subprocess.Popen(
    'which \ifconfig', shell=True, stdout=subprocess.PIPE).communicate()[0].strip()


def ethtool_cmd(args):
    assert args.index  # iterable
    result, _ = subprocess.Popen(
        [ETHTOOL_CMD, ] + list(args), shell=False, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE).communicate()
    return result.strip()


def dhclient_cmd(args):
    assert args.index  # iterable
    result, _ = subprocess.Popen(
        [DHCLIENT_CMD, ] + list(args), shell=False, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE).communicate()
    return result.strip()


def ifconfig_cmd(args):
    assert args.index  # iterable
    result, _ = subprocess.Popen(
        [IFCONFIG_CMD, ] + list(args), shell=False, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE).communicate()
    return result.strip()

def get_ip_address(res):
    gr = re.search("inet (?P<ipaddr>[0-9.]+) ", res, re.MULTILINE)
    if gr:
        return gr.group('ipaddr')
    else:
        return None

def wired_interface_statuses(interfaces, active_only=False):
    def get_link_status(res):
        gr = re.search("Link detected: (?P<link>.+)", res, re.MULTILINE)
        if gr:
            return gr.group('link')
        else:
            return None
    results = {}
    for iface in interfaces:
        ifconfig_cmd((iface, 'up'))  # ensure interface is up
        status = get_link_status(ethtool_cmd((iface, )))
        ipaddr = get_ip_address(ifconfig_cmd((iface, )))
        # yes = up and configured
        # no = up but not configured
        # None = not up, not configured
        if all((status == 'yes', ipaddr)):
            results[iface] = 'yes'
        elif not active_only or status is not None:
            results[iface] = 'no' if status == 'yes' else None
    return results


def wireless_interface_statuses(interfaces, active_only=False):
    def get_link_status(res):
        entry = [r for r in res.splitlines() if not r.startswith('Iface')]
        if entry:
            flags = entry[0].split()[10]
            if 'U' in flags:  # interface is 'up'
                return 'yes'
            else:
                return 'no'
        else:
            return None
    results = {}
    for iface in interfaces:
        status = get_link_status(ifconfig_cmd(('-s', iface, )))
        ipaddr = get_ip_address(ifconfig_cmd((iface, )))
        if status == 'yes' and ipaddr:
            results[iface] = 'yes'
        elif not active_only or status is not None:
            results[iface] = 'no' if status else None
    return results


def disable_wireless():
    log.info("Shutting down wireless")
    for iface in WIRELESS_INTERFACES:
        dhclient_cmd(('-k', iface))


def disable_wired():
    log.info("Shutting down wired")
    for iface in WIRED_INTERFACES:
        dhclient_cmd(('-k', iface))


def configure_interface(iface):
    log.info("Bringing up %s", iface)
    ifconfig_cmd((iface, 'up'))
    dhclient_cmd((iface, ))


def auto_configure():
    active_wired = wired_interface_statuses(WIRED_INTERFACES, active_only=True)
    for iface, status in active_wired.items():
        if status == 'yes':
            # already configured, nothing to do
            return iface
        elif status == 'no':
            # disable wireless and bring up wired
            disable_wireless()
            configure_interface(iface)
            return iface
        else:
            log.error("Skipping wired interface with unknown status: %s %s",
                      iface, status)

    # fall back to wireless
    active_wless = wireless_interface_statuses(WIRELESS_INTERFACES)
    for iface, status in active_wless.items():
        if status == 'yes':
            # already configured, nothing to do
            return iface
        elif status == 'no':
            disable_wired()
            configure_interface(iface)
            return iface
        else:
            log.error("Skipping wless interface with unknown status: %s %s",
                      iface, status)


def monitor():
    while 1:
        auto_configure()
        time.sleep(5)

if __name__ == '__main__':
    monitor()
