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

#The managers are package variables to allow both local and remote allocation
#(i.e. within and ouside the same process) to function correctly.
Managers = []
#Tracking Maanger IDs prevents needless searches for IDs later.
Ids      = {}


def genWorkers():
    """Invokes n parallel wordgenerators, as defined in the config file.
    
       Input: None.

       Output: None.
    """
    #f-string expressions don't like evaluating ternaries.
    workers = int(self.args['num_workers']) if(int(params['num_outs']) >= \
              int(self.args['num_workers'])) else int(params['num_outs'])
    log.debug(f"Starting {workers} workers.")
    #This however, is separate to dynamically give finished workers new work.
    cur_index = workers
    idles     =  range(0, workers)
    args = [(w, w) for w in idles]

    #Since it may be obtuse: limit to the lesser of num_out or num_workers.
    with mp.Pool(processes=workers) as pool:

        while cur_index <= int(self.args['num_outs']):

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
                    done    = result[w].get(float(self.args['main_timeout']))
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

    """Notably parses the json config file, verifies the word dictionary can
       be parsed, and sets the RNG config for this process.  These are checked
       early to allow for graceful error handlign and early exit on error.

       Input: self - Pointer to the current object instance
              manager_id - The current maanger's ID

       Output: None - Throws exceptions on error.

    """
    def __init__(self, manager_id):
        self.args         = {'cfg' : '../cfg/default_manager_config.json'}
        self.not_int      = False
        self.ID           = manager_id
        self.start_index  = 0
        self.start_time   = 0
        self.worker_count = 5

        print(f"here?")
        #Sure this is a little sloppy but we don't need the config after this
        #so there's no reason to keep the old definition anyways and cause an
        #if split in the code.
        with open(self.self.args['cfg']) as json_file:

            self.args = json.load(json_file)
            os.makedirs(self.args['out_dir'], \
                        mode=int(self.args['out_dir_mode'], 8), exist_ok=True)

        #Individual log files will probably be configurable in the future.
        os.makedirs(self.args['log_dir'], \
                        mode=int(self.args['out_dir_mode'], 8), exist_ok=True)
        #We must use basic config because the dict config would require a
        #static logger definition which then must be manually changed every
        #time conf.json changes logger count, which is obviously unworkable.
        log.basicConfig(filename=(self.args['log_dir'] + 'main_log.txt'), \
                        encoding=self.args['log_encoding'], \
                        filemode=self.args['log_mode'], \
                        level=getattr(log, self.args['log_level'].upper()))
        log.info(f"using {cfg_path} and logging to {self.args['log_dir']}")

        #The workers need to know the dictionary line-count to properly grab
        #random entries but we don't want each to have to manually seek the
        #number, hence we get it here.
        #It's convenient to check that the dictionary exists and is accessible.
        if os.path.isfile(self.args['dict_path']):
            self.args['dict_size'] = sum(1 for line in open(params['dict_path'], \
              encoding=self.args['dict_encoding'], errors=params['dict_enc_err']))
            log.debug(f"size is {self.args['dict_size']}")
        else:
            log.error(f"Unable to seek size of {self.args['dict_path']}")
            return status

        #This could arguably be done in the dictionary declaration but here
        #allows for better future changes.
        self.args['ascii_sp'] = string.punctuation
        log.debug(f"Special characters are: {self.args['ascii_sp']}")

        #Similar as the above, each worker needs to know what the num ranges
        #are as actual values.  Try/Catch is apparently the fastest way to do
        #this check.
        #The int check *must* be first because of type conversions.
        log.debug(f"numgen min input: {self.args['num_gen']['range_min']}")
        log.debug(f"numgen max input: {self.args['num_gen']['range_max']}")

        try:
            self.args['num_gen']['min'] = int(params['num_gen']['range_min'])
            self.args['num_gen']['max'] = int(params['num_gen']['range_max'])

        except Exception as err:
            log.warning(f"caught error {err=} when trying to int")
            not_int = True

        if self.not_int:
            try:
                self.args['num_gen']['min'] = float(params['num_gen']['range_min'])
                self.args['num_gen']['max'] = float(params['num_gen']['range_max'])
            except Exception as err:
                log.error(f"caught error {err=} when trying to float")


    ####  Accessors  ####
    def getWorkerCount(self):
        return self.worker_count

    def getId(self):
        return self.ID

    #### Definitions ####
    def manage(self, index):
        """Generates a number of worker files as specifid by the config file.
           The Manager return (report) indicates how many workers succeeded.

           Input : self - reference to a specific manager instance

           Output: None.
        """
        print(f"Made it with {self.ID} {self.start_index}")

        return self.worker_count



#####  Package Functions  #####
def create(manager_id):
    """Creates the local manager instance and assigns it a number.  A separate
       creation step prevents constant reallocation of managers for new work
       and better management of local resources (like log files).

       Input: manager_id - The manager's assigned ID

       Output: None.
    """
    global Managers

    if manager_id not in Ids :
        #This might be converted to allowing a list input instead of requiring
        #the caller to loop.
        Managers.append(Manager(manager_id))
        Ids[manager_id] = Managers[manager_id]

    return


def start(manager_id, index) :
    """Serves as the entry point for the manager package and initializes the 
       local class.  This setup allows classes to be instantiated in the local
       process instead of from the calling process (which causes weird memory
       access/locks and isn't possible with remote processes).

       Input : manager_id - this manager's ID (it's sometimes useful to know)
               index - The first position in num_outs a worker will work on

       Output: manager_id - the ID of the manager that ran
               work_done - How much work was done; negative if error
    """
    #This is explicitly initialized to signify an error return on bad ID.
    work_done = -1

    if manager_id in Ids :
        work_done = Managers[manager_id].manage(index)

    #This allows the parent to know which manager finished and reschedule it
    #specifically. Just having an iterator doesn't identify the actual manager,
    #especially across an asyncio connection to a remote.
    return [manager_id, work_done]
