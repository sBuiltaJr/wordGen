#Generates output of dictionary-supplied words to a given size, notably
#truncating to fit a given 'block size' if necessary.

#Markovs are being ignored for now since they're too deterministic and would
#greatly skew the training data but will probably be optional in the future.


#####  imports  #####

import argparse
import json
import logging as log
import multiprocessing as mp
import os
import string
import sys
#tqdm is specifically not being used because of the formatting issues and lack
#of nice parallelization, including conflicts with the logger.
import time


#####  package variables  #####

#The great thing about dictionaries defined at the package level is their global
#(public-like) capability, avoiding constant passing down to 'lower' defs. 
#Static data only, no file objects or similar (or else!).
params = {'cfg' : '../cfg/default_config.json'}
version = '0.0.5'


#####  package functions  #####

def loadConfig(cfg_path):
    """Updates the global dictionary with the supplied configuration, if it
       exists, and creates the output directory.

       Input : cfg_path - optional CLI input to the json config file

       Output : None.
    """
    global params
    not_int = False
    status = (False, {})

    if cfg_path :
        params['cfg'] = cfg_path

    #Sure this is a little sloppy but we don't need the config after this so
    #there's no reason to keep the old definition anyways and cause an if split
    #in the code.
    with open(params['cfg']) as json_file:

        params = json.load(json_file)
        os.makedirs(params['out_dir'], \
                    mode=int(params['out_dir_mode'], 8), exist_ok=True)

    #Individual log files will probably be configurable in the future.
    os.makedirs(params['log_dir'], \
                    mode=int(params['out_dir_mode'], 8), exist_ok=True)
    #We must use basic config because the dict config would require a static
    #logger definition which then must be manually changed every time cfg.json
    #changes logger count, which is obviously unworkable.
    log.basicConfig(filename=(params['log_dir'] + 'main_log.txt'), \
                    encoding=params['log_encoding'], \
                    filemode=params['log_mode'], \
                    level=getattr(log, params['log_level'].upper()))
    log.info(f"using {cfg_path} and logging to {params['log_dir']}")

    return status

def genWorkers():
    """Invokes n parallel wordgenerators, as defined in the config file.
    
       Input: None.

       Output: None.
    """
    #f-string expressions don't like evaluating ternaries.
    workers = int(params['num_workers']) if(int(params['num_outs']) >= \
              int(params['num_workers'])) else int(params['num_outs'])
    log.debug(f"Starting {workers} workers.")
    #This however, is separate to dynamically give finished workers new work.
    cur_index = workers
    idles     =  range(0, workers)
    args = [(w, w) for w in idles]

    #Since it may be obtuse: limit to the lesser of num_out or num_workers.
    with mp.Pool(processes=workers) as pool:

        while cur_index <= int(params['num_outs']):

            #The worker check loop will have a null result if everyone's busy.
            if idles:
                log.debug(f"args: {args} {idles} {cur_index} {len(idles)}")
                result = [pool.apply_async(genWordFile, (args[worker][0], \
                         args[worker][1],)) for worker in range(0, len(idles))]
                idles  = []
                args   = []

            #Future versions might put a status tracker here.  Or convert it to
            #a callback count function.  This structure allows workers to be
            #reused (effectively) as soon as they're finished, instead of
            #waiting for an entire batch to finish before returning.
            for w in range(0, workers):

                try:
                    done    = result[w].get(float(params['main_timeout']))
                    #Both properties need to be checked since exceptions will
                    #pass the 'ready' state but not the 'successful' one.
                    ready   = result[w].ready()
                    success = result[w].successful()

                except Exception as err:
                    continue

                idles.append(w)
                args.append((w, cur_index))
                #if only Python had a ++ operator.
                cur_index += 1

                if ready and not success:
                    log.error(f"worker {w} returned error: {result[w]._value}")

            log.info(f"next job list {idles} with {cur_index - workers} done")

        #We must stop the zombie apocalypse!
        pool.close()
        pool.join()
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

        if not status[0] :
            total_time[0] = time.perf_counter()
            status = genWorkers()
            #This doesn't need to be set here per se, but it's more readable.
            total_time[1] = time.perf_counter()
            diff = total_time[1] - total_time[0] 

            if "True" == params['main_timing']:
                print(f"Total execution time of: {diff:6f} seconds.")

    except Exception as err:
        print(f"Encountered {err=}, {type(err)=}")

if __name__ == '__main__':
    main()

