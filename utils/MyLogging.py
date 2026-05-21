#!/usr/bin/env python3
# -*- coding: utf-8 -*-
###############################################################################
'''
   MyLogging.py

   class CustomFormatter

###!!!!!! - in your main have these lines first!!!!
###   logger = logging.getLogger(__file__)
###   CustomFormatter.setupLogger(logger, (__file__).replace('.py', '.log'))
###   sys.excepthook = handle_exception

M.Merrett-took am/pm out of screen output format

'''
__version__ = '2.0.6'
__author__ = 'Mike Merrett'
__updated__ = '2026-03-28 01:18:57'
###############################################################################

import logging.handlers
import logging
import traceback
import time
#import functools
# import json

from utils.MySettings import MySettings
import sys
import os
from logging.handlers import RotatingFileHandler

isTesting = False


#=================================================================
#=================================================================
#=================================================================
def log_decorator(func):
    """
    A decorator to log function calls, arguments, and return values.
    
    This decorator logs the function name, arguments, and return value using the logger set up by CustomFormatter.
    It also handles exceptions and logs them as errors.
    :param func: The function to be decorated.
    :return: The wrapped function with logging functionality.

        Example usage:
            @log_decorator
            def my_function(arg1, arg2):
                return arg1 + arg2
                    result = my_function(1, 2)
                    # This will log the function call, arguments, and return value.
                    #   
                    #   The log messages will be formatted using the CustomFormatter class.
                    #               The logger will also handle exceptions and log them as errors.
                    #               The log messages will be colored based on their severity level.  
    """

    def wrapper(*args, **kwargs):
        logger = CustomFormatter.theLogger  # Use the logger set up by CustomFormatter
        #logger.decorator("@+@                 ")
        logger.decorator(f"Calling function: {func.__name__}")
        logger.decorator(f"Arguments: {args}, {kwargs}")
        try:
            start_time = time.perf_counter()  # Start timing
            result = func(*args, **kwargs)
            logger.decorator(f"Return value: {result}")
            logger.decorator("@-@                 ")
            end_time = time.perf_counter()  # End timing
            logger.decorator(f"Function {func.__name__} took {end_time - start_time:.6f} seconds")
            print ("^")
            return result
        except Exception as e:
            logger.decorator_error(f"Exception in {func.__name__}: {e}")
            logger.decorator_error(traceback.format_exc())
            logger.decorator("@e@                 ")
            raise
    return wrapper


#=================================================================
#=================================================================
class ExcludeLevelFilter(logging.Filter):
    """
    A logging filter to exclude specific logging levels.
    This filter can be used to prevent certain log levels from being processed by the logger.

    Example usage:
        logger = logging.getLogger(__name__)
        exclude_filter = ExcludeLevelFilter()
        logger.addFilter(exclude_filter)

        # To exclude a specific level, use:
        exclude_filter.addFilterLevel(logging.DEBUG)

        # To remove the exclusion, use:
        exclude_filter.removeFilterLevel(logging.DEBUG)

        # To exclude multiple levels, you can use:
        exclude_filter.addFilterLevel(logging.DEBUG)
        exclude_filter.addFilterLevel(logging.INFO)
        exclude_filter.addFilterLevel(logging.WARNING)
        exclude_filter.addFilterLevel(logging.ERROR)
        exclude_filter.addFilterLevel(logging.CRITICAL)


    """
    Filters = set()

    def __init__(self, name=""):
        """
        Initializes the filter with an empty set of levels to exclude.
        :param name: Optional name for the filter.
        """
        super().__init__(name)
        #######self.Filters = set()

    def filter(self, record):
        """
        Filters out log records based on the excluded levels.
        :param record: The log record to check.
        :return: True if the record should be logged, False otherwise.
        """
        return record.levelno not in self.Filters

    def addFilterLevel(self, level):
        """
        Adds a logging level to the exclusion list.
        :param level: The logging level to exclude.
        """
        self.Filters.add(level)

    def removeFilterLevel(self, level):
        """
        Removes a logging level from the exclusion list.
        :param level: The logging level to include again.
        """
        self.Filters.discard(level)



#=================================================================
#=================================================================
#=================================================================
#=================================================================
class CustomFormatter(logging.Formatter):
    """
    Custom logging formatter to add colors and formats to log messages.
    This formatter can be used to customize the appearance of log messages based on their severity level.

    Example usage:
        logger = logging.getLogger(__name__)
        formatter = CustomFormatter()
        handler = logging.StreamHandler()

        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)

        logger.debug('This is a debug message')

        logger.info('This is an info message')
        logger.warning('This is a warning message')
        logger.error('This is an error message')
        logger.critical('This is a critical message')
        logger.query('This is a query message')
        logger.trace('This is a trace message')
        logger.tracea('This is a tracea message')


"""
    wantLevelName = False

    DEFAULT_TEXT_MSG = "~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~"
    MARKER_LOW = 300
    MARKER_HIGH = 399

    grey =      "\x1b[38;20m"
    yellow =    "\x1b[33;20m"
    red =       "\x1b[31;20m"
    bold_red =  "\x1b[31;1m"
    blue=       "\x1b[36;1m"
    green =     "\x1b[1;32m"
    redOnyellow ="\x1b[1;33;41m"
    blackOnRed ="\x1b[62;30;41m"

    reset = "\x1b[0m"
    theFilename= None
    theLogger=None

    # formatStr = "%(filename)s|%(lineno)4s|%(funcName)s|%(levelname)7s| %(message)s"
    # formatStr = "%(filename)s:%(lineno)4s|%(funcName)s| %(message)s"
    formatStr = "%(filename)s:%(lineno)4s|%(funcName)s|%(levelname)7s| %(message)s"
    # if wantLevelName:
        ###formatStr = "%(asctime)s|%(lineno)4s |%(levelname)8s| %(message)s"
        #formatStr = "%(asctime)s|%(funcName)s|%(lineno)4s |%(levelname)7s| %(message)s"
    # else:
        # formatStr = "%(filename)s|%(funcName)s|%(lineno)4s| %(message)s"

    FORMATS = {
         logging.DEBUG:    green    + formatStr + reset
        ,logging.INFO:     blue     + formatStr + reset
        ,logging.WARNING:  yellow   + formatStr + reset
        ,logging.ERROR:    redOnyellow + formatStr + reset
        ,logging.CRITICAL: blackOnRed + formatStr + reset
    }

    #-----------------------------------------------------------------
    def __init__(self, fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt=None):
        """
        Initializes the custom formatter with default format and date format.
        """
        super().__init__(fmt, datefmt)  # Call the base class initializer
        self.default_format = fmt
        self.date_format = datefmt

        # Define additional formats for specific log levels (if needed)
        self.error_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s [ERROR]"

    #-----------------------------------------------------------------
    def format(self, record):
        """
        Formats the log record with custom formatting based on the log level.
        :param record: The log record to format.
        :return: The formatted log message.


        This method overrides the default format method to apply custom formatting
        based on the log level. It also limits the length of the filename and function name.
        """
        FILENAME_SIZE = 15
        FUNCNAME_SIZE = 18
        log_fmt = self.FORMATS.get(record.levelno)

        #or record.msg.strip() ==""
        if not record.msg or record.msg == CustomFormatter.DEFAULT_TEXT_MSG:
            if CustomFormatter.MARKER_LOW <= record.levelno <= CustomFormatter.MARKER_HIGH:
                record.msg= f"{record.levelno- 300:1d}{CustomFormatter.DEFAULT_TEXT_MSG}"
        ##log_fmt = f"{record.levelname} - {self.FORMATS.get(record.levelno)}"

        # limit the file name to FILENAME_SIZE length
        # record.filename = record.filename.replace('.py','')
        if len(record.filename) > FILENAME_SIZE:
            record.filename = record.filename[:FILENAME_SIZE]
        else:
            record.filename = record.filename.rjust(FILENAME_SIZE)

        # Limit funcName to the first 15 characters
        if len(record.funcName) > FUNCNAME_SIZE:
            record.funcName = record.funcName[:FUNCNAME_SIZE]
        else:
            record.funcName = record.funcName.rjust(FUNCNAME_SIZE)

        # abs_path = os.path.abspath(record.filename)
        # rel_path = os.path.relpath(abs_path)
        # record.filename = rel_path

        formatter = logging.Formatter(log_fmt, datefmt='%M:%S')
        return formatter.format(record)

    #-----------------------------------------------------------------
    def add_log_level(level_name, level_num, method_name=None) -> None:
        """
        Adds a new logging level to the logging module and logger class.
        :param level_name: Name of the new logging level.
        :param level_num: Numeric value of the new logging level.
        :param method_name: Optional method name for the new logging level.


        This method dynamically adds a new logging level to the logging module and logger class.
        It also creates a method for logging at the new level.
        If the level name or method name already exists, an AttributeError is raised.


        Example usage:
            CustomFormatter.add_log_level('CUSTOM_LEVEL', 25, 'custom_log')
            logger = logging.getLogger(__name__)
            logger.custom_log('This is a custom log message at level 25')
        """
        if not method_name:
            method_name = level_name.lower()

        if hasattr(logging, level_name):
            raise AttributeError('{} already defined in logging module'.format(level_name))
        if hasattr(logging, method_name):
            raise AttributeError('{} already defined in logging module'.format(method_name))
        if hasattr(logging.getLoggerClass(), method_name):
            raise AttributeError('{} already defined in logger class'.format(method_name))

        # This method was inspired by the answers to Stack Overflow post
        # http://stackoverflow.com/q/2183233/2988730,
        # # # def log_for_level(self, message, *args, **kwargs):
            # # # if self.isEnabledFor(level_num):
                # # # self._log(level_num, message, args, **kwargs)
        def log_for_level(self, message=None, *args, **kwargs):
            stacklevel = kwargs.pop('stacklevel', 2)  # Default to 2 levels up
            if not message:
                message=CustomFormatter.DEFAULT_TEXT_MSG
            if self.isEnabledFor(level_num):
                self._log(level_num, message, args, kwargs, stacklevel=stacklevel)

        def log_to_root(message, *args, **kwargs):
            logging.log(level_num, message, *args, **kwargs)

        logging.addLevelName(level_num, level_name)
        setattr(logging, level_name, level_num)
        setattr(logging.getLoggerClass(), method_name, log_for_level)
        setattr(logging, method_name, log_to_root)


    #-----------------------------------------------------------------
    def cleanLogFile(checkVal: bool) -> None:
        """
        Cleans the log file if checkVal is True.
        :param checkVal: Boolean value to determine if the log file should be cleaned.

        This method truncates the log file to zero length if checkVal is True.
        It also logs a message indicating that the log file has been cleaned.

        Example usage:
            CustomFormatter.cleanLogFile(True)
        """
        #print(f'{checkVal=}')
        #print(f'{CustomFormatter.theFilename=}')
        if checkVal:
            CustomFormatter.theLogger.tracez( f'at clean log file {CustomFormatter.theFilename=}')
            os.truncate( CustomFormatter.theFilename,0)
            CustomFormatter.theLogger.info(' --- Just cleaned(truncated) the file log (this line should be the first in the file) ---')

    #-----------------------------------------------------------------
    def add(name, id, fmt) -> None:
        """
        Adds a new logging level with a custom format.
        :param name: Name of the logging level.
        :param id: Numeric ID of the logging level.
        :param fmt: Format string for the logging level.
        """
        CustomFormatter.add_log_level(name, id)
        CustomFormatter.FORMATS[id]  = fmt + CustomFormatter.formatStr + CustomFormatter.reset

    #-----------------------------------------------------------------
    def setupLogger( logger, fileName, isTesting=True ) -> None:
        """
        Sets up the logger with custom formatting and handlers.

        :param logger: The logger instance to set up.
        :param fileName: The name of the log file.
        :param isTesting: Boolean value to determine if the logger is in testing mode.


        This method configures the logger with custom formatting, handlers, and filters.
        It also sets the logging level and adds custom log levels.
        If isTesting is True, it shows example logging levels.

        Example usage:
            logger = logging.getLogger(__name__)
            CustomFormatter.setupLogger(logger, 'my_log_file.log', isTesting=True)
        """
        CustomFormatter.theLogger = logger
        CustomFormatter.theFilename = fileName

        CustomFormatter.add('QUERY',    55, "\x1b[1;35;40m")

        CustomFormatter.add( 'TRACE', 100, "\x1b[00;97;45m")
        CustomFormatter.add('TRACEA', 101, "\x1b[1;32;104m")
        CustomFormatter.add('TRACEB', 102, "\x1b[1;37;43m" )
        CustomFormatter.add('TRACEC', 103, "\x1b[1;37;42m" )
        CustomFormatter.add('TRACED', 104, "\x1b[1;93;100m")
        CustomFormatter.add('TRACEE', 105, "\x1b[1;34;102m")
        CustomFormatter.add('TRACEF', 106, "\x1b[00;30;102m")
        CustomFormatter.add('TRACEG', 107, "\x1b[00;33;100m")
        CustomFormatter.add('TRACEH', 108, "\x1b[00;34;46m")
        CustomFormatter.add('TRACEI', 109, "\x1b[00;33;104m" )

        CustomFormatter.add('TRACEJ', 110, "\x1b[1;34;47m" )
        CustomFormatter.add('TRACEK', 111, "\x1b[65;93;100m" )
        CustomFormatter.add('TRACEL', 112, "\x1b[00;30;105m" )
        CustomFormatter.add('TRACEM', 113, "\x1b[00;94;43m" )
        CustomFormatter.add('TRACEN', 114, "\x1b[00;93;106m" )
        CustomFormatter.add('TRACEO', 115, "\x1b[0;35;43m" )
        CustomFormatter.add('TRACEP', 116, "\x1b[00;30;106m" )
        CustomFormatter.add('TRACEQ', 117, "\x1b[1;34;43m" )
        CustomFormatter.add('TRACER', 118, "\x1b[00;90;106m" )
        CustomFormatter.add('TRACES', 119, "\x1b[1;32;45m" )

        CustomFormatter.add('TRACET',  120, "\x1b[1;95;106m")
        CustomFormatter.add('TRACEU',  121, "\x1b[1;96;100m")
        CustomFormatter.add('TRACEV',  122, "\x1b[00;30;46m")
        CustomFormatter.add('TRACEW',  123, "\x1b[00;93;46m")
        CustomFormatter.add('TRACEX',  124, "\x1b[00;34;46m")
        CustomFormatter.add('TRACEY',  125, "\x1b[1;93;104m")
        CustomFormatter.add('TRACEZ',  126, "\x1b[1;93;105m")
        CustomFormatter.add('GREY',    201, "\x1b[1;90;40m")
        CustomFormatter.add('CYAN',    202, "\x1b[1;36;40m")
        CustomFormatter.add('PURPLE',  203, "\x1b[1;35;40m")
        CustomFormatter.add('GOLD',    204, "\x1b[0;33;40m")
        CustomFormatter.add('GREEN',   205, "\x1b[1;32;40m")
        CustomFormatter.add('YELLOW',  206, "\x1b[1;93;40m")
        CustomFormatter.add('LTBLUE',  207, "\x1b[1;34;40m")
        CustomFormatter.add('BLUE',    208, "\x1b[0;34;40m")
        CustomFormatter.add('WHITE',   209, "\x1b[1;37;40m")
        CustomFormatter.add('blkonoj', 210, "\x1b[7;33;40m")
        CustomFormatter.add('blkonyk', 211, "\x1b[7;93;40m")

        CustomFormatter.add('MARK',  300, "\x1b[04;92;107m")
        CustomFormatter.add('MARK1', 301, "\x1b[04;92;107m")
        CustomFormatter.add('MARK2', 302, "\x1b[04;92;107m")
        CustomFormatter.add('MARK3', 303, "\x1b[04;92;107m")
        CustomFormatter.add('MARK4', 304, "\x1b[04;92;107m")
        CustomFormatter.add('MARK5', 305, "\x1b[04;92;107m")
        CustomFormatter.add('MARK6', 306, "\x1b[04;92;107m")
        CustomFormatter.add('MARK7', 307, "\x1b[04;92;107m")
        CustomFormatter.add('MARK8', 308, "\x1b[04;92;107m")
        CustomFormatter.add('MARK9', 309, "\x1b[04;92;107m")

        CustomFormatter.add('ToDo',  400, "\x1b[07;90;107m")
        CustomFormatter.add('ToDo1', 401, "\x1b[07;90;107m")
        CustomFormatter.add('ToDo2', 402, "\x1b[07;90;107m")
        CustomFormatter.add('ToDo3', 403, "\x1b[07;90;107m")
        CustomFormatter.add('ToDo4', 404, "\x1b[07;90;107m")
        CustomFormatter.add('ToDo5', 405, "\x1b[07;90;107m")
        CustomFormatter.add('ToDo6', 406, "\x1b[07;90;107m")
        CustomFormatter.add('ToDo7', 407, "\x1b[07;90;107m")
        CustomFormatter.add('ToDo8', 408, "\x1b[07;90;107m")
        CustomFormatter.add('ToDo9', 409, "\x1b[07;90;107m")

        CustomFormatter.add('Decorator',   500, "\x1b[00;90;103m")
        CustomFormatter.add('Decorator1',  501, "\x1b[00;32;103m")
        CustomFormatter.add('Decorator2',  502, "\x1b[00;30;103m")
        CustomFormatter.add('Decorator3',  503, "\x1b[00;34;103m")
        CustomFormatter.add('Decorator4',  504, "\x1b[00;36;103m")
        CustomFormatter.add('Decorator5',  505, "\x1b[00;95;103m")

        CustomFormatter.add('Decorator_error',  510, "\x1b[00;91;103m")

        CustomFormatter.add('rocket',         600, "\x1b[00;91;103m🚀")
        CustomFormatter.add('party',          601, "\x1b[00;91;103m🎉")
        CustomFormatter.add('cross',          602, "\x1b[00;91;103m❌")
        CustomFormatter.add('check',          603, "\x1b[00;91;103m✅")
        CustomFormatter.add('closedfolder',   604, "\x1b[00;91;103m📁")
        CustomFormatter.add('openfolder',     604, "\x1b[00;91;103m📂")
        CustomFormatter.add('tools',          605, "\x1b[00;91;103m🛠 ")
        CustomFormatter.add('explanationmark',606, "\x1b[00;91;103m❗️")
        CustomFormatter.add('warningsign',    607, "\x1b[00;91;103m⚠️")
        CustomFormatter.add('infosign',       608, "\x1b[00;91;103mℹ️")
        CustomFormatter.add('music',          609, "\x1b[00;91;103m🎵")
        CustomFormatter.add('magnifierLeft',  610, "\x1b[00;91;103m🔍")
        CustomFormatter.add('magnifierRight', 611, "\x1b[00;91;103m🔎")
        CustomFormatter.add('pipe',           612, "\x1b[00;91;103m🐛")
        CustomFormatter.add('microscope',     613, "\x1b[00;91;103m🔬")
        CustomFormatter.add('telescope',      614, "\x1b[00;91;103m🔭")

        # Create a filter handler
        exclude_filter = ExcludeLevelFilter()

        # Create Stream handler
        console_handler = logging.StreamHandler()
        console_handler.addFilter(exclude_filter)

        # file_handler = logging.FileHandler(fileName)
        file_handler = RotatingFileHandler(
            fileName, maxBytes=10_000_000, backupCount=3, encoding="utf-8"
        )

        file_handler.addFilter(exclude_filter)
        # Create formatters
        file_handler_format = logging.Formatter( CustomFormatter.formatStr, datefmt='%Y/%m/%d %I:%M:%S %p')

        # Assign formatters to handlers
        file_handler.setFormatter(file_handler_format )

        ## setup the console to show colors
        console_handler.setFormatter(CustomFormatter())

        # Add handlers to the logger
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

        #logger.setLevel(logging.DEBUG)
        logger.setLevel(1)

        # if isTesting:
        #     CustomFormatter.showExampleLoggingLevel(logger, True )



    #-----------------------------------------------------------------
    @staticmethod
    def turnOffTrace(logger):
        for handler in logger.handlers:
            for i in range(100, 199):
                for f in handler.filters:  # Access filters directly
                    if isinstance(f, ExcludeLevelFilter):
                        f.addFilterLevel(i)  # Dynamically add levels to exclude

    #-----------------------------------------------------------------
    @staticmethod
    def turnOnTrace(logger):
        for handler in logger.handlers:
            for i in range(100, 199):
                for f in handler.filters:  # Access filters directly
                    if isinstance(f, ExcludeLevelFilter):
                        f.removeFilterLevel(i)  # Dynamically add levels to include

    #-----------------------------------------------------------------
    @staticmethod
    def turnOffMarkers(logger):
        for handler in logger.handlers:
            for i in range(300, 399):
                for f in handler.filters:  # Access filters directly
                    if isinstance(f, ExcludeLevelFilter):
                        f.addFilterLevel(i)  # Dynamically add levels to exclude

    #-----------------------------------------------------------------
    @staticmethod
    def turnOnMarkers(logger):
        for handler in logger.handlers:
            for i in range(300, 399):
                for f in handler.filters:  # Access filters directly
                    if isinstance(f, ExcludeLevelFilter):
                        f.removeFilterLevel(i)  # Dynamically add levels to include
    #-----------------------------------------------------------------
    @staticmethod
    def turnOffTodo(logger):
        for handler in logger.handlers:
            for i in range(400, 499):
                for f in handler.filters:  # Access filters directly
                    if isinstance(f, ExcludeLevelFilter):
                        f.addFilterLevel(i)  # Dynamically add levels to exclude

    #-----------------------------------------------------------------
    @staticmethod
    def turnOnTodo(logger):
        for handler in logger.handlers:
            for i in range(400, 499):
                for f in handler.filters:  # Access filters directly
                    if isinstance(f, ExcludeLevelFilter):
                        f.removeFilterLevel(i)  # Dynamically add levels to include

    #-----------------------------------------------------------------
    @staticmethod
    def turnOffNonStandardLevels(logger):
        CustomFormatter.turnOffLevelRange(logger, 11, 19)
        CustomFormatter.turnOffLevelRange(logger, 21, 29)
        CustomFormatter.turnOffLevelRange(logger, 31, 39)
        CustomFormatter.turnOffLevelRange(logger, 41, 49)
        CustomFormatter.turnOffLevelRange(logger, 51, 59)
        CustomFormatter.turnOffLevelRange(logger, 60, 1000)

    #-----------------------------------------------------------------
    @staticmethod
    def turnOnAllNonStandardLevels(logger):
        for handler in logger.handlers:
            for i in range(1, 1000):
                for f in handler.filters:  # Access filters directly
                    if isinstance(f, ExcludeLevelFilter):
                        f.removeFilterLevel(i)  # Dynamically add levels to include

    #-----------------------------------------------------------------
    @staticmethod
    def turnOffLevelRange(logger, start, end):
       for handler in logger.handlers:
            for i in range(start, end):
                for f in handler.filters:  # Access filters directly
                    if isinstance(f, ExcludeLevelFilter):
                        f.addFilterLevel(i)  # Dynamically add levels to exclude

    #-----------------------------------------------------------------
    @staticmethod
    def turnOnLevelRange(logger, start, end):
        for handler in logger.handlers:
            for i in range(start, end):
                for f in handler.filters:  # Access filters directly
                    if isinstance(f, ExcludeLevelFilter):
                        f.removeFilterLevel(i)  # Dynamically add levels to include

    #-----------------------------------------------------------------
    @staticmethod
    def turnOffLevel(logger, level):
        for handler in logger.handlers:
            for f in handler.filters:  # Access filters directly
                if isinstance(f, ExcludeLevelFilter):
                    f.addFilterLevel(level)  # Dynamically add levels to exclude

    #-----------------------------------------------------------------
    @staticmethod
    def turnOnLevel(logger, level):
        for handler in logger.handlers:
            for f in handler.filters:  # Access filters directly
                if isinstance(f, ExcludeLevelFilter):
                    f.removeFilterLevel(level)  # Dynamically add levels to include

    #-----------------------------------------------------------------
    @staticmethod
    def turnOff200level(logger):
        CustomFormatter.turnOffLevelRange(logger, 200, 299)

    #-----------------------------------------------------------------
    @staticmethod
    def turnOn200level(logger):
        CustomFormatter.turnOnLevelRange(logger, 200, 299)

    #-----------------------------------------------------------------
    @staticmethod
    def turnOn300level(logger):
        CustomFormatter.turnOnLevelRange(logger, 300, 399)

    #-----------------------------------------------------------------
    @staticmethod
    def turnOn400level(logger):
        CustomFormatter.turnOnLevelRange(logger, 400, 499)

    @staticmethod
    #-----------------------------------------------------------------
    def showExampleLoggingLevel(logger, showForLoops=True) -> None:
        """
        Shows examples of different logging levels and their formatting.
        :param logger: The logger instance to use for logging.
        :param showForLoops: Boolean value to determine if for loops should be shown.


        This method demonstrates the usage of different logging levels and their formatting.
        It also shows examples of colored output using ANSI escape codes.
        If showForLoops is True, it shows examples of different combinations of attributes,
        foreground colors, and background colors.
        """

        attribs ={ '00': 'Normal', '01':'Bold', '04':'Underlined', '05':'Blinking', '07':'Reversed', '08':'Concealed'}
        foreground = {'30':'black' , '31':'red','32':'green', '33':'orange', '34':'blue', '35':'purple', '36':'cyan', '37':'grey',
            '90':'dark grey','91':'light red','92':'light green', '93':'yellow', '94':'light blue', '95':'light purple',
            '96':'turquoise', '97':'bright white'}
        background = {'40':'black' , '41':'red','42':'green', '43':'orange', '44':'blue', '45':'purple', '46':'cyan', '47':'grey',
            '100':'dark grey','101':'light red','102':'light green', '103':'yellow', '104':'light blue', '105':'light purple',
            '106':'turquoise', '107':'bright white'}

        ''' shows all the different combinations of attributes, foreground colors, and background colors '''
        if showForLoops:
            for b,bv in background.items():
                for f, fv in foreground.items():
                    for a,av in attribs.items():
                         print (f"\x1b[0m  \033[{a};{f};{b}m ...A...{fv} on {bv} background with atrrib {av}      AaBbQrStUvWxYz--xxx {a};{f};{b} \033[0m ")

        ''' shows all the different levels of logging '''

        logger.debug('This message should go to the log file level 10')
        logger.info('So should this level 20')
        logger.warning('And this, too level 30')
        ### logger.warn('And this, too just warn not warning')
        logger.error('test error level level 40')
        logger.critical('test critical error level 50')

        logger.query('test of query 55')

        logger.trace( 'test of trace 100')
        logger.tracea('test of trace 101')
        logger.traceb('test of trace 102')
        logger.tracec('test of trace 103')
        logger.traced('test of trace 104')
        logger.tracee('test of trace 105')
        logger.tracef('test of trace 106')
        logger.traceg('test of trace 107')
        logger.traceh('test of trace 108')
        logger.tracei('test of trace 109')

        logger.tracej('test of trace 110')
        logger.tracek('test of trace 111')
        logger.tracel('test of trace 112')
        logger.tracem('test of trace 113')
        logger.tracen('test of trace 114')
        logger.traceo('test of trace 115')
        logger.tracep('test of trace 116')
        logger.traceq('test of trace 117')
        logger.tracer('test of trace 118')
        logger.traces('test of trace 119')

        logger.tracet('test of trace 120')
        logger.traceu('test of trace 121')
        logger.tracev('test of trace 122')
        logger.tracew('test of trace 123')
        logger.tracex('test of trace 124')
        logger.tracey('test of trace 125')
        logger.tracez('test of trace 126')

        logger.grey('test of grey 201')
        logger.cyan('test of cyan 202')
        logger.purple('test of purple 203')
        logger.gold('test of gold 204')
        logger.green('test of green 205')
        logger.yellow('test of yellow 206')
        logger.ltblue('test of light blue 207')
        logger.blue('test of blue 208')
        logger.white('test of white 209')
        logger.blkonoj('test of black on orangec 210')
        logger.blkonyk('test of black on yellow 211')

        logger.mark ("test of mark 300")
        logger.mark1("test of mark 301")
        logger.mark2("test of mark 302")
        logger.mark3("test of mark 303")
        logger.mark4("test of mark 304")
        logger.mark5("test of mark 305")
        logger.mark6("test of mark 306")
        logger.mark7("test of mark 307")
        logger.mark8("test of mark 308")
        logger.mark9("test of mark 309")
        logger.mark()
        logger.mark1()

        logger.todo ("test of todo 400")
        logger.todo1("test of todo 401")
        logger.todo2("test of todo 402")
        logger.todo3("test of todo 403")
        logger.todo4("test of todo 404")
        logger.todo5("test of todo 405")
        logger.todo6("test of todo 406")
        logger.todo7("test of todo 407")
        logger.todo8("test of todo 408")
        logger.todo9("test of todo 409")
        logger.todo()
        logger.todo9()

        logger.decorator( "test of decorator 500")
        logger.decorator1("test of decorator 501")
        logger.decorator2("test of decorator 502")
        logger.decorator3("test of decorator 503")
        logger.decorator4("test of decorator 504")
        logger.decorator5("test of decorator 505")
        logger.decorator_error("test of decorator 510")

        logger.rocket         ("test of rocket        600")
        logger.party          ("test of party         601")
        logger.cross          ("test of cross         602")
        logger.check          ("test of check         603")
        logger.closedfolder   ("test of closedfolder  604")
        logger.openfolder     ("test of openfolder    604")
        logger.tools          ("test of tools         605")
        logger.explanationmark("test of explanationmark 606")
        logger.warningsign    ("test of warning       607")
        logger.infosign       ("test of infosign      608")
        logger.music          ("test of music         609")
        logger.magnifierLeft  ("test of magnifierLeft 610")
        logger.magnifierRight ("test of magnifierRight 611")
        logger.pipe           ("test of pipe          612")
        logger.microscope     ("test of microscope    613")
        logger.telescope      ("test of telescope     614")


#-----------------------------------------------------------------

#=================================================================
## from https://stackoverflow.com/questions/384076/how-can-i-color-python-logging-output
##-----------------------------------------------------------------
##
## also from https://stackoverflow.com/questions/4842424/list-of-ansi-color-escape-sequences
## from https://azrael.digipen.edu/~mmead/www/mg/ansicolors/index.html
##             ESC[1;37;44mBright white on blueESC[0m
##
##   Attributes	      Foreground color	Background color
##                      30 = black           40 = black
##   00 = normal        31 = red             41 = red
##   01 = bold          32 = green           42 = green
##   04 = underlined    33 = orange          43 = orange
##   05 = blinking      34 = blue            44 = blue
##   07 = reversed      35 = purple          45 = purple
##   08 = concealed     36 = cyan            46 = cyan
##                      37 = grey            47 = white (grey)
##
##                      90 = dark grey       100 = dark grey
##                      91 = light red       101 = light red
##                      92 = light green     102 = light green
##                      93 = yellow          103 = yellow
##                      94 = light blue      104 = light blue
##                      95 = light purple    105 = light purple
##                      96 = turquoise       106 = turquoise
##                      97 = bright White    107 = bright white
##
##
#-----------------------------------------------------------------





#-----------------------------------------------------------------
if __name__ == '__main__':
    """
    This is the main function that runs when the script is executed directly.
    It sets up the logger and demonstrates the usage of the CustomFormatter class.
    """
    print("You should not run this file directly, it is a module to be imported.")
    sys.exit(-99)



#-----------------------------------------------------------------
#-----------------------------------------------------------------
#-----------------------------------------------------------------
#-----------------------------------------------------------------
# Load config once at import time
# with open(os.path.join(os.path.dirname(__file__), '../../config.json'), 'r') as f:
#     config = json.load(f)


fn = MySettings.getStr("General", "log_file_path", "logs/conversion_log.txt")
logger = logging.getLogger(fn)
CustomFormatter.setupLogger(logger, fn.replace('.py', '.log'))
################CustomFormatter.showExampleLoggingLevel(logger, True)
