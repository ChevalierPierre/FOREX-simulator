import fxcmpy


class Session():
    def __init__(self):
        self.__connection__ = None

        try:
            print("Connecting...")
            self.__connection__ = fxcmpy.fxcmpy(config_file='config/fxcm.cfg')
            print("Connection successfull!")
        except Exception as e:
            self.__connection__ = None
            print("Connection failed : ", e)

    def close(self):
        if self.__connection__ != None:
            self.__connection__.close()
            print("Connection closed!")

    def isConnected(self):
        if self.__connection__ == None:
            return False
        return self.__connection__.is_connected()

    def getConnection(self):
        if self.isConnected():
            return self.__connection__
