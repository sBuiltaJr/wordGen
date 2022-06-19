#Generates output of dictionary-supplied words to a given size, notably
#truncating to fit a given 'block size' if necessary.

#Markovs are being ignored for now since they're too deterministic and would
#greatly skew the training data but will probably be optional in the future.


#####  imports  #####

import argparse
import concurrent.futures as cf
import json
import logging as log
import multiprocessing as mp
import os
import manager.wordGenManager as jm
import string
import sys
#tqdm is specifically not being used because of the formatting issues and lack
#of nice parallelization, including conflicts with the logger.
import time


#####  Package Variables  #####

#The great thing about dictionaries defined at the package level is their global
#(public-like) capability, avoiding constant passing down to 'lower' defs. 
#Static data only, no file objects or similar (or else!).
params = {'cfg' : '../cfg/default_config.json'}
version = '0.1.0'


#####  Package Functions  #####

def loadConfig(cfg_path):
    """Updates the global dictionary with the supplied configuration, if it
       exists, and creates the output directory.

       Input : cfg_path - optional CLI input to the json config file

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

    #We must use basic config because the dict config would require a static
    #logger definition which then must be manually changed every time cfg.json
    #changes logger count, which is obviously unworkable.
    log.basicConfig(filename=(params['log_dir'] + 'main_log.txt'), \
                    encoding=params['log_encoding'], \
                    filemode=params['log_mode'], \
                    level=getattr(log, params['log_level'].upper()))
    log.info(f"using {cfg_path} and logging to {params['log_dir']}")

    #These could be grouped into single checks but explicitly reporting exact
    #errors is nice too.
    if 0 >= int(params['num_outs']):
        log.error("num_outs must be greater than 0!")
        return False

    if int(params['num_outs']) != float(params['num_outs']):
        log.error("num_outs must be a whole number!")
        return False

    if 0 >= int(params['num_managers']):
        log.error(f"num_managers must be greater than 0!")
        return False

    if int(params['num_managers']) != float(params['num_managers']):
        log.error("num_managers must be a whole number!")
        return False

    return True

def genManagers():
    """Invokes n parallel wordgenerators, as defined in the config file.
    
       Input: None.

       Output: None.
    """
    managers  = int(params['num_managers'])
    log.info(f"Starting {managers} managers.")
    num_mans  =  range(0, managers)
    args      = [[m, m] for m in num_mans]
    remainder = int(params['num_outs']) % managers
    results   = []

    #This should probably try to evenly spread the remainder or adapt to a
    #user-defined remainder strategy at some future point.  It's added to the
    #frong since, all else equal, the first manager is likely to finish before
    #the later managers.
    args[0][1] += remainder
    log.info(f"Added {remainder} extra jobs to maanger 0.")

    #This has been convered explicitly to an asyncio ProcessPool to allow
    #future versions to invoke Managers across computers (e.g. subprocess_exec
    #with TCP/UDP data flowing to/from a series of remote terminals).
    try:
        #This is in a try statement explicitly to warn Windows users who
        #specified more than 60 managers in the config file.
        pool = cf.ProcessPoolExecutor(max_workers=managers)
        
        #In the future, this should return the number of workers under a
        #manager to allow for better load-balancing.
        [jm.create(m_id) for m_id in num_mans]
        log.info(f"Created {managers} Managers")

    except ValueError as err:
        log.error(f"Too many Managers for the current platform!: {managers}")
    except Exception as err:
        log.error(f"Error when making Manager pool: {err=}")

    #Future versions may implement a slip band (like the Managers do) for 
    #optimizing parallel work (and reducing completion time deviation) but this
    #is sufficent for now given the complexity of the alternative. The major
    #change would be: assign Managers a pool proportional to their Worker
    #allotment and job processing time.
    try:
        results = [pool.submit(jm.start, args[m][0], args[m][1]) for m in num_mans]

        for r in cf.as_completed(results):
            res = r.result()
            print(f"Result is: {res}")

    except Exception as err:
        print(f"Exception when running submit: {err=}")
            
    pool.shutdown(True, cancel_futures=True)
    log.info(f"Worker jobs complete.")


#####  main  #####

def main():
    """Parses the optionally-supplied config file path and starts the string
       generator.

       Input : config - filepath of where to find the optional config file.

       Output: None.
    """
    total_time = [0.0, 0.0]
    parser = argparse.ArgumentParser(
                description="Generates a set of output text strings based on \
                             the input parameters.  This includes special \
                             character insertion and randomization.")
    parser.add_argument('--config', help='Optional path to the config file.')
    parser.add_argument('--version', help='Prints the version and exits.', \
                        action="store_true")

    args = parser.parse_args()

    if args.version:
        print(f"wordGen version {version}")
        sys.exit()
    
    try:
        status = loadConfig(args.config)

        if status :
            total_time[0] = time.perf_counter()
            genManagers()
            #This doesn't need to be set here per se, but it's more readable.
            total_time[1] = time.perf_counter()
            diff = total_time[1] - total_time[0] 

            if "True" == params['main_timing']:
                print(f"Total execution time of: {diff:6f} seconds.")

    except Exception as err:
        print(f"Encountered {err=}, {type(err)=}")

if __name__ == '__main__':
    main()

