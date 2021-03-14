#!/usr/bin/python3
# -*-coding:Utf-8 -*
#Deus, in adjutorium meum intende

import re

class Config(dict):
    def __init__(self, *args, **kwargs):
        super(Config, self).__init__(*args, **kwargs)
        self.__dict__ = self

    def wash(self):
        """Deletes values that are empty"""
        for k,v in tuple(self.items()):
            if isinstance(v,Config):
                v.wash()
            if v is None or len(v) == 0:
                del(self[k])


class ConfigParser:
    def __init__(self,raw):
        self.raw = raw
        self._remove_comments()
        self._split()
        self._fill()

    def _remove_comments(self):
        """Takes raw and remove every comment
        A comment must be a the end of the line between parentheses"""
        self._last_state = re.sub(r"\(.*\)","",self.raw)

    def _split(self):
        """Split raw in lines and packs of characters delimited by spaces"""
        self._last_state = [line.split() for line in self._last_state.split("\n")]

    def _fill_part(self,lines, idx, level):
        """recursive function"""
        # TODO il y a un problème lors du retour d'un niveau plus bas:
        # la fonction fait comme si tout était terminé
        data = dict()
        name = ""
        for i in range(idx,len(lines)):
            line = lines[i]
            if line == []:
                continue
            if name:
                res = line
                if len(line) == 1:
                    res = line[0]
                elif line[0] == "#"*(level+1):
                    # higher level
                    res = self._fill_part(lines,i,level+1)
                data[name] = self.__to__int(res)
                name = ""
            elif line[0] == "#"*level:
                name = line[1]
            elif "#" in line[0]:
                #lower level
                return Config(data)
        return Config(data)

    def _fill(self):
        """Fill the config class"""
        self.data = Config(self._fill_part(self._last_state,0,1))

    def __to__int(self, data):
        """Tries to change data to int"""
        try:
            if isinstance(data,list):
                return [int(elt) for elt in data]
            return int(data)
        except (TypeError, ValueError):
            return data
