# Overview
This is a list of possible upgrades/updates that may be added to the project.  They're listed here so as to not be forgotten.  Neither list is in priority order.

## Planned
- Execution timing output/logging
- Status updates to the CLI
- Windows dictionary testing (How to get a Windows dictionary?)
- Mac Dictionary testing (should mostly match linux version)
- Mac Truncate() support for block mode
- Worker refactor to be a separate module (why won't apply_async take classes and instantiate them?)
  - Word, number, logger, and various filepaths as state data instead of function arguments
  - Get a static copy of params to the object
- Individual worker job logging capability (currently all goes to the same log)
- Parameter Randomization enabling
  - The ability to randomize number insertion (to avoid a static repeating pattern on rollover)
- Optional ability to inject numbers/special characters into arbitrary locations
- Ability to add special characters other than ASCII punctuation 
- Proper testing with other encoding types (Asian languages, Russian, Arabic, Sanskrit, etc.)
- Better Status{} handling/checking in higher-level functions.
- Actual logger message formatting.

## Unplanned
- Unit tester? (can probably borrow an existing one)
- use starmap_async? (current async seems to work as desired)
- instantiation across multiple servers?
- Worker core affinity?
- Impsum mode? (mostly as a joke, but maybe it could be handy)
- Better ability to regenerate an exact dataset? (hard right now with the RNG setup)
- Better natural sentences (not quite a Markov but similar).
- Proper sentence capitalization?
- Ability to direct output to multiple folders? (or maybe a subfolder for each output?)
