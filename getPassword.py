#
"""
    getPassword.py
    - a module to get passwords from an ini file
    TODO: encode the username?  - and use it as a piece of knowledge to decrypt the password????
    
    - it can be called from the command line or from another python module
    - the main idea is to separate the password from the key and the key is stored in a
            root directory that should never get included in a git add
        - and the actual password is never stored anywhere when it is unencrypted
    - only printing the decrypted password to the console or returning it from a function
        is useful when calling this from a batch file and putting it into a environment variable with this code:

# USEFULL:   -                                 note the database name vvvvvvvvvvvv inside the quotes
# USEFULL:        @echo for database DynamicAsset
# USEFULL:                @FOR /F "delims=" %%A IN ('py getPassword.py DynamicAsset') DO SET MYPASSWORD=%%A
# USEFULL:                @ECHO     The value is: %MYPASSWORD%


    the INI file with the decode keys is GlobalImportantStuff.ini
    it will by default look here: r"\\vm-gis-prd1\gis_manager\GlobalImportantStuff.ini"
    for that ini
    the other ini containing the passwords is by default config.ini
    which will be in the parent of the current working directory or in the working directory
    if there is no config.ini in the parent directory

    it will simply print or return the password without any other text
    and it will fail silently if it cannot find the password

    this module will also generate a new key and a new password for you to enter into the ini files

    At a Dos prompt or dos batch file you can run this as:
        getPassword.py 'DatabaseName'   - will return the password for the database
    or
        getPassword.py 'DatabaseName' 'passwordToEncode' - will encode the password and return the new key and password

    from another python module you can call it like this:
            (the first parameter in the list is ignored (it is basically matching the sys.argv of calling it from the command line))

        import getPassword
        args = [ 'test scripty thing', 'DynamicGeneral']
        pw = getPassword.main(args)
        print(f"the password is '{pw}'")
    or

        import getPassword
        decodeKey, password = getPassword.main( ['getPassword.py', 'DatabaseName', 'passwordToEncode'])
        print(f"{decodeKey=} {password=}")

# NOTE: all the comment out print statements are for debugging and can be removed or uncommented as needed

# USEFULL: most of my problems with this module have been making sure which INI files are being used
# USEFULL: you can use the dump() method of the MySettings class to see what is in the INI files
# USEFULL:   or you can use the ini.giveINIfile() method to see which INI file is being used


    10Jul25 M.Merrett - initial write
    22Jul25 M.merrett - added ability to call this from another pythong module and give the same password back

"""

__version__ = "0.3.0"
__author__ = "Mike Merrett"
__updated__ = "2025-07-24 14:18:11"

###############################################################################

from cryptography.fernet import Fernet
import traceback
from utils.MySettings import MySettings
import sys
import os   


# -----------------------------------------------------------------
"""    do_init() - this function will parse the command line arguments
    it will return the database name, the password to encode (if any) and a boolean to indicate if it should rebuild the passwords
    if the database name is not given it will default to 'DynamicGeneral
    if the password to encode is not given it will default to None
    if the third parameter is 'Rebuild' it will return True, otherwise it will return False
"""


def do_init(args=sys.argv):
    doRebuild = False

    if len(args) < 2 or not args[1].strip():
        databaseName = r"DynamicGeneral".lower()
    else:
        databaseName = args[1].lower()
    # print( f"{databaseName=}")

    if len(args) == 3 and args[2].strip():
        pwToEncode = args[2]
    else:
        pwToEncode = None
    # print( f"{pwToEncode=}")

    if len(args) == 4 and args[3].strip():
        if args[3] == "Rebuild":
            doRebuild = True
        else:
            doRebuild = False

    return databaseName, pwToEncode, doRebuild


# -----------------------------------------------------------------
"""    giveGlobalINI() - this function will return the GlobalINI object
    it will check if the file exists and if it does not it will print an error message and exit
"""


def giveGlobalINI(
    GlobalINILocation=r"\\vm-gis-prd1\gis_manager\GlobalImportantStuff.ini",
):
    if os.path.isfile(GlobalINILocation):
        # print (f"file does exist: {GlobalINILocation}")
        pass
    else:
        print("file does exist")
        sys.exit(-1)

    GlobalINI = MySettings(GlobalINILocation)
    # GlobalINI.dump()

    return GlobalINI


# -----------------------------------------------------------------
"""Fencode2() - this function will encode the password using the given Fernet key
"""


def Fencode2(FormatSeed, pwToEncode):
    newpw = FormatSeed.encrypt(pwToEncode.encode())
    return newpw


# -----------------------------------------------------------------
def Fencode3(GlobalINI, databaseName, pwToEncode):
    fernetKey = giveEncrytionKey(databaseName, GlobalINI)
    newpw = Fencode2(fernetKey, pwToEncode)
    pass


# -----------------------------------------------------------------
""" Fdecode() - this function will decode the password using the given Fernet key
"""


def Fdecode(FernetSeed, token):
    # print(f"here  {FernetSeed=}  {token=}")
    f = Fernet(FernetSeed.encode())
    value = f.decrypt(token)
    return value


# -----------------------------------------------------------------
"""getINIKey() - this function will return the key for the given database name from the GlobalINI
    it will look in the DatabaseENC section of the GlobalINI
    if the key is not found it will return None
    """


def getINIKey(databaseName, GlobalINI):
    section = f"DatabaseENC"
    # print(f"{section=}")
    inikey = GlobalINI.getStr(section, databaseName)
    # print( f"{inikey=}")
    return inikey


# -----------------------------------------------------------------
""" giveEncrytionKey() - this function will return the Fernet key for the given database name
    it will look in the DatabaseENC section of the GlobalINI
    if the key is not found it will return None
"""


def giveEncrytionKey(databaseName, GlobalINI):
    inikey = getINIKey(databaseName, GlobalINI)
    # print (f"{inikey=}")
    fernetKey = Fernet(inikey.encode())
    return fernetKey


# -----------------------------------------------------------------
""" this will rebuild and replace all the passwords and the encryption keys in the GlobalINI and the config.ini

# TODO: this has not been fully tested yet and should not be used in production until it has been tested

"""


def doTheRebuild(GlobalINI):
    for key, value in GlobalINI.items("DatabaseENC"):
        print(f"{ key=} {value}")

        k = key.replace("'", "")
        print(f"{k=}")

        inikey = GlobalINI.getStr("DatabaseENC", k)
        print(f"{inikey=}")

        oldToken = mySettings("Database", f"password_{k}")
        print(f"{oldToken=}")

        oldPW = Fdecode(inikey, oldToken)
        print(f"{oldPW=}")

        newFernetKeySeed = Fernet.generate_key()
        print(f"{newFernetKeySeed=}")

        newFernetKey = Fernet(newFernetKeySeed)
        print(f"{newFernetKey=}")

        newpw = newFernetKey.encrypt(oldPW)
        print(f"{newpw=}")

        print("-=-=-=-=-=-")
        GlobalINI.setStr("DatabaseENC", k, newFernetKeySeed.decode("utf-8"))
        print("after globalini")

        mySettings.setStr("Database", f"password_{k}", newpw.decode("utf-8"))
        print("after may settings")


# -----------------------------------------------------------------
""" doPasswordEncode() - this function will encode the password for the given database name
    it will return the Fernet key and the encoded password
    it will generate a new Fernet key if one is not found in the GlobalINI
"""


def doPasswordEncode(GlobalINI, databaseName, pwToEncode):
    # print("about to encode a new password   ")
    # fernetKey = giveEncrytionKey(databaseName, GlobalINI)
    fernetKey = Fernet.generate_key()
    # print(f"{fernetKey=}")

    FernetSeed = Fernet(fernetKey)

    newpw = FernetSeed.encrypt(pwToEncode.encode())
    # print ( f"{newpw=}" )

    # newpw = Fencode2(fernetKey, pwToEncode )
    # print ( f"{newpw=}" )

    return fernetKey, newpw


# -----------------------------------------------------------------
""" doGivePassword() - this function will return the password for the given database name
    it will look in the GlobalINI for the key and then decode the password from the config.ini
"""


def doGivePassword(GlobalINI, databaseName):
    # GlobalINI.dump()
    inikey = getINIKey(databaseName, GlobalINI)
    # print(f"{inikey=}" )

    # mySettings.dump()
    aToken = mySettings.getStr("Database", f"password_{databaseName}")
    # print( f"( 'Database', f'password_{databaseName}')")
    # print( f"{aToken=}")

    # aPW =  fernetKey.decrypt( aToken)
    # print(f"{aPW=}")
    # print (aPW.decode('utf-8'))

    aPW = Fdecode(inikey, aToken)
    # # aPW = Fdecode( fernetKey, aToken)
    # print(aPW.decode('utf-8'))
    return aPW.decode("utf-8")


# -----------------------------------------------------------------
""" everything runs thru this main function
    it is called from the command line, or from other modules
"""


# -----------------------------------------------------------------
def main(
    args, GlobalINILocation=r"\\vm-gis-prd1\gis_manager\GlobalImportantStuff.ini"
):
    # print( f"getPassword.py main() called with {args=}")
    try:
        databaseName, pwToEncode, doRebuild = do_init(args)
        # print (f"{databaseName=}   {pwToEncode=}  {doRebuild=}")

        GlobalINI = giveGlobalINI(
            GlobalINILocation=r"\\vm-gis-prd1\gis_manager\\GlobalImportantStuff.ini"
        )

        if doRebuild:
            # print ('here')
            doTheRebuild(GlobalINI)
        else:
            # print('not here')
            if pwToEncode is not None:
                # print(" -  ")
                decodeKey, password = doPasswordEncode(
                    GlobalINI, databaseName, pwToEncode
                )

                dbNamelow = databaseName.lower()
                print()
                print(
                    f"in GlobalINI, section: [DatabaseENC],   \n{dbNamelow} =  {decodeKey.decode()}"
                )
                print()
                print(
                    f"And in the local config.ini , section: [Database], \npassword_{dbNamelow} = {password.decode()} "
                )
                print()

                return decodeKey, password
            else:
                # print ('somewhere else')
                password = doGivePassword(GlobalINI, databaseName)

        if __name__ == "__main__":
            print(password)
        else:
            return password
    except Exception as e:
        # tb_str = "".join(traceback.format_exception(e))
        # print(tb_str)
        # print(
        #     "vvvvvvvvvv Check that these are the expected ini files !!!!!!vvvvvvvvvvvvvv"
        # )
        # print(f" configini file = {mySettings.giveINIfile()}")
        # print(f" globalini file = {GlobalINI.giveINIfile()}")
        # print(f"Key decoding failed: {e}")
        pass



# -----------------------------------------------------------------
if __name__ == "__main__":
    main(sys.argv)
