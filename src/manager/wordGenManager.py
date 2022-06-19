#Manages Worker Threads and reports back to the main User Process.

#####  imports  #####

import argparse
import json
import logging as log
import linecache as lc
import multiprocessing as mp
import os
import random
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

#The managers are package variables to allow both local and remote allocation
#(i.e. within and ouside the same process) to function correctly.
Managers = []

#####  package functions  #####

def errRet(err):
    """Is a generic, reentrant error handling callback for worker functions.
       Primarily this jsut logs errors and updates any status information
       necessary to do so.

       Input : err - error condition returned by the worker.

       Output: None.
    """
    #These should probably be class functions instead to avoid multi-process
    #issues when accessing the package list.
    return

def workRet(ret):
    """Is the generic, reentrant regular worker callback function.  It mostly
       updates any relevant status information.

       Input : ret - The return value from the worker.

       Output: None.
    """

    return



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

    #The workers need to know the dictionary line-count to properly grab random
    #entries but we don't want each to have to manually seek the number, hence
    #we get it here.  Future versions may push this to a corpus class __init__
    #It's also a convenient check that the dictionary exists and is accessible.
    if os.path.isfile(params['dict_path']):
        params['dict_size'] = sum(1 for line in open(params['dict_path'], \
            encoding=params['dict_encoding'], errors=params['dict_enc_err']))
        log.debug(f"size is {params['dict_size']}")
    else:
        log.error(f"Unable to seek size of {params['dict_path']}")
        return status

    #This could arguably be done in the dictionary declaration but here allows
    #for better future changes.
    params['ascii_sp'] = string.punctuation
    log.debug(f"Special characters are: {params['ascii_sp']}")

    #Similar as the above, each worker needs to know what the num ranges are as
    #actual values.  Try/Catch is apparently the fastest way to do this check.
    #The int check *must* be first because of type conversions.
    log.debug(f"numgen min input: {params['num_gen']['range_min']}")
    log.debug(f"numgen max input: {params['num_gen']['range_max']}")

    try:
        params['num_gen']['min'] = int(params['num_gen']['range_min'])
        params['num_gen']['max'] = int(params['num_gen']['range_max'])

    except Exception as err:
        log.warning(f"caught error {err=} when trying to int")
        not_int = True

    if not_int:
        try:
            params['num_gen']['min'] = float(params['num_gen']['range_min'])
            params['num_gen']['max'] = float(params['num_gen']['range_max'])
        except Exception as err:
            log.error(f"caught error {err=} when trying to float")
            status = {False, err}

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


#####  Manager Class  #####
class Manager:

    def __init__(self, manager_id):
        self.ID           = manager_id
        self.start_index  = 0
        self.start_time   = 0
        self.worker_count = 5


    ####  Accessors  ####
    def getWorkerCount(self):
        return self.worker_count

    def manage(self, index):
        """Generates a number of worker files as specifid by the config file.
           The Manager return (report) indicates how many workers succeeded.

           Input : self - reference to a specific manager instance

           Output: None.
        """
        print(f"Made it with {self.ID} {self.start_index}")

        return self.worker_count




#####  Entry  #####
def create(manager_id):
    """Creates teh local manager instance and assigns it a number.  A separate
       creation step prevents constant reallocation of managers for new work
       and better management of lcoal resources (like log files).

       Input: manager_id - The manager's assigned ID

       Output: None.
    """
    global Managers

    #This might be converted to allowing a list input instead of requiring the
    #caller to loop.
    Managers.append(Manager(manager_id))


def start(manager_id, index) :
    """Serves as the entry point for the manager package and initializes the 
       local class.  This setup allows classes to be instantiated in the local
       process instead of from the calling process (which causes weird memroy
       access/locks and isn't possible with remote processes).

       Input : manager_id - this manager's ID (it's sometimes useful to know)
               index - The first position in num_outs a worker will work on

       Output: None.
    """
    print(f"Hi? {manager_id} {index}, {len(Managers)}")

    work_done = Managers[manager_id].manage(index)

    #This allows the parent to know which manager finished and reschedule it
    #specifically. Just having an iterator doesn't identify the actual manager,
    #especially across an asyncio connection to a remote.
    return [manager_id, work_done]
