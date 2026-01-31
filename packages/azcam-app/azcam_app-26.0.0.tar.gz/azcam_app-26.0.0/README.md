# azcam-app

*azcam-app* is a python package which creates the *azcamapp* application used to control imaging systems such as those used for scientific observations.

## Installation

`pip install azcam-app`

## Usage

Run the application as:

`azcamapp <full_path_to_config_file> -- <options>`

For example,

`azcamapp /data/90prime/code/pf_config.py -- -normal -datafolder /data/90prime`

The azcamapp command is effectively the same as the command:

`python -m azcam-app`

## Notes

The config_file should be a full path, not an installed python package. This is different from the standarad process for running *azcamserver*.

