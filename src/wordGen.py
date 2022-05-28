#Generates output of American English words to a given size, notably truncating
#to fit if necessary.

import sys
import os
import argparse
import string
import random

class wordGen:

    def __init__(self):
        """Does this acutally need one though?  Probably just read the dict
           into memory (who needs RAM anyways?)"""
        #Defaults generate loosely 'norma' looking text.

#The great thing about dictionaries defined at the script level is their global
#(public-like) capability, avoiding constant passing down to 'lower' defs.
params_dict = {'cfg' : ''}


def loadConfig(cfg_path):

    if str != 'None':
        params_dict['cfg'] = cfg_path
        print(f"it's here: {params_dict['cfg']}")


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

