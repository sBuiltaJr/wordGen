# wordGen
## A Multiprocess Random Word Block Generator

wordGen is an offline python 3.x tool designed for large-dataset generation of
pseudo-random text data (though it also supports small-scale parameters). It 
samples a provided dictionary file and generates a series of configurable 
output files based on the included json settings file (defaulted to the
[default_config.json file](cfg/default_config.json).

wordGen is highly configurable, such as input/output encoding, RNG sources, 
insertion of special characters and/or numbers, parameter randomization,
variable paragraph and sentence lengths, and more. The project aims to expand
the program's versatility and resiliency against dataset patterns across all
textual generation types as it matures.

wordGen is not expressly a lorem ipsum generator, though its output can be
configured for the same purpose.

# Dependencies
- Python 3.9 or newer (for encoding handling)

wordGen is a python 3.x project, currently tested on python 3.9.12.  While
intended to be portable, older versions will not be expressly supported.

## License
wordGen (and all flies in the wordgen repo) fall under the [GPLv3](LICENSE.md)

# Usage
wordgen is invoked directly via command-line:
e.g.:
```
cd /src
python wordGen.py
```
Or with an optional config file path:
```
python wordGen.py --config <config_file_path>
```

## Limitations/Known Issues
Also see the [changelog](CHANGELOG.md).

- Parameter randomization not currently supported.
- Windows-based dictionaries untested.
- Block truncate (via truncate()) may not work on Mac OS.
- Numbers and special characters are currently inserted only after words.
- Special characters are only pulled from the ASCII special set.

## Common Gochas
- Do you have permissions to have all the workers writing to their output files concurrently (/etc/security/limits.conf)?



