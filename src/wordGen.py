#Generates output of American English words to a given size, notably truncating
#to fit if necessary.

import sys
import os
import argparse
import string
import random
import json


#The great thing about dictionaries defined at the script level is their global
#(public-like) capability, avoiding constant passing down to 'lower' defs.
params_dict = {'cfg' : 'cfg.json'}


def loadConfig(cfg_path):

    global params_dict

    if cfg_path :
        params_dict['cfg'] = cfg_path
        print(f"it's here: {params_dict['cfg']} from {cfg_path}")

    #Sure this is a little sloppy but we don't need the config after this
    #so there's no reason to keep the old definition anyways and cause an
    #if split in the code.
    with open(params_dict['cfg']) as json_file:
        params_dict = json.load(json_file)
        
        print(f"{params_dict['just_spaces']}, {params_dict['block_aligned']}")


def main():
    print("Starting?\r\n")
    parser = argparse.ArgumentParser(
                description="Generates a set of output text strings based on \
                             the input parameters.  This includes special \
                             character insertion and randomization.")
    parser.add_argument('--config', help='Path to the config file.')
    parser.add_argument('-out', default ='out.txt',
                         help='output file path, defaults to out.txt')

    args = parser.parse_args()
#    try:
    loadConfig(args.config)
#    except Exception as err:
#        print(f"Encountered {err=}, {type(err)=}")
#Convert to global dict here?
    print(f"Args: {args.config}\r\n  \
                  {args.out}\r\n")

if __name__ == '__main__':
    main()

#--One config file to define how the parameters are randomized
#-- Option to include special characters
#--Option to limit max word count
#--option to randomize parameters (number of words per newline, number of spaces/returns)

