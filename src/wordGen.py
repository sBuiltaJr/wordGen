#Generates output of dictionary-supplied words to a given size, notably
#truncating to fit a given 'block size' if necessary.

#####  imports  #####

import argparse
import json
import multiprocessing as mp
import os
import random
import string
import sys
import time

#####  package variables  #####

#The great thing about dictionaries defined at the package level is their global
#(public-like) capability, avoiding constant passing down to 'lower' defs.
params = {'cfg' : '../cfg/default_config.json'}


#####  pool definitions  #####

def genWordFile(file_num):
    """Currently the worker only needs to create its oject-specific file. The
    def assumes params has already been initialized to at least default values.
    """
    #This doesn't need to be explicitly thread-safe since params is assumed set
    #and effectively read-only for each process.
    global params

    out = params['out_dir'] + params['out_base'] + f'_{file_num}' + \
          params['out_ext']

    #Note the possibility of IO exceptions if /dev/urandom (or similar) is not
    #initialized/empty on your machine.  Using less workers can help.
    random.seed(random.getrandbits(int(params['num_rand_bits'])) \
                if (params['search_seed']) else os.urandom(4))
    wait_t = random.randint(0,10)
    time.sleep(wait_t)
    print(f"HAHA: {file_num}, {wait_t}", flush=True)
    return {file_num, wait_t}


#####  package functions  #####

def loadConfig(cfg_path):
    """Updates the global dictionary with the supplied configuration, if it
       exists, and creates the output directory.

       Input : cfg_path : optional CLI input to the json config file

       Output : None.
    """
    global params

    if cfg_path :
        params['cfg'] = cfg_path

    #Sure this is a little sloppy but we don't need the config after this so
    #there's no reason to keep the old definition anyways and cause an if split
    #in the code.
    with open(params['cfg']) as json_file:

        params = json.load(json_file)
        os.makedirs(params['out_dir'],
                    mode=int(params['out_dir_mode'], 8), exist_ok=True)

        print(f"{params['just_spaces']}, {params['block_aligned']}")
    

def genWorkers():
    """Invokes n parallel wordgenerators, as defiend in the config file.
    
       Input: None.

       Output: None.
    """
    #Since it may be obtuse: limit to the lesser of num_out or num_workers
    with mp.Pool(processes=int(params['num_workers'] \
        if (int(params['num_outs']) >= int(params['num_workers'])) \
        else params['num_outs'])) as pool:

        result = [pool.apply_async(genWordFile, (worker,)) \
                 for worker in range(int(params['num_workers']))]
        #We must stop the zombie apocalypse!
        pool.close()
        pool.join()

#####  main  #####

def main():
    """Parses the optionally-supplied config file path and starts the string
       generator.

       Input : config - Where to find the optional config file.

       Output: None.
    """
    print("Starting?\r\n")
    parser = argparse.ArgumentParser(
                description="Generates a set of output text strings based on \
                             the input parameters.  This includes special \
                             character insertion and randomization.")
    parser.add_argument('--config', help='Optional path to the config file.')

    args = parser.parse_args()
#    try:
    loadConfig(args.config)
    genWorkers()
#    except Exception as err:
#        print(f"Encountered {err=}, {type(err)=}")

#    time.sleep(20)
    print(f"Args: {args.config}\r\n")

if __name__ == '__main__':
    main()

