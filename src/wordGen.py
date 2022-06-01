#Generates output of dictionary-supplied words to a given size, notably
#truncating to fit a given 'block size' if necessary.

#Markovs are being ignored for now cine they're too deterministic and would
#greatly skew the training data but will probably be optional in the future.


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
import time


#####  package variables  #####

#The great thing about dictionaries defined at the package level is their global
#(public-like) capability, avoiding constant passing down to 'lower' defs. 
#Static data only, no file objects or similar (or else!).
params = {'cfg' : '../cfg/default_config.json'}
version = '0.0.2'

#####  pool functions  #####

def getRandNumList(w_log):
    """Returns a (optional) list of numbers to infuse into the data.  Infusion
       is managed in a later step.  Numbers are generated by the python random
       library in accordance to the specified in the {params}.  True random 
       needs require a different implementation.

       Input: 

       Output:
    """
    num_list = {}

    #The cfg load has guaranteed both keys are either int or float.
    if isinstance(params['num_gen']['min'], (float)):
        w_log.debug(f"Used the floag RNG.")
        for i in range(0, int(params['num_gen']['count'])) :
            num_list[i] = random.uniform(params['num_gen']['min'], \
                                         params['num_gen']['max'])
    else:
        w_log.debug(f"Used the int RNG.")
        for i in range(0, int(params['num_gen']['count'])) :
            num_list[i] = random.randrange(params['num_gen']['min'], \
                                           params['num_gen']['max'])
    
    return num_list

def getByWordLimit(w_log):
    """Returns a list of random words limited by count.  This is used when the
       {block_size} parameter is <= 0 in {params}. Size alignment is not 
       guaranteed and special characters/spaces are not yet added.

       Input : dict_file - file-object to the word dictionary

       Output : words - list of the randomly-selected words from dict_file
    """
    word_list = {}

    for i in range(0, int(params['num_words'])):
        word_list[i] = lc.getline(params['dict_path'], \
                            random.randrange(0, params['dict_size'])).strip()
    w_log.debug(f"Word lsit size: {range(0, int(params['num_words']))}") 
    return word_list

def getByBlockLimit(w_log):
    """Returns a list of random words limited by (output) block size.  This is
       used when the {block_size} parameter is >0 in {params}.  The last word
       may be truncated if a list exactly matching {block_size} is not created.
       Finally, this list may need to be further truncated by consumers if
       other parameters, like {randomize} or {special_count} are used.

       Input : dict_file - file-object to the word dictionary

       Output : words - list of the randomly-selected words form dict_file
    """
    word_list = {}
    #Sadly while loops are still sometimes necessary, even in Python. Block
    #size assumes the config file already accounts for byte conversions (e.g.:
    #1 byte per ASCII encoding and between 1-4 for unicode).
    count = 0
    index = 0

    while count < (int(params['block_size']) * int(params['block_count'])):
        word_list[index] = lc.getline(params['dict_path'], \
                            random.randrange(0, params['dict_size'])).strip()
        count += len(word_list[index])
        w_log.debug(f"Word {word_list[index]} with size {len(word_list[index])}")
        index += 1

    return word_list

def getDictWords(w_log):
    """Opens the supplied dictionary and returns a random set of words of size
       specified in the config.  This function is intentionally separate to 
       allow future upgrades to dictionary sources (it's arguably more
       efficient to not have the list return).
       This function assumes the list request and word source are reasonable 
       (e.g. not millions of words or a single word size filling all of RAM)

       Input : dict_file - file-object to the word dictionary

       Output : words - list of the randomly-selected words from dict_file
    """
    if (int(params['block_size']) > 0):
        word_list = getByBlockLimit(w_log)
    else:
        word_list = getByWordLimit(w_log)

    return word_list

def genFile(w_log, my_file, word_list, num_list=None):
    """Writes the supplied word list to the supplied file, given the values
       defined in {params}.  This is intentionally split from the word list
       generation to allow for future dictionary source changes.

       Input : process_file - Where to write the data pattern
               words - list of order-randomizable source words for the file

       Output: None.
    """
    line    = ""
    #This can be independent of the word_list length
    num_len = len(num_list)
    num_ind = 0
    written = 0

    while written < int(params['num_words']):
        #There's probably a clever combinational trick out there somewhere I'm
        #not bothering to think of currently.
        for p in range(0, int(params['sen_per_par'])):
            for w in range(0, int(params['words_per_sen'])):
                #The list was generated randomly so doesn't need shuffling.
                line = line + f"{word_list[written]}"
                #This is where a word list can get wrapped.
                written = (written + 1) % len(word_list)
                w_log.debug(f"written: {written}")
                #Most sentences end with a period (typos and heretics aside).
                if w < (int(params['words_per_sen'])-1):
                    line = line + ' '
                else:
                    line = line + '. '

                #There needs to be a special exist case to ensure that only the
                #request number of words are written if the config file doesn't
                #implicitly specify divisible limits.
                if written == 0:
                    w_log.debug(f"Writing last sentence: {line}")
                    my_file.write(line)
                    return

                for sp in range(0, int(params['special_count'])):
                    #This will eventually be a percentage-based write
                    #influenced by the {randomize} parameter.
                    line = line + params['ascii_sp'][random.randrange(0, \
                                                     len(params['ascii_sp']))]
                #Exactly where numbers get injected will probably change in the
                #randomization update; for now here seems most correct.
                if num_len > 0:
                    line = line + str(num_list[num_ind]) + " "
                    #The number list has the same wrapping issue.
                    num_ind = (num_ind + 1) % num_len

            #Writing sentences seems the best compromise between excessive
            #writes and monstrous line (sentence) lengths.
            w_log.debug(f"writing sentence: {line}")
            my_file.write(line)
            line = ''
        my_file.write(os.linesep)

    return

def postProcess(file_path, w_log):
    """Performs and necessary post-processing on files.  For example, the block
       mode usually requires a slight truncation on the output, which is easier
       to do here than inside the loop logic.

       Input: None.

       Output: None.
    """
    #Block mode is currently the only mode needing post-processing (to trim to
    #the specified block size).
    if 0 != int(params['block_size']) and int(params['block_count'] != 0):
        w_log.info(f"Shrinking {file_path} from {os.path.getsize(file_path)}")
        #Only in python is truncate easier than logging.
        os.truncate(file_path, \
                    (int(params['block_count']) * int(params['block_size'])))
        w_log.info(f"File size shrunk to {os.path.getsize(file_path)}")
    else:
        w_log.info(f"Not shrinking file: {file_path}")
    return

def genWordFile(worker, file_num):
    """Currently the worker only needs to create its object-specific file. The
    def assumes params has already been initialized to at least default values.
    
    Input: the particular worker's number.

    Output: pass/fail and exception status, if any.

    """
    #This doesn't need to be explicitly thread-safe since params is assumed set
    #and effectively read-only for each process.
    global params

    #This is made here purely for readability (and because I like having local
    #variables forward-declared whenever possible, blame my professors.
    num_list = {}
    out = params['out_dir'] + params['out_base'] + f'_{file_num}' + \
          params['out_ext']
    status = (True, {})
    word_list = {}

    #Each worker makes its own log file for its job.  This will be expanded in
    #The future to add unique logs for each job execution.
    #Since logging is a centralized client/server, python expects each process
    #here to add a unique handler instead of making their own logger.
    w_handler = log.FileHandler(params['log_dir'] + 'worker_' + str(worker),
                   mode=params['worker_mode'], encoding=params['log_encoding'])
    w_handler.setLevel(getattr(log, params['worker_level'].upper()))
    #This instance has to be manually passed around until the issue with a pool
    #spawning object instances via classes is resolved.
    w_log = log.getLogger(f"worker_{worker}_log")
    w_log.addHandler(w_handler)
    #It's a bit annoying to have to effectively do this twice.
    w_log.setLevel(getattr(log, params['worker_level'].upper()))
    #Otherwise worker messages also end up in the main logger.
    w_log.propagate = False
    w_log.debug(f"Created Logger for woker {worker}")
    w_log.debug(f"Out path is {out}")

    try:
        #Note the possibility of IO exceptions if /dev/urandom (or similar) is
        #not initialized/empty on your machine.  Using less workers can help.
        random.seed(random.getrandbits(int(params['num_rand_bits'])) \
                    if (params['search_seed']) else os.urandom(8))
        w_log.debug(f"Using rand state: {random.getstate()}")
    except Exception as err:
        status = {False, err}
        w_log.error(f"Process {worker} encountered {err=}, {type(err)=}")
    
    #The dictionary path was validated when loading the config.
    word_list = getDictWords(w_log)
    w_log.debug(f"word list is: {word_list}")

    if (int(params['num_gen']['count']) > 0):
        num_list  = getRandNumList(w_log)
        w_log.debug(f"Number list is: {num_list}")

    #The 'w' is intentional as we're generating new data.  Save your data if
    #you want it to persist between dataset generations (or use a new out_dir).
    with open(out, mode='w', encoding=params['out_encoding']) as process_file:
        genFile(w_log, process_file, word_list, num_list)

    #This is necessary for the block mode but made generic for future changes.
    postProcess(out, w_log)

    return status


#####  package functions  #####

def loadConfig(cfg_path):
    """Updates the global dictionary with the supplied configuration, if it
       exists, and creates the output directory.

       Input : cfg_path : optional CLI input to the json config file

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
    log.debug(f"using {cfg_path} and logging to {params['log_dir']}")
    
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
    log.debug(f"numben max input: {params['num_gen']['range_max']}")
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
    #f-string expressions don't like evaluating ternaries
    workers = int(params['num_workers']) if(int(params['num_outs']) >= \
              int(params['num_workers'])) else int(params['num_outs'])
    log.debug(f"Starting {workers} workers.")
    #Since it may be obtuse: limit to the lesser of num_out or num_workers.
    with mp.Pool(processes=workers) as pool:

        for out_file in range(0, int(params['num_outs'])):
            result = [pool.apply_async(genWordFile, (worker, out_file,)) \
                     for worker in range(int(params['num_workers']))]
            print(f"How many though? {out_file}")
        print(f"Stati: {result}")
        #We must stop the zombie apocalypse!
        pool.close()
        pool.join()
        print(f"Yep")


#####  main  #####

def main():
    """Parses the optionally-supplied config file path and starts the string
       generator.

       Input : config - Where to find the optional config file.

       Output: None.
    """
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
            status = genWorkers()
    except Exception as err:
        print(f"Encountered {err=}, {type(err)=}")

if __name__ == '__main__':
    main()

