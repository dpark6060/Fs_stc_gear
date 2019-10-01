#!/usr/bin/env python3

import codecs, json, sys, os
import subprocess as sp
import glob,shutil
from pathlib import Path

FLYWHEEL="/flywheel/v0"
INPUT=os.path.join(FLYWHEEL,'input')
OUTPUT=os.path.join(FLYWHEEL,'output')

# We'll use this to check if an optional input is present or not
def Check_key(dict, key):
    if key in dict.keys():
        return True
    return False


# Define a little append to run command thing to make the code look a little neater
def Append_to_run(call, key, val):
    call += '--{}={} '.format(key, val)
    return (call)


print(glob.glob('{}/*'.format(FLYWHEEL)))

#shutil.copy2('{}/config.json'.format(FLYWHEEL),'{}/output/config.json'.format(FLYWHEEL))


invocation = json.loads(open('config.json').read())
config = invocation['config']
inputs = invocation['inputs']
destination = invocation['destination']

runcmd = '{}/filtershift '.format(FLYWHEEL)

# Now we'll build our call: Let's start with our required arguments. First check to verify the input was given and
# exists:

if Check_key(inputs, 'input'):
    input = inputs['input']['location']['path']

    if not os.path.exists(input):
        print('File not found: {}'.format(input))
        sys.exit(1)
    else:
        print('File {} exists'.format(input))
    runcmd = Append_to_run(runcmd, 'in', input)
else:
    print('No input provided')
    sys.exit(1)

# Now check for the TR.  From here on these have default values so we don't need to check if they exist.
if config['tr'] <= 0:
    print('TR is required and must be greater than zero')
    sys.exit(1)
tr = config['tr']
runcmd = Append_to_run(runcmd, 'TR', tr)

# Now Check For Cutoff Frequency
cf = config['cf']
runcmd = Append_to_run(runcmd, 'cf', cf)

# Now we check for HPF/LPF options.  Theses are bool, so
if config['hpf'] & config['lpf']:
    print('HPF and LPF cannot be called together.')
    sys.exit(1)
elif config['hpf']:
    runcmd = Append_to_run(runcmd, 'hpf', '')
elif config['lpf']:
    runcmd = Append_to_run(runcmd, 'lpf', '')

# Strictly speaking, if we have a hpf or lpf, we don't need any more input
# But for completeness, we will go through.

# Now we build our call: First check to see if we have a slice timing/order file (Most common input types in my opinion)
Has_file = False
if Check_key(inputs, 'timing') & Check_key(inputs, 'order'):
    print('Only a slice timing file OR a slice order file can be provided.  Please choose one.')
    sys.exit(1)

elif Check_key(inputs, 'timing'):
    timing = inputs['timing']['location']['path']
    runcmd = Append_to_run(runcmd, 'timing', timing)
    Has_file = True

elif Check_key(inputs, 'order'):
    order = inputs['order']['location']['path']
    runcmd = Append_to_run(runcmd, 'order', order)
    Has_file = True

# It's possible to select a reference time or slice if using an order file, but not a slice timing file.
# However, this exception is handled in the code itself

if config['reftime'] >= 0:
    runcmd = Append_to_run(runcmd, 'reftime', config['reftime'])

if config['refslice'] > 0:
    runcmd = Append_to_run(runcmd, 'refslice', config['refslice'])

# Now we look at start slice and direction codes
if not Has_file:
    if config['start'] > 0:
        runcmd = Append_to_run(runcmd, 'start', config['start'])

    if config['dir'] != 0:
        runcmd = Append_to_run(runcmd, 'direction', config['dir'])

# Check for Axis:
if config['axis'] != 'z':
    runcmd = Append_to_run(runcmd, 'axis', config['axis'])

# Check for hires:
if config['hires']:
    runcmd = Append_to_run(runcmd, 'hires', '')

# Now we can finally make the call:
with open('/tmp/gear_environ.json', 'r') as f:
    environ = json.load(f)

print(runcmd)
result = sp.Popen(runcmd, stdout=sp.PIPE, stderr=sp.PIPE,
                  universal_newlines=True, env=environ, shell=True)

stdout, stderr = result.communicate()
print(stdout)
if result.returncode != 0:
    print(stderr)
    raise Exception(stderr)

suffixes=Path(input).suffixes
filebase=input.rsplit('.')[0]
output=filebase+'_st'
for i in suffixes:
    output+=i

Flywheel_output=os.path.join(FLYWHEEL,'output')
if not os.path.exists(Flywheel_output):
    print('No Such output directory \n {}'.format(Flywheel_output))
    sys.exit(1)

shutil.copy2(output, Flywheel_output)
shutil.copy('/tmp/gear_environ.json',Flywheel_output)

