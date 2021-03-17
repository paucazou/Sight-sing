#!/usr/bin/python3
# -*-coding:Utf-8 -*
#Deus, in adjutorium meum intende

import mingus.containers.note as mcn

DEGREES = "I II III IV V VI VII".split()

def convert_degree(val):
    """Convert val from numerical to roman numeral
    or the opposite"""
    values = {i+1:deg for i, deg in enumerate(DEGREES)}
    values.update({deg:i+1 for i,deg in enumerate(DEGREES)})
    return values[val]

class ConfigModifier:
    """Modifies the configuration loaded:
    checks the command line first,
    second the viability"""
    def __init__(self,file_config, cmd_config):
        self.file_config = file_config
        self.cmd_config = cmd_config

    def _update_file_config_with_cmd_config(self):
        """Updates file config with command line
        config"""
        self.final_config = self.file_config

        if self.cmd_config is not None:
            self.cmd_config.wash()
            self.final_config.update(self.cmd_config)

        if "degrees_available" in self.cmd_config:
            keys_to_remove = [deg for deg in self.final_config.degrees.keys() if convert_degree(deg) not in self.cmd_config.degrees_available]
            for k in keys_to_remove:
                del(self.final_config.degrees[k])
                
        if "intervals" in self.cmd_config:
            # set intervals available
            for deg in self.final_config.degrees.keys():
                self.final_config.degrees[deg] = self.cmd_config.intervals


    def __call__(self):
        self._update_file_config_with_cmd_config()

        # check notes number
        if self.final_config.number < 3:
            print(f"Number of notes too low: {self.final_config.number} set to minimum 3")
            self.final_config.number = 3

        # check tessitura configuration
        n1, n2 = sorted([mcn.Note(n) for n in self.final_config.tessitura])
        if n1.measure(n2) < 12:
            n2.octave_up()
            print(f"Tessitura too low: {n1.measure(n2)}. One octave at least is required. New limits are: {n1}, {n2}")

        self.final_config.tessitura = (n1,n2)

        # check degrees intervals: at least second and unison
        changed = []
        for degree,value in self.final_config.degrees.items():
            for i in (1,2):
                if i not in value:
                    print(i)
                    value.append(i)
                    changed.append(degree)
        if changed != []:
            print(f"""Unisons and seconds are required for every degree. Degrees changed: {", ".join(changed)}""")

        # set degrees available
        if "degrees_available" not in self.final_config:
            self.final_config.degrees_available = [
                    DEGREES.index(k) + 1 for k in self.final_config.degrees.keys()
                    ]

        # add a convenient degrees alias with numerical values
        self.final_config.degrees_numeric = {
                DEGREES.index(k)+1 : v 
                for k,v in self.final_config.degrees.items()
                }

        

        # set balance of intervals
        self.final_config.interval_priority.reverse()

        return self.final_config


