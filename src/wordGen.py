#Generates output of American English words to a given size, notably truncating
#to fit if necessary.

#####  imports  #####
import sys
import os
import argparse
import string
import random
import json

#####  package variables  #####

#The great thing about dictionaries defined at the package level is their global
#(public-like) capability, avoiding constant passing down to 'lower' defs.
params_dict = {'cfg' : '../cfg/default_config.json'}


#####  class definitions  #####





#####  package functions  #####
def loadConfig(cfg_path):
    """Updates the global dictionary with the supplied configuration, if it
       exists, and creates the output directory.

       Input : cfg_path : optional CLI input to the json config file

       output : None.
    """
    global params_dict

    if cfg_path :
        params_dict['cfg'] = cfg_path

    #Sure this is a little sloppy but we don't need the config after this so
    #there's no reason to keep the old definition anyways and cause an if split
    #in the code.
    with open(params_dict['cfg']) as json_file:

        params_dict = json.load(json_file)
        os.makedirs(params_dict['out_dir'], mode=0o664, exist_ok=True)

        print(f"{params_dict['just_spaces']}, {params_dict['block_aligned']}")
    

def genWords():
    print("stupid Paython")


#####  main  #####
def main():
    print("Starting?\r\n")
    parser = argparse.ArgumentParser(
                description="Generates a set of output text strings based on \
                             the input parameters.  This includes special \
                             character insertion and randomization.")
    parser.add_argument('--config', help='Optional path to the config file.')

    args = parser.parse_args()
#    try:
    loadConfig(args.config)
    genWords()
#    except Exception as err:
#        print(f"Encountered {err=}, {type(err)=}")

    print(f"Args: {args.config}\r\n")

if __name__ == '__main__':
    main()

#--One config file to define how the parameters are randomized
#-- Option to include special characters
#--Option to limit max word count
#--option to randomize parameters (number of words per newline, number of spaces/returns)

