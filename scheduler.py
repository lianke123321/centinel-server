#!/usr/bin/env python
#
# Georgia Tech Spring 2014
#
# scheduler.py: script to manage experiments and data by finding
# appropriate clients, copying files into those directories, and
# potentially modifying the scheduling frequency information
#
# Note: you *MUST NOT* start more than 1 instance of this program at
# the same time. Doing so could cause race conditions in our scheduler
# and could result in your experiments not being run at the expected
# frequency


import argparse
from datetime import datetime, timedelta
import json
import os
import os.path
import sys


import config
from centinel.models import Client


def parse_args():
    parser = argparse.ArgumentParser()
    country_help = ('Two letter country code of the country to run the'
                    'experiment in')
    parser.add_argument('--country', '-c', help=country_help, required=True)
    client_help = ("Number of clients in the country to run the measurement "
                   "on. If this is not specified, the experiment will be "
                   "scheduled on all clients in the country")
    parser.add_argument('--num-clients', '-n', help=client_help, default=None)
    data_help = ("Data file for the clients to use. Note that this must be "
                 "paired with an experiment file that has the same name "
                 "(specified at the top of the class in the experiment file)")
    parser.add_argument('--data', '-d', help=data_help, default=None)
    exp_help = ("Experiment file for the clients to use. This should be a "
                "Python file following the format as other experiments "
                "(see the example template or ping.py for how to do this)")
    parser.add_argument('--experiment', '-e', help=exp_help, default=None)
    freq_help = ("How often the experiment should be run in minutes, i.e. "
                 "enter 60 to run the experiment every hour. If no "
                 "frequency information is specified, the measurement will "
                 "run every time the client does a measurement")
    parser.add_argument('--frequency', '-f', help=freq_help, default=None)
    remove_help = ("Remove the experiment or data file with the specified "
                   "name from the target clients. Note that this option will "
                   "be applied to both data and experiments if both the -d "
                   "and -e options are specified")
    parser.add_argument('--remove', '-r', help=remove_help, default=False,
                        action='store_true')
    args = parser.parse_args()

    if args.frequency is not None and args.experiment is None:
        parser.error("Specifying the frequency is only a valid option if you "
                     "are specifying an experiment to run. You must specify "
                     "a new experiment to schedule as well with the -e option")
    return args


def find_clients(country, num_clients):
    """Find num_clients active clients in the target country

    Params:
    country- two letter country code of target country
    num_clients- number of clients to get. If this is None, then we
        get all the active clients for that country

    Note: we define active here as having seen the client in the past
    month

    """
    clients = []
    potential_clients = Client.query.filter_by(country=country).all()
    month_diff = timedelta(days=30)
    for client in potential_clients:
        if client.last_seen < datetime.now() - month_diff:
            continue
        if num_clients is not None and len(clients) >= num_clients:
            continue
        clients.append(client.username)
    return clients


def copy_data(clients, data):
    """Copy the given data file so that it gets used by the clients

    Params:
    clients- the clients to copy the data file to
    data- the data file to copy into each user's directory

    """
    if not os.path.exists(data):
        print "Error: invalid data file to copy from"
        return
    with open(data, 'r') as file_p:
        content = file_p.read()
    basename = os.path.basename(data)
    for client in clients:
        filename = os.path.join(config.inputs_dir, client, basename)
        with open(filename, 'w') as file_p:
            file_p.write(content)


def remove_data(clients, data):
    """Remove the given data file so that it does not get used by the clients

    Params:
    clients- the clients to copy the data file to
    data- the data file basename to remove

    """
    data = os.path.basename(data)
    for client in clients:
        filename = os.path.join(config.inputs_dir, client, data)
        if os.path.exists(filename):
            os.remove(filename)


def copy_exps(clients, exp):
    """Copy the given experiment so that it gets used by the clients

    Params:
    clients- the clients to copy the data file to
    exp- the experiment to copy into each user's directory

    """
    if not os.path.exists(exp):
        print "Error: invalid experiment to copy from"
        return
    with open(exp, 'r') as file_p:
        content = file_p.read()
    basename = os.path.basename(exp)
    for client in clients:
        filename = os.path.join(config.experiments_dir, client, basename)
        with open(filename, 'w') as file_p:
            file_p.write(content)


def remove_exps(clients, exp):
    """Remove the given experiment so that it does not get used by the clients

    Params:
    clients- the clients to copy the data file to
    exp- the experiment file basename to remove

    """
    basename = os.path.basename(exp)
    for client in clients:
        filename = os.path.join(config.experiments_dir, client, basename)
        if os.path.exists(filename):
            os.remove(filename)


def copy_frequency(clients, freq, exp):
    """Schedule the given experiment to run at the frequency specified

    Params:
    clients- the clients to update the frequencies for
    freq- how many minutes should elapse between runs, i.e. enter 60 to
        run every hour
    exp- the experiment to adjust the frequency for

    """
    exp_name, _ = os.path.splitext(os.path.basename(exp))
    for client in clients:
        # if the experiment doesn't exist for that user, then don't
        # adjust the frequency
        exp_file = os.path.join(config.experiments_dir, client, exp)
        if not os.path.exists(exp_file):
            continue
        filename = os.path.join(config.experiments_dir, client,
                                "scheduler.info")
        freqs = {}
        if os.path.exists(filename):
            with open(filename, 'r') as file_p:
                freqs = json.load(file_p)
        freqs[exp_name] = {'last_run': 0, 'frequency': int(freq) * 60}
        # Note: as mentioned in the first few introductory lines, this
        # section presents a race condition if another instance of the
        # scheduler is running at the same time and your experiment
        # may not be scheduled
        with open(filename, 'w') as file_p:
            json.dump(freqs, file_p)


def remove_frequency(clients, exp):
    """Remove the given experiment from the scheduler

    Params:
    clients- the clients to update the frequencies for
    exp- the experiment to adjust the frequency for

    """
    exp = os.path.basename(exp)
    for client in clients:
        filename = os.path.join(config.experiments_dir, client,
                                "scheduler.info")
        freqs = {}
        if os.path.exists(filename):
            with open(filename, 'r') as file_p:
                freqs = json.load(file_p)
        if freqs.get(exp) is not None:
            del freqs[exp]
        if freqs == {}:
            os.remove(filename)
            return
        # Note: as mentioned in the first few introductory lines, this
        # section presents a race condition if another instance of the
        # scheduler is running at the same time and your experiment
        # may not be scheduled
        with open(filename, 'w') as file_p:
            json.dump(freqs, file_p)


if __name__ == "__main__":
    # Note: the argument parser takes care of default values for us,
    # so we don't need to specify default values
    args = parse_args()

    # lookup the clients/ probes to use
    clients = find_clients(args.country, args.num_clients)

    # print the clients and return if we are not copying any files over
    if args.experiment is None and args.data is None:
        print ("You have not specified a data file or experiment to run on "
               "the clients, so I will just print the clients usernames that "
               "you would have scheduled experiments on")
        for client in clients:
            print "{0}".format(client)
        sys.exit(0)

    # copy the data files if necessary
    if args.data is not None:
        if args.remove:
            remove_data(clients, args.data)
        else:
            copy_data(clients, args.data)

    # copy the experiment files if necessary
    if args.experiment is not None:
        if args.remove:
            remove_exps(clients, args.experiment)
            remove_frequency(clients, args.experiment)
        else:
            copy_exps(clients, args.experiment)

    # add the frequency info as appropriate
    if not args.remove and args.frequency is not None:
        copy_frequency(clients, args.frequency, args.experiment)
