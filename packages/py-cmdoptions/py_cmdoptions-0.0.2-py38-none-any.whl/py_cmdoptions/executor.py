from __future__ import annotations
from typing import Tuple, Union
from os.path import dirname
import os, subprocess

if __name__ == '__main__':
    import sys
    from os.path import dirname
    sys.path.append(dirname(dirname(__file__))) # append './../' to sys.path

from py_cmdoptions.option import Option, OptionSet

class Executor:
    cmd:str = 'echo'
    options:OptionSet

    def __init__(self):
        self.options = OptionSet()

    def __str__(self):
        return type(self).getCommand(self.options)
    
    def addOption(self, option:Union[Option, str])->Executor:
        self.options.addOption(option)
        return self

    def addOptions(self, options:Tuple[Union[Option, str]])->Executor:
        for option in options:
            self.addOption(option)
        return self
    
    def clearOptions(self):
        self.options.clearOptions()
    
    def execute(self):
        return type(self)._execute(f'{self}')
    
    def run(self):
        return type(self)._run(f'{self}')
    
    def process(self):
        return type(self)._process(f'{self}')
    
    @classmethod
    def getCommand(cls, options:OptionSet)->str:
        cmd = []
        args = f'{options}'
        if(len(cls.cmd) > 0):
            cmd.append(cls.cmd)
        if(len(args) > 0):
            cmd.append(args)
        return ' '.join(f'{__}' for __ in cmd)
    
    @classmethod
    def _execute(cls, cmd:str)->int:
        return os.system(cmd)

    @classmethod
    def _run(cls, cmd:str)->subprocess.CompletedProcess:
        res = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return res

    @classmethod
    def _process(cls, cmd:str)->subprocess.Popen[bytes]:
        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return proc

def main():
    exec = Executor()
    exec.addOption('666')
    exec.addOption(Option(777))
    exec.execute()
    print(exec.run().stdout)

if __name__ == '__main__':
    main()