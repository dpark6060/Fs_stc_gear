#!/usr/bin/env python3

import codecs
import glob
import json
import logging
import os
from pathlib import Path
import shutil
import subprocess as sp
import sys

import flywheel

FLYWHEEL = "/flywheel/v0"
INPUT = os.path.join(FLYWHEEL, 'input')
OUTPUT = os.path.join(FLYWHEEL, 'output')


# We'll use this to check if an optional input is present or not
# It turned out not being super useful, but whatever
def check_key(dict, key):
    if key in dict.keys():
        return True
    return False


# Define a little append to run command thing to make the code look a little neater
def append_to_run(call, key, val):
    call += '--{}={} '.format(key, val)
    return (call)


# This is the meat of the code, the function that does logic on the inputs.  Some of the logic is taken care of in the
# filtershift binary itself, but there's still a bit of
def filtershift_input_logic(gear_context):
    config = gear_context.config

    # The start of the run command
    runcmd = '{}/filtershift '.format(FLYWHEEL)

    # Now we'll build our call: Let's start with our required arguments. First check to verify the input was given and
    # exists:

    if gear_context.get_input('NIFTI'):
        nifti = gear_context.get_input_path('NIFTI')

        if not os.path.exists(nifti):
            print('File not found: {}'.format(nifti))
            sys.exit(1)
        else:
            print('File {} exists'.format(nifti))
        runcmd = append_to_run(runcmd, 'in', nifti)
    else:

        # Currently handling all errors with a sys.exit(1).  Any suggestions for more graceful ways would be welcome
        # Also better logging, which I'll use Andy's method for the future.
        print('No input provided')
        sys.exit(1)

    # Now check for the TR.  From here on these have default values so we don't need to check if they exist.
    if config['tr'] <= 0:
        print('TR is required and must be greater than zero')
        sys.exit(1)

    tr = config['tr']
    runcmd = append_to_run(runcmd, 'TR', tr)

    # Now Check For Cutoff Frequency
    cf = config['cf']
    runcmd = append_to_run(runcmd, 'cf', cf)

    # Now we check for HPF/LPF options.  Theses are bool, so
    if config['hpf'] & config['lpf']:
        print('HPF and LPF cannot be called together.')
        sys.exit(1)

    elif config['hpf']:
        runcmd = append_to_run(runcmd, 'hpf', '')

    elif config['lpf']:
        runcmd = append_to_run(runcmd, 'lpf', '')

    # Strictly speaking, if we have a hpf or lpf, we don't need any more input
    # But for completeness, we will go through.

    # Now we build our call: First check to see if we have a slice timing/order file (Most common input types in my opinion)
    has_file = False
    if gear_context.get_input('timing') and gear_context.get_input('order'):
        print('Only a slice timing file OR a slice order file can be provided.  Please choose one.')
        sys.exit(1)

    elif gear_context.get_input('timing'):
        timing = gear_context.get_input_path('timing')
        runcmd = append_to_run(runcmd, 'timing', timing)
        has_file = True

    elif gear_context.get_input('order'):
        order = gear_context.get_input_path('order')
        runcmd = append_to_run(runcmd, 'order', order)
        has_file = True

    # It's possible to select a reference time or slice if using an order file, but not a slice timing file.
    # However, this exception is handled in the code itself, so we don't check for it here.

    if config['reftime'] >= 0:
        runcmd = append_to_run(runcmd, 'reftime', config['reftime'])

    if config['refslice'] > 0:
        runcmd = append_to_run(runcmd, 'refslice', config['refslice'])

    # Now we look at start slice and direction codes
    if not has_file:
        if config['start'] > 0:
            runcmd = append_to_run(runcmd, 'start', config['start'])

        if config['dir'] != 0:
            runcmd = append_to_run(runcmd, 'direction', config['dir'])

    # Check for Axis:
    if config['axis'] != 'z':
        runcmd = append_to_run(runcmd, 'axis', config['axis'])

    # Check for hires:
    if config['hires']:
        runcmd = append_to_run(runcmd, 'hires', '')

    return (runcmd)


def main():

    with flywheel.GearContext() as gear_context:
        # Initialize logging
        log = logging.getLogger('[flywheel/fs-stc]')
        gear_context.init_logging(level='INFO')
        # Check for that dummy file made in the docker.  Nothing to do with function of the gear.
        log.info(glob.glob('{}/*'.format(FLYWHEEL)))


        runcmd = filtershift_input_logic(gear_context)

        # Now we can finally make the call:
        #First load the environment to be passed to sp.Popen:
        with open('/tmp/gear_environ.json', 'r') as f:
            environ = json.load(f)

        log.info(runcmd)

        # Shamelessly copied from Josh.  Still not 100% on handling stdout and stderr.
        result = sp.Popen(runcmd, stdout=sp.PIPE, stderr=sp.PIPE,
                          universal_newlines=True, env=environ, shell=True)

        stdout, stderr = result.communicate()
        log.debug(stdout)
        if result.returncode != 0:
            log.info(stderr)
            raise Exception(stderr)

        # If the run was succesful, the output will be the same file as the input with "_st" appended to the end.from
        # So we work some extension manipulation to tweak that out.  Hopefully there are no "."'s ever in the filename
        # aside from the extension...Are there?
        nifti = gear_context.get_input_path('NIFTI')
        suffixes = Path(nifti).suffixes
        filebase = nifti.rsplit('.')[0]
        output_nifti = filebase + '_st'
        for i in suffixes:
            output_nifti += i
        if not os.path.isfile(output_nifti):
            log.error('Expected output file does not exist: {}'.format(output_nifti))
            log.error('Exiting...')
            os.sys.exit(1)
        # Check for output directory and make it if it's not there
        flywheel_output = gear_context.output_dir
        if not os.path.exists(flywheel_output):
            os.mkdir(flywheel_output)

        # Copy the output file to the appropriate output directory
        shutil.copy2(output_nifti, flywheel_output)


# This could all be smarter, especially with error/exception handling.
if __name__ == "__main__":
    main()
