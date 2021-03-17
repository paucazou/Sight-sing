#!/usr/bin/python3
# -*-coding:Utf-8 -*
#Deus, in adjutorium meum intende

import argparse
import config_parser
import config_checker
import notes_generator

import mingus.core.scales as mcs

# arguments
cmdparse = argparse.ArgumentParser(description="Creates a melody following user defined rules")

# specific cmd line arguments values and functions
_scales = []
for k in mcs.keys:
    _scales.append(k[0])
    _scales.append(k[1])

_max_number = 500
def _type_number(val):
    val = int(val)
    if val not in range(3,_max_number):
        raise TypeError
    return val

cmdparse.add_argument("--scale","-s",help="Select which scale you want to use. Minor scales are specified in lower case: C = major; c = minor. To use a chromatic scale, enter the word 'chromatic'.",choices=_scales)
cmdparse.add_argument("--number","-n",help=f"Change number of notes played. Min: 3. Max: {_max_number}",type=_type_number)
cmdparse.add_argument("--tessitura","-t",nargs=2,help="Tessitura of the melody. Example: C-4 A-6. Minimum: an octave")
cmdparse.add_argument("--degrees","-d",nargs="*",help="Degrees selected, from 1 to 7",type=int,choices=range(1,8),dest="degrees_available")
cmdparse.add_argument("--intervals","-i",nargs="*",help="Intervals possible.",type=int,choices=range(1,8))

cmdargs = cmdparse.parse_args()


def main():
    # parsing config
    with open ("config") as f:
        raw_config = f.read()

    parser = config_parser.ConfigParser(raw_config)

    config = config_checker.ConfigModifier(parser.data,config_parser.Config(cmdargs.__dict__))()

    # notes generation

    selector = notes_generator.NotesSelector(config)
    generator = notes_generator.NotesGenerator(selector,selector.config.number)
    return generator

if __name__ == "__main__":
    print(main()())




