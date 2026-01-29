from typing import List
from os.path import dirname
from pathlib import Path
import os

# Env tool:
# 1. get PATH as a list 
# 2. add a path to PATH
class Env:
    @classmethod
    def getPath(cls)->List[str]:
        return os.environ['PATH'].split(os.pathsep)

    @classmethod
    def addPath(cls, path:str):
        if(os.path.isdir(path)):
            path = Path(path)
        elif(os.path.isfile(path)):
            path = dirname(path)
        PATH = cls.getPath()
        if(path not in PATH):
            PATH.insert(0, f'{path}')
            os.environ['PATH'] = os.pathsep.join(PATH)

def main():
    print(Env.getPath())
    Env.addPath('/usr/local')
    print(Env.getPath())

if __name__ == '__main__':
    main()