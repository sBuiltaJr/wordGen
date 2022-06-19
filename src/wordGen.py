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


#####  package variables  #####

#The great thing about dictionaries defined at the package level is their global
#(public-like) capability, avoiding constant passing down to 'lower' defs. 
#Static data only, no file objects or similar (or else!).
params = {'cfg' : '../cfg/default_config.json'}
version = '0.1.0'


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

    #We must use basic config because the dict config would require a static
    #logger definition which then must be manually changed every time cfg.json
    #changes logger count, which is obviously unworkable.
    log.basicConfig(filename=(params['log_dir'] + 'main_log.txt'), \
                    encoding=params['log_encoding'], \
                    filemode=params['log_mode'], \
                    level=getattr(log, params['log_level'].upper()))
    log.info(f"using {cfg_path} and logging to {params['log_dir']}")

    return status

def genManagers():
    """Invokes n parallel wordgenerators, as defined in the config file.
    
       Input: None.

       Output: None.
    """
    #f-string expressions don't like evaluating ternaries.
    managers = int(params['num_managers']) if(int(params['num_outs']) >= \
               int(params['num_managers'])) else int(params['num_outs'])
    log.debug(f"Starting {managers} managers.")
    #This however, is separate to dynamically give finished workers new work.
    cur_index = managers
    idles     =  range(0, managers)
    args      = [(m, m) for m in idles]
    mangs     = [jm.Manager() for m in idles]
    procs     = []
    results = []

    #This has been convered explicitly to an asyncio ProcessPool to allow
    #future versions to invoke Managers across computers (e.g. subprocess_exec
    #with TCP/UDP data flowing to/from a series of remote terminals).
    try:
        #This is explicitly in a try statement explicitly to warn windows users
        #who specified more than 60 managers in the config file.
        pool = cf.ProcessPoolExecutor(max_workers=managers)
    except ValueError as err:
        log.error(f"Too many managers for the current platform!: {managers}")
    except Exception as err:
        log.error(f"Error when making manager pool: {err=}")

    #Since it may be obtuse: limit to the lesser of num_out or num_workers.
    #with mp.Pool(processes=workers) as pool:

    while cur_index <= int(params['num_outs']):

        #The idles check loop will have a null result if everyone's busy.
        if idles:
            log.debug(f"args: {idles} {cur_index} {len(idles)}")

            try:
                #for i in idles:
                #    print(f"Adding idle {i}")
                    #procs.append(pool.map(jm.main, args[i], chunksize=int(params['chunk_size'])))
                    
                #results = pool.map(mangs.main, args, chunksize=int(params['chunk_size']))
                #for i in idles:
                #    result.append(pool.submit())
                #    print(f"Result is: {r}")
                for i in idles:
                    results.append(pool.submit(mangs[i], args[i]))

                for r in results:
                    print(f"Result is: {r}")

                cur_index += managers
            except Exception as err:
                print(f"Exception when running map: {err=}")
            
#            for i in idles:
#                try:
#                    print(f"Proc: {i}")
#                    idles.append(i)
#                    args.append(i, cur_index)
#                    cur_index += 1
#                except cf.TimeoutError as err:
#                    continue
#                except cf.CancelledError as err:
#                    log.warning(f"Maanger {i} was cancelled!")
#                except Exception as err:
#                    log.error(f"Caught {err=} from manager {i}!")

            #Future versions might put a status tracker here.  Or convert it to
            #a callback count function.  This structure allows workers to be
            #reused (effectively) as soon as they're finished, instead of
            #waiting for an entire batch to finish before returning.
#            for m in range(0, managers):

#                try:
#                    done    = result[w].get(float(params['main_timeout']))
                    #Both properties need to be checked since exceptions will
                    #pass the 'ready' state but not the 'successful' one.
#                    ready   = result[w].ready()
#                    success = result[w].successful()

#                except Exception as err:
#                    continue

#                idles.append(w)
#                args.append((w, cur_index))
                #if only Python had a ++ operator.
#                cur_index += 1

#                if ready and not success:
#                    log.error(f"worker {w} returned error: {result[w]._value}")

#            log.info(f"next job list {idles} with {cur_index - workers} done")

        #We must stop the zombie apocalypse!
#        pool.close()
#        pool.join()
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
    
#    try:
    status = loadConfig(args.config)

    if not status[0] :
        total_time[0] = time.perf_counter()
        genManagers()
        #This doesn't need to be set here per se, but it's more readable.
        total_time[1] = time.perf_counter()
        diff = total_time[1] - total_time[0] 

        if "True" == params['main_timing']:
            print(f"Total execution time of: {diff:6f} seconds.")

#    except Exception as err:
#        print(f"Encountered {err=}, {type(err)=}")

if __name__ == '__main__':
    main()

