#!/usr/bin/env python

from netmiko import Netmiko
import argparse
import re
from argparse import RawTextHelpFormatter
import getpass
from datetime import datetime
import multiprocessing as mp


def ssh_session(device_type, ip, commandfile, username, password):
    try:
        ssh = Netmiko(device_type=device_type, ip=ip, username=username, password=password)
        print()
        print('----- Connected to {} {} -----'.format(ip, datetime.now().time()))
        print()
        if args.mode == 'show':
            # open command file
            with open(commandfile) as c:
                # read, split into lines, iterate over lines and send to ssh session
                for command in c.read().splitlines():
                    output = ssh.send_command(command)
                    # if -w given at command line write to file
                    if args.write:
                        with open('{}.txt'.format(ip), 'a') as logg:
                            logg.write('Command: {}'.format(command))
                            logg.write('\n\n')
                            logg.write(output)
                            logg.write('\n\n')
                    # if -s not given at command line print output to screen
                    if args.out:
                        print('Command: ' + command)
                        print()
                        print(output)
                        print()
        # if -m config is passed at command line
        elif args.mode == 'config':
            # send commands from file to ssh session * automatically splits
            output = ssh.send_config_from_file(commandfile)
            # if -w passed at command line
            if args.write:
                # write output of commands to file named after host
                with open('{}.txt'.format(ip), 'a') as logg:
                    logg.write('Configuration Changes:')
                    logg.write('\n\n')
                    logg.write(output)
            # if -s not passed at command line output commands to screen
            if args.out:
                print('Configuration Changes:')
                print()
                print(output)
                print()
        # close ssh session
        ssh.disconnect()
        print('----- Disconnected From {} {} -----'.format(ip, datetime.now().time()))
        print()
    except Exception as e:
        print('----- Error connecting to {} {} -----'.format(ip, datetime.now().time()))
        print(e)
        print()
        with open('error.txt', 'a') as error:
            error.write('----- {} {} {} -----'.format(ip, e, datetime.now().time()))


def main(hostfile):
    # retrieve username from local host and prompt for password
    username = getpass.getuser()
    print()
    print('Username: ' + username)
    password = getpass.getpass()
    pool = mp.Pool(processes=args.procs)
    # open hostfile
    with open(hostfile) as h:
        # read the hostfile, split into lines and iterate over lines
        for host in h.read().splitlines():
            # create regxex to match components of host file example - 'router1.location:cisco_ios'
            regx = re.search('^(.*):(cisco_ios|cisco_xr|cisco_nxos|cisco_asa)', host)
            # ensure lines match regxex and are not empty
            if regx:
                pool.apply_async(ssh_session, args=(regx.group(2), regx.group(1), args.commandfile, username, password))
            else:
                print()
                print('----- Skipping blank or malformated Host File entry "{}" {} -----'.format(host, datetime.now().time()))
                print()
    pool.close()
    pool.join()


# create command line argument structure
parser = argparse.ArgumentParser(
    description='\t\tCOMMANDER\n\n Host File Format: core1.smq:cisco_ios\n\n Host Types: cisco_ios, cisco_nxos, cisco_xr, cisco_asa\n\n Example Usage: commander -m show -rf hosts.txt -cf show_commands.txt',
    formatter_class=RawTextHelpFormatter)
parser.add_argument('-m', dest='mode', help='"show" or "config" defaults to show if no option given', type=str,
                    default='show')
parser.add_argument('-hf', dest='hostfile', help='file containing hosts and type one per line', required=True)
parser.add_argument('-cf', dest='commandfile', help='file containing commands one per line', required=True)
parser.add_argument('-p', dest='procs', help='number of parallel processes default 10', type=int, default=10)
parser.add_argument('-w', dest='write', help='write output to file per device', action='store_true')
parser.add_argument('-o', dest='out', help='output to screen', action='store_true')
args = parser.parse_args()

# run main function with passed arguments
if __name__ == '__main__':
    main(args.hostfile)
