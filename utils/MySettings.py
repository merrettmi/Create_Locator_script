#!/usr/bin/env python3
# -*- coding: utf-8 -*-
##############################################################################################################################################################
''' 
    MySettings.py

Add this to you pre-main  (if you have setup logging -- remove the logger line if not)

    ##### configuration settings (howmany times have i run the program)
    config = mySettings( (__file__).replace('.py', '') , isTesting)
    runCounter = config.getRunCounter()
    
    logger.info( f'+_+_+_+_+_+_+_+_+_+_+_+_+_+_+_+_+_+_+_+_+_+_+_{runCounter}')


'''
__version__ = '2.2.3'
__author__ = "Mike Merrett"
__updated__ = '2026-02-22 22:00:15'
###############################################################################


# import json
import os
import sys
import configparser
from datetime import datetime
from enum import Enum

# from os import getenv
#server = getenv("PYMSSQL_TEST_SERVER")


# -----------------------------------------------------------------
# -----------------------------------------------------------------
class MySettings():  # configparser):

    INIfile = 'config.ini'
    curApp = 'unknown'
    config = None

    isShowingDebug=False

    class fldType(Enum):
        Bool = 'Bool'
        Int = 'Int'
        Str = 'Str'
        Float = 'Float'
        #Json = 'Json'


    #-----------------------------------------------------------------
    def __init__(self, fn , showDebug=False)-> None:
        self.curApp = (os.path.basename(fn)).replace('.py', '')
        self.config = configparser.ConfigParser(allow_no_value=True)
        if os.path.exists(self.INIfile):
            self.config.read( self.INIfile)
        else:
            self.reset()


        # # # # # # # print(os.path.abspath(self.INIfile))

        # # # # # # # from pathlib import Path
        # # # # # # # print(Path(self.INIfile).resolve())  # Output: C:\path\to\your\script.py
        # # # # # # # self.isShowingDebug = showDebug

        if not self.config.has_section(self.curApp):
            self.config.add_section(self.curApp)

        if self.isShowingDebug:
            self.dump()

    #-----------------------------------------------------------------
    ###                        json.dumps({"auto_create": True,
    ###                                    "merge_playlists": False})),

    resetSettings = {
        "thread_count": ("Performance", 4, fldType.Int),

        "auto_update_check": ("General", True, fldType.Bool),
        "custom_naming_format": ("General", "{artist} - {title}", fldType.Str),
        "dark_mode": ("General", False, fldType.Bool),
        "estimated_time_remaining": ("General", True, fldType.Bool),
        "input_folder": ("General", "", fldType.Str),
        "log_file_path": ("General", "logs/conversion_log.txt", fldType.Str),
        "multi_folder_support": ("General", True, fldType.Bool),
        "output_folder": ("General", "", fldType.Str),
        "reset_sorting": ("General", False, fldType.Bool),

        "auto_create": ("PlayList Rules", True, fldType.Bool),
        "merge_playlists": ("PlayList Rules", False, fldType.Bool),

        "speech_notifications": ("Speech", True, fldType.Bool),
        "speech_volume": ("Speech", 1.0, fldType.Float),

        "window_height": ("Window", 600, fldType.Int),
        "window_width": ("Window", 800, fldType.Int),
        "window_x": ("Window", 200, fldType.Int),
        "window_y": ("Window", 200, fldType.Int),

        "server": ("DatabaseSettings", "192.168.3.205", fldType.Str),
        "port": ("DatabaseSettings", 3306, fldType.Int),
        "database": ("DatabaseSettings", "MikesMusicCopierOrganizer", fldType.Str),
        "username": ("DatabaseSettings", "MikesMusicCopierOrganizer", fldType.Str),
        "password": ("DatabaseSettings", "Unknown", fldType.Str),

        "Mid":("Equalizer", 0, fldType.Int),
        "Bass":("Equalizer", 0, fldType.Int),
        "Treble":("Equalizer", 0, fldType.Int),
        "EqualizerEnabled":("Equalizer", False, fldType.Bool),

    }
    # # [DatabaseSettings]
    # # server = 192.168.3.205
    # # port = 3306
    # # database = MikesMusicCopierOrganizer
    # # username = MikesMusicCopierOrganizer
    # # password = Mikes5Music8Copie3Organizer43

    #-----------------------------------------------------------------
    def reset(self):
        for k,v in self.resetSettings.items():
            match( v[2]):
                case MySettings.fldType.Bool:
                    self.setBool(v[0], k, v[1])
                case MySettings.fldType.Int:
                    self.setStr(v[0], k, str(v[1]))
                case MySettings.fldType.Float:
                    self.setStr(v[0], k, str(v[1]))
                #case MySettings.fldType.Json:
                #    self.setStr(v[0], k, json.dumps(v[1]))
                case MySettings.fldType.Str:
                    self.setStr(v[0], k,str(v[1]))

        self.writeConfig()

    #-----------------------------------------------------------------
    def save(self):
        self.writeConfig()

    #-----------------------------------------------------------------
    def writeConfig(self) -> None:
        if self.isShowingDebug:
            self.dump()

        with open(self.INIfile, 'w') as configfile:
            self.config.write(configfile)
        pass

    #-----------------------------------------------------------------
    def getRunCounter(self) -> int:

        if not self.config.has_section(self.curApp):
            self.config.add_section(self.curApp)

        ver = self.config.getint( self.curApp,'RunCounters', fallback=0)

        #update the ini now (just incase it doesnt get written later)
        self.config.set( self.curApp, 'RunCounters', str(ver+1))
        self.config.set( self.curApp, 'LastRunTime', str(datetime.now()))

        self.writeConfig()
        return ver

    #-----------------------------------------------------------------
    def getBool(self, section,  key: str, fallbackVal: bool) -> bool:
        var = self.config.getboolean(self.curApp, key, fallback=fallbackVal)
        return var

    #-----------------------------------------------------------------
    def setBool(self, section, key: str, value: bool) -> None:
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, key, str(value))
        self.writeConfig()

    #-----------------------------------------------------------------
    def getFloat(self, section, key: str, fallbackVal: float = 0.0) -> float:
        if not self.config.has_section(section):
            self.config.add_section(section)
        return self.config.getfloat(section, key, fallback=fallbackVal)

    #-----------------------------------------------------------------
    def setFloat(self, section, key: str, value: float) -> None:
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, key, str(value))
        self.writeConfig()

    #-----------------------------------------------------------------
    def getEnv(self, key) -> str|int:
        return os.environ.get(key)

    #-----------------------------------------------------------------
    def setEnv( self, section, key, value) -> None:
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, key, value)
        self.writeConfig()

    #-----------------------------------------------------------------
    def getInt( self, section, key, fallbackVal= 0) -> int:
        if not self.config.has_section(section):
            self.config.add_section(section)
        return self.config.getint(section, key, fallback=fallbackVal)
    #-----------------------------------------------------------------
    def setInt( self, section, key, value: int) -> None:
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, key, str(value))
        self.writeConfig()

    #-----------------------------------------------------------------
    def getStr( self, section, key, fallbackVal= '') -> str|None:
        return self.config.get(section, key, fallback=fallbackVal)

    #-----------------------------------------------------------------
    def setStr( self, section, key, value)-> None:

        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, key, value)
        self.writeConfig()


    #-----------------------------------------------------------------
    # def dump(self)-> None:
    #     print('vvvvvvvvvvvvvv')
    #     print( f'ini file={self.INIfile}')
    #     print( f'curApp={self.curApp}')
    #     #print( f'conf={self.config}')

    #     print( f'sections={ self.config.sections() }')
    #     print( f'defaults={ self.config.defaults() }')




    #     for i in self.config.sections() :
    #         print (f'>>>[{ i }]')
    #         print(self.config.items(i))


    #     x = self.getEnv('USERNAME')
    #     print(f'getEnv()={x}')

    #     x = self.getEnv('TEMP')
    #     print(f'getEnv()={x}')

    #     x = os.environ.get('TEMP')
    #     print(f'os.environ.get()={x}')

    #     p = self.config.get('GlobalAttachmentRepository', 'db_password')

    #     print( p)
    #     print ( str(hash(p)))

    #     print('##############')

    #     from cryptography.fernet import Fernet
    #     # Put this somewhere safe!
    #     key = Fernet.generate_key()
    #     print(key)
    #     f = Fernet(key)
    #     token = f.encrypt(b"A really secret message. Not for prying eyes.")
    #     print(token)
    #     #token
    #     #b'...'
    #     x = f.decrypt(token)
    #     print(x)
    #     #b'A really secret message. Not for prying eyes.'
    #     print('$$$$$$$$$$$$$')

    #     import keyring
    #     keyring.set_password('GlobalAttachmentRepository', 'sde','GoldRushSDE')

    #     pwd = keyring.get_password('GlobalAttachmentRepository','sde',)
    #     print(pwd)


    #     print('@@@@@@@@@')




MySettings  = MySettings('config.ini')        #'../../config.ini')



#-----------------------------------------------------------------
if __name__ == '__main__':
    print ('this must be called from another module')
    sys.exit(-1)