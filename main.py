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

_scales = []
for k in mcs.keys:
    _scales.append(k[0])
    _scales.append(k[1])

cmdparse.add_argument("--scale","-s",help="Select which scale you want to use. Minor scales are specified in lower case: C = major; c = minor. To use a chromatic scale, enter the word 'chromatic'.",choices=_scales)
cmdparse.add_argument("--number","-n",help="Change number of notes played. Min: 3",type=int,choices=range(3,500))
cmdparse.add_argument("--tessitura","-t",nargs=2,help="Tessitura of the melody. Example: C-4 A-6. Minimum: an octave")

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




