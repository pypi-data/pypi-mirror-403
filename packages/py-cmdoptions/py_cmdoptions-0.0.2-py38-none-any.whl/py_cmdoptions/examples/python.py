from py_cmdoptions.executor import Executor, Option

class Python(Executor):
    cmd:str = 'python'

class Version(Option):
    opt:str = '--version'

class Module(Option):
    opt:str = '-m'

class Pip(Option):
    opt:str = 'pip'

def main():
    py = Python()
    py.addOption(Version())
    py.execute()

    py.clearOptions()
    
    py.addOption(Module(Pip('list')))
    py.execute()


if __name__ == '__main__':
    main()