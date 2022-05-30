#Generates output of dictionary-supplied words to a given size, notably
#truncating to fit a given 'block size' if necessary.

#Markovs are being ignored for now cine they're too deterministic and would
#greatly skew the training data but will probably be optional in the future.


#####  imports  #####

import argparse
import json
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


#####  pool functions  #####

def getRandNumList():
    """Returns a (optional) list of numbers to infuse into the data.  Infusion
       is managed in a later step.  Numbers are generated by the python random
       library in acoordance to the specified in the {params}.  True random 
       needs require a different implementation.

       Input: 

       Output:
    """
    num_list = {}

    #The cfg load has guaranteed both keys are either int or float.
    if isinstance(params['num_gen']['min'], (float)):
        for i in range(0, int(params['num_gen']['count'])) :
            num_list[i] = random.uniform(params['num_gen']['min'], \
                                         params['num_gen']['max'])
    else:
        for i in range(0, int(params['num_gen']['count'])) :
            num_list[i] = random.randrange(params['num_gen']['min'], \
                                           params['num_gen']['max'])
    return num_list

def getByWordLimit():
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
#    print(f"Today's meat:\r\n {word_list}")
    return word_list

def getByBlockLimit():
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
        index += 1

#    print(f"Today's HAM: {count}\r\n {word_list}")
    
    return word_list

def getDictWords():
    """Opens the supplied dictionary and returns a random set of words of size
       specificed in the config.  This function is intentionally separate to 
       allow future upgrades to dictionary sources (it's arguably more efficent
       to not have the list return).
       This function assumes the list request and word source are reasonable 
       (e.g. not millions of words or a single word size filling all of RAM)

       Input : dict_file - file-object to the word dictionary

       Output : words - list of the randomly-selected words from dict_file
    """
    if (int(params['block_size']) > 0):
        word_list = getByBlockLimit()
    else:
        word_list = getByWordLimit()

    return word_list

def genFile(my_file, word_list, num_list=None):
    """Writes the supplied word list to the supplied file, given the values
       defined in {params}.  This is intentionally split from the word list
       generation to allow for future dictionary source changes.

       Input : process_file - Where to write the data pattern
               words - list of order-randomizable source words for the file

       Output: None.
    """
    written = 0
    line = ""

    #There's probably a clever combinational trick out there somehwere I'm not
    #bothering to think of currently.
    for p in range(0, int(params['words_per_par'])):
        #wrong pattern, need to write until words are gone, not per sentence.
        for w in word_list:
            #The list was generateed randomly so doesn't need shuffling.
            line = f"{word_list[w]}"
            my_file.write(line)
            #If only python had a ++ operator
            written += 1

            if 0 == (written % int(params['words_per_sen'])):
                my_file.write('.')
            my_file.write(' ')

            for sp in range(0, int(params['special_count'])):
                #This will eventually be a percentage-based wite influenced by
                # the {randomize} parameter
                my_file.write(params['ascii_sp'][random.randrange(0, \
                                                 len(params['ascii_sp']))])
        my_file.write(os.linesep)

    return

def genWordFile(file_num):
    """Currently the worker only needs to create its oject-specific file. The
    def assumes params has already been initialized to at least default values.
    
    Input: the particular worker's number.

    Output: pass/fail and exception status, if any.

    """
    #This doesn't need to be explicitly thread-safe since params is assumed set
    #and effectively read-only for each process.
    global params

    #This is made here purely for readability (and because I like having local
    #variables forward-delcared whenever possible, blame my professors.
    num_list = {}
    out = params['out_dir'] + params['out_base'] + f'_{file_num}' + \
          params['out_ext']
    status = (False, {})
    word_list = {}

    print(f"Steew {out}")
    try:
        #Note the possibility of IO exceptions if /dev/urandom (or similar) is
        #not initialized/empty on your machine.  Using less workers can help.
        random.seed(random.getrandbits(int(params['num_rand_bits'])) \
                    if (params['search_seed']) else os.urandom(8))
    except Exception as err:
        status = {False, err}
        print(f"Process {file_num} encountered {err=}, {type(err)=}")

    #The dictionary path was validated when loading the config
    word_list = getDictWords()

    if (int(params['num_gen']['count']) > 0):
        num_list  = getRandNumList()

    #The 'w+' is intentional as we're generating new data.  Save your data if
    #you want it to persist between datase generations (or use a new out_dir)
    with open(out, mode='w+', encoding=params['out_encoding'], \
              error=params['out_enc_err']) as process_file:
        genFile(process_file, word_list, num_list)

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
        os.makedirs(params['out_dir'],
                    mode=int(params['out_dir_mode'], 8), exist_ok=True)

    #The workers need to know the dictionary line-count to properly grab random
    #entries but we don't want each to have to manually seek the number, hence
    #we get it here.  Future versions may push this to a corpus class __init__
    #It's also a convenient check that the dictionary exists and is accessable.
    if os.path.isfile(params['dict_path']):
        params['dict_size'] = sum(1 for line in open(params['dict_path'], \
            encoding=params['dict_encoding'], errors=params['dict_enc_err']))
        print(f"size is {params['dict_size']}")
    else:
        return status

    #This could arguably be done in the dictionary declaration but here allows
    #for better future changes.
    params['ascii_sp'] = string.punctuation

    #Similar as the above, each worker needs to know what the num ranges are as
    #actual values.  Try/Catch is apparently the fastest way to do this check.
    #The int check *must* be first because of type conversions
    try:
        params['num_gen']['min'] = int(params['num_gen']['range_min'])
        params['num_gen']['max'] = int(params['num_gen']['range_max'])
    except Exception as err:
        print(f"caught error {err=} when trying to int")
        not_int = True
    if not_int:
        try:
            params['num_gen']['min'] = float(params['num_gen']['range_min'])
            params['num_gen']['max'] = float(params['num_gen']['range_max'])
        except Exception as err:
            print(f"caught error {err=} when trying to float")
            status = {False, err}

    print(f"Found nums: {params['num_gen']['min']}, {params['num_gen']['max']}, {not_int}")
    return status

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
    status = loadConfig(args.config)
    if not status[0] :
        status = genWorkers()
#    except Exception as err:
#        print(f"Encountered {err=}, {type(err)=}")

    print(f"Args: {args.config}\r\n")

if __name__ == '__main__':
    main()

