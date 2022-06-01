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
- Ability yo truncate to a single block size added.
- User-configurable paths to the dictionary, data, and log files added.
- User-configurable directory permissions added.
- User-configurable error behavior for unicode/encoding errors added.

### Specific Changes
- Project generated.

