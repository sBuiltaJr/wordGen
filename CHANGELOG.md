# Version 0.0.4

## Highlights
- Enabled high-precision timing of the generation process.

### Specific Changes
- Added a wrapper around the invocation of all workers to measure total execution time.
  - An issue discovered prevents individual worker timing, it is expected to resolved in the future.

# Version 0.0.3

## Highlights
- Worker management properly enabled.
- Unicode shenanigans when writing files resolved.
- Better logging added at the INFO level.

### Specific Changes
- Revamped genWorkers to actually handle when workers != out_size.
  - The args also properly identify which worker is working on which file.
- Enabled better load-balancing across worker jobs.
  - The for loop with exception handling effectively catches when a worker is done.
    - This may be converted to a callback in the future, but testing of 200 files with 100000 word output worked well.
- Added INFO logs to workers and main about when workers are done and what they're working on.
- Fixed the bug causing some file generations to end early (unicode issues in genFile())
  - Added checks to halt execution if the dictionary encoding isn't actually what was specified (apparently 'open()' wasn't actually doing the encode by default).
  - Added logfile errors when the encoding becomes an issue for writing to files.
  - Added general exception handling to the write function, just in case.
- Added better file buffering to genFile().
  - Use of open() specifically when writing guarantees the file buffer for each file is flushed before continuing.
- Added more vertical whitespace to match my own preferences.

# Version 0.0.2

## Highlights
- Worker-level logging enabled.
- Block-mode bug fixed.

### Specific Changes
- Enabled a per-worker logging mechanism.
  - loggers are currently manually passed to the sub-functions.
    - This should be fixed with the pool/class interaction is resolved.
- logs are written to the same log foler as the main thread logger.
- Several instances of DEBUG, INFO, WARNIING, and ERROR logs added to the code.
  - All previous print statements that can be converted, have been.
    - Some remain in main() prior to the logger initialization.
  - Future updates may include better filtering options for workers.
- Entries added to the config for managing the worker logging (versus the main thread logging).
- Block mode truncation in postProcess() now multiplies by block count.

# Version 0.0.1

## Highlights
- Unlimited word sequence added.
- Variable input and output encoding format supported.
- Number and Special Character insertion added.
- Configurable paragraph and sentence size added.
- Configurable worker processes and number of output files added.
- Variable worker Random seeds added.
- Main thread logger added.
- Option to generate words by block size or word count added.
- Ability to truncate to a single block size added.
- User-configurable paths to the dictionary, data, and log files added.
- User-configurable directory permissions added.
- User-configurable error behavior for unicode/encoding errors added.

### Specific Changes
- Project generated.

