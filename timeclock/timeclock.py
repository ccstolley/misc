"""
Simple time keeping script for tracking time worked on a project.

A particular project should have a dedicated user login. That user's
.login and .logout files should have `01clock -i` and `01clock -o`
respectively. Finally, that user's crontab should call the idle
login killer script to prevent over-charging, like so:

*/5  *  *  *  * /usr/local/sbin/kill_idle_logins

"""

from __future__ import print_function
import time
import os
import datetime
import subprocess
from optparse import OptionParser

__version__ = 0.05
TIMECLOCK_FILE = "%s/.01timeclock" % os.environ['HOME']


def write_log(data):
    """
    Write data to the timeclock log file.
    """
    with open(TIMECLOCK_FILE, "a") as f:
        f.write(data + "\n")


def parse_log_entry(ent):
    """
    Returns a dict of a timeclock log file entry.
    """
    (event, epoch_time, stamp) = ent.split()
    return {"event": event,
            "timestamp": int(epoch_time),
            "timestamp_dt": datetime.datetime.fromtimestamp(int(epoch_time)),
            "timestamp_h": stamp}


def last_log_entry():
    """
    Returns the most recently added timeclock log file entry. If
    the logfile is empty, a bogus clockout entry is returned.
    """
    with open(TIMECLOCK_FILE, "r") as f:
        data = f.readlines()
    if data:
        return parse_log_entry(data[-1])
    else:
        return parse_log_entry("OUT 21421123 google")


def multiple_logins():
    """
    Checks if the current user is logged in multiple times. Returns a boolean.
    """
    p = subprocess.Popen(['id', '-un'], stdout=subprocess.PIPE)
    myid = p.communicate()[0].strip()
    p = subprocess.Popen(['w', '-h', myid], stdout=subprocess.PIPE)
    output = p.communicate()[0].splitlines()
    return len(output) > 1


def clock_in():
    """
    Clocks in the current user so he can begin working. This starts
    the timeclock.
    """
    now = int(time.time())
    stamp = datetime.datetime.now().isoformat()
    lle = last_log_entry()
    if lle['event'] == 'IN':
        secs_clocked_in = (now - lle['timestamp'])
        if secs_clocked_in > (now + 60 * 60 * 5):
            print ("WARNING: You are already clocked in for %d hours" %
                   (secs_clocked_in / (60 * 60)))
    else:
        write_log("IN %d %s" % (now, stamp))


def clock_out(force=False):
    """
    Clocks out the current user so that he can stop working. A user
    who is logged in multiple times will not clock out unless
    force=True.
    """
    now = int(time.time())
    stamp = datetime.datetime.now().isoformat()
    if last_log_entry()["event"] != "IN":
        print("ERROR: you must clock in before clocking out.")
    elif force is not True and multiple_logins():
        print("INFO: Not clocking out, still logged in")
    else:
        write_log("OUT %d %s" % (int(now), stamp))


def calculate_daily_totals(datestart, dateend):
    """
    Calculates the hours worked for each day within the time spanned
    by datestart and dateend. Prints results to stdout.
    """

    if datestart is None:
        datestart = datetime.date.today() - datetime.timedelta(days=7)
        dateend = datetime.date.today()
    with open(TIMECLOCK_FILE, "r") as f:
        date_total = 0
        all_time_total = 0
        current_date = None
        last_event = None
        for ent in f:
            entry = parse_log_entry(ent)
            if entry["event"] == "IN":
                last_event = "IN"
                clock_in_time = entry["timestamp"]
                clock_in_date = entry["timestamp_dt"].date()
                if clock_in_date != current_date:
                    if current_date and ((current_date >= datestart) and 
                                         (current_date <= dateend)):
                        print("%s - %.1f hours" % (current_date.isoformat(),
                              date_total / (60.0 * 60)))
                    all_time_total += date_total
                    date_total = 0
                    current_date = clock_in_date
            elif entry["event"] == "OUT":
                last_event = "OUT"
                clock_out_time = entry["timestamp"]
                if not (current_date >= datestart and
                        current_date <= dateend):
                    continue
                else:
                    date_total += clock_out_time - clock_in_time
            else:
                print("Timeclock file parse error.")
                raise SystemExit
        if (current_date >= datestart and current_date <= dateend):
            if last_event == "OUT":
                print("%s - %.1f hours" % (clock_in_date.isoformat(),
                      date_total / (60.0 * 60)))
                all_time_total += date_total
            elif last_event is None:
                print("No records to report.")
            else:
                now = int(time.time())
                print("%s - %.1f (still clocked in)" % (
                    clock_in_date.isoformat(),
                    (((now - clock_in_time) + date_total) / (60.0 * 60))))
                all_time_total += (now - clock_in_time) + date_total
        print("\n%.1f hours total between %s and %s" % (all_time_total/(60.0*60), 
              datestart.isoformat(), dateend.isoformat()))


if __name__ == '__main__':
    import sys
    parser = OptionParser(version=__version__, usage="%prog <options>")
    parser.add_option('-r', '--report', action='store', nargs=2,
        help="Display list of hours between YYYYMMDD and YYYYMMDD",
        dest="report", default=None)
    parser.add_option('-i', '--in', action='store_true', dest="clockin",
        help="Clock in", default=False)
    parser.add_option('-o', '--out', action='store_true', dest="clockout",
        help="Clock out", default=False)
    parser.add_option('-f', '--force', action='store_true',
        help="Force clock out even with multiple logins", dest="force",
        default=False)

    options, args = parser.parse_args(sys.argv)

    funcs = {'in': clock_in,
            'out': clock_out,
            'report': calculate_daily_totals}
    if (not options.report and not options.clockin and not options.clockout):
        if len(args) > 1:
            parser.print_help()
        else:
            calculate_daily_totals(*(None, None))
    elif (options.report):
        fmt = "%Y%m%d"
        try:
            starttime = datetime.datetime.strptime(options.report[0], fmt)
            endtime = datetime.datetime.strptime(options.report[1], fmt)
        except Exception as e:
            print("ERROR: Date ranges must be in YYYYMMDD format.")
            raise SystemExit
        calculate_daily_totals(*(starttime.date(), endtime.date()))
    elif (options.clockout):
        clock_out(options.force)
    elif (options.clockin):
        clock_in()
