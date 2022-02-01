from importlib import reload
import tools.utils as utils
import sys


class Loader():
    config = None
    botFile = None
    algoFile = None
    botModuleFiles = list()

    def load(self, argv, botModuleFilenames):
        try:
            self.config = utils.parseConfigFile(argv)
            self.botFile = __import__("bot")
            self.algoFile = __import__(self.config['strategy'])
            for botModuleFilename in botModuleFilenames:
                self.botModuleFiles.append(__import__(botModuleFilename))
        except Exception as e:
            print("Loading failed : ", e)
            sys.exit()

    def run(self, session, argv):
        for botModuleFile in self.botModuleFiles:
            reload(botModuleFile)
        self.botFile = reload(self.botFile)
        self.algoFile = reload(self.algoFile)

        try:
            getattr(self.botFile, "mainDev")(self.config, getattr(
                self.algoFile, self.config['strategy']), session.getConnection(), argv)
        except Exception as e:
            print("Error: ", e)
