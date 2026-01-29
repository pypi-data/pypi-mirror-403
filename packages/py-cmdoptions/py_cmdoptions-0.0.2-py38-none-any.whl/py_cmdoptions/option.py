from __future__ import annotations
from typing import Any, List, Union, Tuple

# `opt` is a class property.
# `prio` and `value` are object properties.
class Option:
    opt:str = ''
    prio:int = 0 # Option default priority
    value:str

    def __init__(self, val:Any=''):
        self.value = f'{val}'
        self.prio = type(self).prio
    
    # to Arg
    def __str__(self):
        arg = []
        if(len(type(self).opt) > 0):
            arg.append(type(self).opt)
        if(len(self.value) > 0):
            arg.append(self.value)
        return ' '.join(f'{__}' for __ in arg)
    
    # set Option priority
    def setPriority(self, prio:int)->Option:
        self.prio = prio
        return self

# OptionSet is a list of Option
# 1. add Options to OptionSet
# 2. convert OptionSet to Args
class OptionSet:
    __options:List[Option]

    def __init__(self):
        self.__options = []
    
    # to Args(sort by option priority)
    def __str__(self):
        options = sorted(self.__options, key=lambda opt: opt.prio)
        return ' '.join(f'{option}' for option in options)
    
    # add a Option to OptionSet
    def addOption(self, option:Union[Option, str])->OptionSet:
        if(isinstance(option, str)):
            option = Option(option)
        if(isinstance(option, Option)):
            self.__options.append(option)
        else:
            print(f'{option} is a {type(option)}!')
        return self
    
    # add Options to OptionSet
    def addOptions(self, options:Tuple[Union[Option, str]])->OptionSet:
        for option in options:
            self.addOption(option)
        return self

    # clear all Options
    def clearOptions(self):
        self.__options.clear()

# you can extend `Option` to override `opt` and `prio`, like this:
class __TestOption(Option):
    prio:int = 1
    opt:str = '-test'

    def __init__(self, val:int):
        super().__init__(val)

def main():
    optset = OptionSet()
    optset.addOption(Option('prio0_0'))
    optset.addOption(__TestOption('prio1_0'))
    optset.addOption(__TestOption('prio1_1'))
    optset.addOption(__TestOption('prio1_2').setPriority(-1))
    optset.addOption(Option('prio0_1'))
    print(optset)

if __name__ == '__main__':
    main()