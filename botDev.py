from dev.Session import Session
from dev.Loader import Loader
import sys


def main():
    session = Session()
    if (not session.isConnected()):
        return

    loader = Loader()
    loader.load(sys.argv, ["bot", "algorithm", "fxcm", "FxcmBacktest"])

    while True:
        try:
            inputResult = input("# Press 'return' to start the bot")
            if inputResult == '':
                print("# Press 'Crtl-C' to end the bot")
                loader.run(session, sys.argv)
                print("\n# Press 'Crtl-D' to close the program")
        except EOFError:
            print("\nClosing connection...")
            session.close()
            break


if __name__ == "__main__":
    main()
