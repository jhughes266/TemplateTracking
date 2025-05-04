import cv2
import cv2 as cv
import matplotlib.pyplot as plt
import numpy as np
import math
from timerClass import Timer
from datetime import datetime
import time
import csv
import os
import serial
import serial.tools.list_ports
import sys
from traceback import format_exception
from colorama import Fore, Style, init

class ObjectTracking:
    #region initilization methods
    def __init__(self):
        init(autoreset=True)
        # open serial port using the first serial port available
        self._portsList = serial.tools.list_ports.comports()
        self._enableSerialFlag = False
        if len(self._portsList) != 0:
            self._selectedPort = self._portsList[0].device
            self._enableSerialFlag = True
        # init the template
        self._InitTemplate(r'templates/template.jpg')
        # init the default config dictionary
        self._InitDefaultConfig()
        # read the config file
        self._ReadConfig(r'config.txt')
        # non configurable attr init
        self._NonConfigAttrInit()
        # Exception Handling
        self._ExceptionHandling()
        # save the values from the configuration dictionary as attributes
        self._ConfigDictToAttr()
        # init display var
        self._DisplayAttrInit()
        if self._enableSerialFlag:
            self._serialCom = serial.Serial(port=self._selectedPort, baudrate=self._serialBaudRate, timeout=0)
            sys.excepthook = self._programTermination
        #init the serial commands list
        self._InitSerialCommands()

    def _programTermination(self, type, value, traceback):
        if self._enableSerialFlag:
            self._serialCom.close()
        exceptionList = format_exception(type, value, traceback)
        for entry in exceptionList:
            print(Fore.RED + entry, end='')

    def _InitTemplate(self, templateFilePath):
        template = cv.imread(templateFilePath)
        self._template = cv.cvtColor(template, cv.COLOR_BGR2GRAY).astype(np.float32)

    def _InitDefaultConfig(self):
        self._configDict = {
            "roiSize": 70,
            "tmThreshold": 0.17,
            "roiMode": 0,
            "minMovingRoiScale": 3,
            "dataLogWriteMode": 0,
            "serialBaudRate": 9600,
            "serialCOMport": "AUTO",
            "camResolutionWidth": 640,
            "camResolutionHeight": 360,
            "camID": 0,
            "dataLogSwitch": 0,
            "serialLogMode": 0
        }

    def _InitSerialCommands(self):
        #can potentially change this to a dictionary later to take advanantage of hashing
        self._serialCommandList = ['set roisize','get pos']

    def _ReadConfig(self, fileName):
        # opening the file
        configFile = open(fileName, "r")
        # reading each of the lines from the txt file
        configList = configFile.readlines()
        # creating a configuration dictionary keys will be variable names and values the variable values
        for line in configList:
            valueFlag = False
            keyFlag = True
            valueStr = ""
            keyStr = ""
            for char in line:
                if char == "-" or char == "/" or char == "[":
                    continue
                if char == "=":
                    valueFlag = True
                    keyFlag = False
                    continue

                if char == "#":
                    valueFlag = False
                    continue

                if valueFlag:
                    valueStr += char

                if keyFlag:
                    keyStr += char

            # removing spaces

            valueStr = valueStr.replace(" ", "")
            keyStr = keyStr.replace(" ", "")
            if len(keyStr) != 0 and len(valueStr) != 0:
                self._configDict[keyStr] = valueStr
        configFile.close()

    def _ExceptionHandling(self):
        errorList = ["ERRORS--------------------------------------\n"]
        warningList = ["WARNINGS----------------------------------------\n"]
        fatalErrorFlag = False

        # 1 roi Size error checking. Need to add another error checkin in here to make sure that ROI
        # size is not too small relative to the size of the template
        if float(self._configDict["roiSize"]) < 0.00 or float(self._configDict["roiSize"]) > 1.00:
            errorList.append("      The roiSize setting must be between 0 and 1\n")

        # 2 tm threshold checking
        if float(self._configDict["tmThreshold"]) < 0.00 or float(self._configDict["tmThreshold"]) > 1.00:
            errorList.append("      The tmThreshold setting must be between 0 and 1\n")

        # 3
        if int(self._configDict["roiMode"]) != 0 and int(self._configDict["roiMode"]) != 1:
            errorList.append("      The specified setting for roiMode is invalid! It must be either 0 for 'fixed-size' or 1 for 'adjustable'!\n")

        # 4 may be able to change this to a float will keep it as an int for the time being
        if float(self._configDict["minMovingRoiScale"]) < 1:
            errorList.append("      minMovingRoiScale ROI scale has to be greater than 1\n")

        # 5
        if float(self._configDict["camID"]) % 1 != 0  or float(self._configDict["camID"]) < 0 :
            errorList.append("      The camID must be 0 or a postive integer\n")

        # 6 error checking for camera id

        cap = cv.VideoCapture(int(self._configDict['camID']), cv.CAP_DSHOW)
        ret, _ = cap.read()
        # check if the entered id is notconected
        if ret != True:
            errorList.append("      The Camera ID you have entered can not be red. Please ensure that you have selected a valid device. PROGRAM TERMINATED\n")
            fatalErrorFlag = True
        cap.release()


        # 7
        if int(self._configDict["camResolutionWidth"]) < 100:
            errorList.append("      The camResolutionWidth must be greater 100 pixels\n")

        # 8
        if int(self._configDict["camResolutionHeight"]) < 100:
            errorList.append("      The camResolutionHeight must be greater 100 pixels\n")


        # 11
        if int(self._configDict["dataLogSwitch"]) != 0 and int(self._configDict["dataLogSwitch"]) != 1:
            errorList.append("      The specified setting for dataLogSwitch is invalid! It must be either 0 for no writing to the text file or 1 for writing to the text file!\n")

        # 12
        if int(self._configDict["dataLogWriteMode"]) != 0 and int(self._configDict["dataLogWriteMode"]) != 1:
            errorList.append("      The specified setting for dataLogSwitch is invalid! It must be either 0 for 'end' or 1 for 'runtime'!\n")

        # 13 checking that baud rate values are acceptable
        if int(self._configDict['serialBaudRate']) < 1 or int(self._configDict['serialBaudRate']) > 11520:
            errorList.append("      the baud rate must be between 1 and 11520 inclusive\n")
        # 14 Checking that the com port has been successfully accessed
        if len(self._portsList) == 0:
            warningList.append("      Warning: No communication port detected! Check the serial device is connected and the COM port number is correctly set in the config file\n")
        # 15 Checking the selected port is valid
        elif self._configDict['serialCOMport'].lower() != 'auto':
            #flag that will signal weather the selected com port exists
            portConnected = False
            for port in self._portsList:
                if self._configDict['serialCOMport'].lower() == port.device.lower():
                    portConnected = True
                    #The port in the config file exist therefore setting the selected port to that
                    self._selectedPort = port.device
                    break
            if portConnected == False:
                #Disabling serial comunication so that the program does not potentially write to the wrong port
                self._enableSerialFlag = False
                warningList.append("      Warning: There is serial port(s) connected. However the port entered in the config file does not exist! Please check that you have entered the correct port!\n")
                warningList.append("               The port you selected was: " + self._configDict['serialCOMport'] + "\n")
                warningList.append("               The ports currently connected are:\n")
                for port in self._portsList:
                    warningList.append("                 -" + port.device +"\n")

        # 16
        if int(self._configDict["serialLogMode"]) != 0 and int(self._configDict["serialLogMode"]) != 1 and int(self._configDict["serialLogMode"]) != 2:
            errorList.append("      The serial log mode entered is incorrect. It must be 0 for 'closed' or 1 for 'continuous' or '2' for 'on request'\n")

        # open text file for append
        outputLogFile = open("Output.txt", "a")

        if fatalErrorFlag == True:
            outputLogFile.writelines(errorList)
            print("Fatal errors have been detected program execution terminated refer to the output text file!")
            sys.exit()

        outputLogFile.write("\nExecution of object tracking program. " + datetime.now().strftime("%c") + "\n")
        if self._enableSerialFlag:
            outputLogFile.write("      Writing results to " + self._selectedPort + "\n")

        if len(warningList) != 1:
            outputLogFile.writelines(warningList)
            print("Warnings have arisen continuing with program execution refer to the output text file!")


        if len(errorList) != 1:
            outputLogFile.writelines(errorList)
            print("Errors have been detected revering to default config refer to the output text file!")
            self._InitDefaultConfig()

        outputLogFile.close()
        #display warnings and errors in the console
        for line in errorList:
            print(line,end='')

        for line in warningList:
            print(line,end='')

    def _ConfigDictToAttr(self):

        # This is the maximum allowable difference for a match. Essentially it means any matches above this
        # threshold will not be considered a match. This gives a clear indication of when the template is no
        # longer present. This value may require quite a bit of trial and error depending on the background before
        # it is set in stone.
        self._tmThreshold = float(self._configDict['tmThreshold'])
        # sets the mode for roi of interest two modes available "fixed_size" and "adjustable"
        if int(self._configDict['roiMode']) == 0:
            self._roiMode = "fixed-size"
        elif int(self._configDict['roiMode']) == 1:
            self._roiMode = "adjustable"


        # when the template is deemed as stationary the ROI of interest will be a multiple of template size. Likewise with
        # minMovingROI scale a certain multiple of the template size is specfied this is necessary because without it the
        # ROI could get thiner then the template causeing the program to break.
        # MAY NEED TO SPECIFY SOME BOUNDARY CONDITIONS ON THSESE
        self._minMovingRoiScale = float(self._configDict['minMovingRoiScale'])
        self._camResolutionWidth = int(self._configDict['camResolutionWidth'])
        self._camResolutionHeight = int(self._configDict['camResolutionHeight'])
        self._dataLogWriteMode = int(self._configDict['dataLogWriteMode'])
        self._serialBaudRate = int(self._configDict['serialBaudRate'])
        self._camID = int(self._configDict['camID'])

        # converting the roi size to radius as within the context of the program it makes more sense. That is why
        # there is the division by 2
        roiSize = float(self._configDict['roiSize'])
        roiSize *= self._camResolutionWidth
        self._roiRadius = int(roiSize / 2)
        self._dataLogSwitch = int(self._configDict['dataLogSwitch'])
        self._serialLogMode = int(self._configDict['serialLogMode'])
        self._enableSerialFlag = bool(int(self._configDict['serialLogMode']))
        #the warning has alreay been detected in this part if the setting is enabled we need
        # to revert to false if no ports have been detected(There is probably a better way
        # to implement this then just putting in this if statement )
        if len(self._portsList) == 0:
            self._enableSerialFlag = False

        self._waitForSerialRequest = False
        if int(self._configDict['serialLogMode']) == 2:
            self._waitForSerialRequest = True

        #ASSIGN SELECTED PORT

    def _NonConfigAttrInit(self):
        self._yHatPrev = None
        self._xHatPrev = None
        self._tmThresholdDisp = 0
        # This is the maximum value for which the template will be considered stationary. It corresponds to the euclidean
        # distance between the past and the current match
        self._maxStationaryVal = 2
        self._detectionsLocationsList = []
        self._movementDirectionVector = np.zeros(2)
        # checking if directory exists and if not creating it
        if os.path.exists('trackingLocations') != True:
            os.mkdir('./trackingLocations')
        self._currentTime = datetime.now()
        self._fileName = self._currentTime.strftime(r"trackingLocations/%Y-%m-%d-%H-%M-%S.txt")
        #if the runtime dataLogWriteMode option is selected opening the txt file
        if int(self._configDict['dataLogWriteMode']) == 1 and int(self._configDict['dataLogSwitch']) == 1:
            self._txtFile = open(self._fileName, 'w')
        #time flag for writing to the text file
        self._timerFlag = False
        #editing the serial port dictionary value before checking. it is in interger format at the minute but needs to have COM before it
        #first checking if it is 0 and setting it to auto
        if int(self._configDict['serialCOMport']) == 0:
            self._configDict['serialCOMport'] = "AUTO"
        #Now we perform the editing adding COM to the front of the number
        else:
            self._configDict['serialCOMport'] = 'COM' + self._configDict['serialCOMport']
            self._configDict['serialCOMport'] =  self._configDict['serialCOMport'].strip('\n')
        self._previousSerialReadString = ""

    def _DisplayAttrInit(self):
        # storing display vars can be moved if is too slow
        # text
        self._font = cv.FONT_HERSHEY_SIMPLEX
        self._fontScale = .7
        self._fontColor = (0, 0, 255)
        self._boxColor = (0, 0, 255)
        boxThickness = 2
        # dot
        self._dotRadius = 3
        self._dotColor = (0, 0, 255)
        # text display
        self._positionPos = (0, 20)
        self._threshPos = (0, 40)
    #endregion

    #region overall tracking function method
    def Track(self):
        #set up the capture object
        cap = cv.VideoCapture(self._camID, cv.CAP_DSHOW)
        #set the width and
        width = self._camResolutionWidth
        height = self._camResolutionHeight
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        # Check if the webcam is opened correctly
        if not cap.isOpened():
            raise Exception("Could not open video device")
        #flag to tell if calibrating or not if not calibrating then RoiTracking is occuring
        calibrating = True
        totalTimer = Timer("Total Time")
        trackingTimer = Timer("Tracking Time")

        calibratingFlagForTimer = True
        #video loop for tracking
        while True:
            totalTimer.StartTimer()
            ret, frame = cap.read()
            frame = frame.astype(np.float32)
            if not ret:
                raise Exception("Could not read frame correctly")

            # storing a frame for display purposes needs to be divided by 255 as display functions work on a proportions
            self._dispFrame = frame.copy() / 255
            #changing the frame that is to be used in the tracking to black and white
            frame = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
            # calibration (comes after ROI tracking so that after calibration
            # the program does not do an uncessary tracking phase)
            if calibrating == True:
                calibrating = self._Calibrate(frame)



            #ROI tracking
            if calibrating == False:
                trackingTimer.StartTimer()
                calibrating, roiInfo = self._RoiTracking(frame)
                trackingTimer.EndTimer()


            #display of frame and information and recording of
            self._AppendDetectionLocationsListAndSerialCom()
            if calibrating == False:
                self._DisplayRoiTracking(self._dispFrame, roiInfo)
            else:
                self._DisplayCalibrating(self._dispFrame)
            totalTimer.EndTimer()


            # Exit the program if 'q' key is pressed
            if cv.waitKey(1) == ord('q'):
                break


        #writing data to CSV file
        self._ExportDetectionLocationsToCSVAndCloseSerial()
        #final clearing up
        cap.release()
        cv.destroyAllWindows()
        #display all timer results
        totalTimer.DisplayTimerResults()
        trackingTimer.DisplayTimerResults()
    #endregion
    #region calibration methods
    def _Calibrate(self, frame):
        #zero movement direction vector so that the roi becomes stationary and allows for a proper scan
        self._movementDirectionVector = np.zeros(2)
        metricMatrix = cv.matchTemplate(frame, self._template, cv.TM_SQDIFF)
        # normalizing the metric matrix(same process and reasoning as in the calibration section)
        metricMatrix = metricMatrix / (np.size(self._template) * 255 * 255)
        self._tmThresholdDisp = np.min(metricMatrix)
        if np.min(metricMatrix) > self._tmThreshold:
            self._yHatPrev = -1
            self._xHatPrev = -1
            return True

        # mapping the mimimum location back to the original dimensions
        _, _, minLoc, _ = cv.minMaxLoc(metricMatrix)
        minLoc = self._Map(minLoc[1], minLoc[0])

        self._yHatPrev = minLoc[0]
        self._xHatPrev = minLoc[1]
        return False
    #endregion

    #region tracking within the ROI methods
    def _RoiTracking(self, frame):
        if self._roiMode == "fixed-size":
            # setting the top positions here is necessary for tracking when it is being displayed it will appear as
            # if the ROI is lagging this is not the case this is just caused by it using the previous yhat and xhat
            # locations this could be rectified if neccessary but it is not.
            yTopLeft = self._yHatPrev - self._roiRadius
            xTopLeft = self._xHatPrev - self._roiRadius
            # can potentially take bellow out of for loop if speed increase is neccessary
            # kept in side for the sake of simplicity
            width = 2 * self._roiRadius
            height = 2 * self._roiRadius
        else:
            # this generates the  region of interest coordinates given the movement Direction vector. And the previous match location.
            yTopLeft, xTopLeft, width, height = self._GenerateRoiCords()


        # handling situations where the region of interest leaves the dimensions
        # of the frame
        if yTopLeft < 0:
            yTopLeft = 0

        if xTopLeft < 0:
            xTopLeft = 0

        if yTopLeft + height >= frame.shape[0]:
            yTopLeft = frame.shape[0] - height

        if xTopLeft + width >= frame.shape[1]:
            xTopLeft = frame.shape[1] - width

        # taking the ROI out of the input frame
        roiFrame = frame[int(yTopLeft): int(yTopLeft + height), int(xTopLeft): int(xTopLeft + width)]
        # template matching the roi Frame with the template
        metricMatrix = cv.matchTemplate(roiFrame, self._template, cv.TM_SQDIFF)
        # normalizing the metric matrix(same process and reasoning as in the calibration section)
        metricMatrix = metricMatrix / (np.size(self._template) * 255 * 255)
        self._tmThresholdDisp = np.min(metricMatrix)
        if np.min(metricMatrix) > self._tmThreshold:
            self._yHatPrev = -1
            self._xHatPrev = -1
            return True, None
        # mapping the mimimum location back to the original dimensions
        _, _, minLoc, _ = cv.minMaxLoc(metricMatrix)
        minLoc = self._Map(minLoc[1], minLoc[0])
        # the locations are within the ROI NOT THE IMAGE
        roiY = minLoc[0]
        roiX = minLoc[1]
        # only the match location withing the ROI now need to convert it back to the location within
        # the frame so it needs to be added to the top left cordinates

        # storing the previous location for vector calculations
        yHatInitial = np.copy(self._yHatPrev)
        xHatInitial = np.copy(self._xHatPrev)

        self._yHatPrev = yTopLeft + roiY
        self._xHatPrev = xTopLeft + roiX


        y = self._yHatPrev
        x = self._xHatPrev

        if self._roiMode == "adjustable":
            self._movementDirectionVector = self._GenerateVector(yHatInitial, xHatInitial, y, x)

        roiInfo = [int(y), int(x), int(yTopLeft), int(xTopLeft), int(height), int(width)]

        return False, roiInfo

    def _GenerateRoiCords(self):

        if (np.linalg.norm(self._movementDirectionVector)) < self._maxStationaryVal:
            yRadius = int(self._minMovingRoiScale * self._template.shape[0])
            xRadius = int(self._minMovingRoiScale * self._template.shape[1])
            yTopLeft = self._yHatPrev - yRadius
            xTopLeft = self._xHatPrev - xRadius
            # Has to be the roiRadius size for calibration
            height = 2 * yRadius
            width = 2 * xRadius
            #print(height)
            #print(width)
            return int(yTopLeft), int(xTopLeft), int(width), int(height)

        # scaling the input vector so that its magnitude equals the vaue of the ROI radius
        scaledVector = np.zeros_like(self._movementDirectionVector)
        scaleFactor = self._roiRadius / np.linalg.norm(self._movementDirectionVector)
        scaledVector[0] = self._movementDirectionVector[0] * scaleFactor
        scaledVector[1] = self._movementDirectionVector[1] * scaleFactor

        # height and width calculations
        height = abs(scaledVector[0]) + self._minMovingRoiScale * self._template.shape[0]
        width = abs(scaledVector[1]) + self._minMovingRoiScale * self._template.shape[1]
        # Bellow the code sets up the ROI based on the scaled vector.
        # In each case padding out the roi to ensure that the template
        # inside it
        # y pos, x pos
        if scaledVector[0] >= 0 and scaledVector[1] >= 0:
            yTopLeft = self._yHatPrev - self._minMovingRoiScale / 2 * self._template.shape[0]
            xTopLeft = self._xHatPrev - self._minMovingRoiScale / 2 * self._template.shape[1]
        # y neg, x pos
        elif scaledVector[0] <= 0 and scaledVector[1] >= 0:
            yTopLeft = self._yHatPrev - self._minMovingRoiScale / 2 * self._template.shape[0] + scaledVector[0]
            xTopLeft = self._xHatPrev - self._minMovingRoiScale / 2 * self._template.shape[1]
        # y pos, x neg
        elif scaledVector[0] >= 0 and scaledVector[1] <= 0:
            yTopLeft = self._yHatPrev - self._minMovingRoiScale / 2 * self._template.shape[0]
            xTopLeft = self._xHatPrev - self._minMovingRoiScale / 2 * self._template.shape[1] + scaledVector[1]
        # y neg, x neg
        elif scaledVector[0] <= 0 and scaledVector[1] <= 0:
            yTopLeft = self._yHatPrev - self._minMovingRoiScale / 2 * self._template.shape[0] + scaledVector[0]
            xTopLeft = self._xHatPrev - self._minMovingRoiScale / 2 * self._template.shape[1] + scaledVector[1]

        return int(yTopLeft), int(xTopLeft), int(width), int(height)

    def _Map(self, yMetric, xMetric):
        yFrame = yMetric + self._IfEven(self._template.shape[0])
        xFrame = xMetric + self._IfEven(self._template.shape[1])
        return int(yFrame), int(xFrame)

    @staticmethod
    def _IfEven(dim):
        result = np.floor(dim / 2)
        if dim % 2 == 0:
            result -= 1
        return result

    @staticmethod
    def _GenerateVector(yInit, xInit, yFin, xFin):
        vector = np.zeros(2)
        vector[0] = yFin - yInit
        vector[1] = xFin - xInit
        return vector

    #endregion

    #region export of locations to a CSV file methods
    def _AppendDetectionLocationsListAndSerialCom(self):
        if self._timerFlag == False:
            self._programStartTime = time.perf_counter()
            self._timerFlag = True

        timeSinceProgramLaunch = round(time.perf_counter() - self._programStartTime, 4 )
        entry = ["{:.4f},".format(timeSinceProgramLaunch), str(self._xHatPrev) + ",", str(self._yHatPrev)]
        # send to the serial port if it is in use
        if self._enableSerialFlag == True and self._waitForSerialRequest == False:
            self._serialCom.write(("{:.4f},".format(timeSinceProgramLaunch) + str(self._xHatPrev) + "," + str(self._yHatPrev) + "\n\r").encode('utf-8'))
        elif self._enableSerialFlag == True and self._waitForSerialRequest == True:
            self._serialCommandHandler(timeSinceProgramLaunch)
        #anything bellow this if statement is associated with the data log entry if data logging in the file is turned off then we exit the function at this point
        if int(self._configDict['dataLogSwitch']) == 0:
            return

        # if the mode is run time then we write directly to the txt file
        if int(self._configDict['dataLogWriteMode']) == 1:
            self._txtFile.writelines(entry)
            self._txtFile.write("\n")
        else:
            self._detectionsLocationsList.append(entry)

    #Method for handling serial commands
    def _serialCommandHandler(self, timeSinceProgramLaunch):
        # read the port if it has the message "getPos" then write the pos to the serial port
        recievedData = self._serialCom.read_all().decode('utf-8').strip()
        # we need to keep track of previously red serial strings because sometimes during reading the string can get split
        # if the recieved data is empty it means that there was no "overflow from the previous command" therefore we reset the storage of the previous command
        if recievedData == "":
            self._previousSerialReadString = ""

        # the previously red command had data in it so we add the recieved dat to the previously red string
        if self._previousSerialReadString != "":
            recievedData = self._previousSerialReadString + recievedData

        if "get pos" in recievedData:
            self._serialCom.write(("{:.4f},".format(timeSinceProgramLaunch) + str(self._xHatPrev) + "," + str(self._yHatPrev) + "\n\r").encode('utf-8'))
        elif "set roisize" in recievedData:
            command = "set roisize"
            try:
                roiSize = float(recievedData.replace(command, ""))
            except ValueError:
                self._serialCom.write(("ERROR: Invalid 'roisize' must be a float between 0 and 1 exculsive" + "\n\r").encode('utf-8'))
            else:
                # calculates the max fixed size when the tracking mode is fixed size
                maxFixedSizeRoi = min(self._camResolutionWidth, self._camResolutionHeight) / self._camResolutionWidth

                # calculates the max fixed size when the tracking mode is adjustable
                # this takes the addition of the padding with the min moving roi scale into account
                leftOverWidth = min(self._camResolutionWidth, self._camResolutionHeight) - max(self._template.shape)
                # is the left over width after the subtracting of the padding divided by the min dimension of the screen
                maxAdjustableSizeRoi = leftOverWidth / min(self._camResolutionWidth, self._camResolutionHeight)
                if self._roiMode == "fixed-size" and (roiSize <= 0.0 or roiSize >= maxFixedSizeRoi):
                    self._serialCom.write(("ERROR: Invalid 'roisize' for FIXED-SIZE must be a float between 0 and " + str(maxFixedSizeRoi) + " exculsive " + "\n\r").encode('utf-8'))
                elif self._roiMode == "adjustable" and (roiSize <= 0.0 or roiSize >= maxAdjustableSizeRoi):
                    self._serialCom.write(("ERROR: Invalid 'roisize' for ADJUSTABLE must be a float between 0 and " + str(maxAdjustableSizeRoi) + " exculsive " + "\n\r").encode('utf-8'))
                else:
                    roiSize *= self._camResolutionWidth
                    self._roiRadius = int(roiSize / 2)
                    self._serialCom.write(("Done" + "\n\r").encode('utf-8'))

        else:
            # the data red this cycle is not a valid command but it could be part of one red next cycle so it gets added to the previously red string
            if recievedData != '':
                self._previousSerialReadString = recievedData
                self._serialCom.write(("Invalid command or port is waiting for the rest of command. Command was: '"+ recievedData + "'\n\r").encode('utf-8'))

    def _ExportDetectionLocationsToCSVAndCloseSerial(self):
        if self._enableSerialFlag:
            self._serialCom.close()
        #anything bellow this if statement is associated with the data log entry if data logging in the file is turned off then we exit the function at this point
        if int(self._configDict['dataLogSwitch']) == 0:
            return

        if int(self._configDict['dataLogWriteMode']) == 0:
            self._txtFile =  open(self._fileName, 'w')
            for entry in self._detectionsLocationsList:
                self._txtFile.writelines(entry)
                self._txtFile.write("\n")
        self._txtFile.close()

    #endregion

    #region display methods
    def _DisplayRoiTracking(self, dispFrame, roiInfo):
        # extracting data from ROI info
        y = roiInfo[0]
        x = roiInfo[1]
        roiYTopLeft = roiInfo[2]
        roiXTopLeft = roiInfo[3]
        roiHeight = roiInfo[4]
        roiWidth = roiInfo[5]

        #putting the position into a tuple
        position = (self._xHatPrev, self._yHatPrev)

        #ROI placement
        topLeft = (roiXTopLeft, roiYTopLeft)
        bottomRight = (roiXTopLeft + roiWidth, roiYTopLeft + roiHeight)
        cv.rectangle(dispFrame, topLeft, bottomRight, self._boxColor)
        #predicition dot placement
        cv.circle(dispFrame, position, self._dotRadius, self._dotColor, thickness=cv.FILLED)
        #text placement
        posText1 = "Postion x: " + str(position[0]) + " y: " + str(position[1])
        posText2 = "Template Matching Threshold: " + str(round(self._tmThresholdDisp, 5))
        cv.putText(dispFrame, posText1, self._positionPos, self._font, self._fontScale, self._fontColor)
        cv.putText(dispFrame, posText2, self._threshPos, self._font, self._fontScale, self._fontColor)
        #show the image
        cv.imshow('Webcam Live', dispFrame)

    def _DisplayCalibrating(self, dispFrame):
        #dispFrame = cv2.cvtColor(dispFrame, cv2.COLOR_GRAY2BGR)
        position = (self._xHatPrev, self._yHatPrev)
        #####TESTING REMOVE WHEN FINISHED#################################
        cv.circle(dispFrame, position, self._dotRadius, self._dotColor, thickness=cv.FILLED)
        #####TESTING REMOVE WHEN FINISHED#################################
        posText = "Postion x: " + str(position[0]) + " y: " + str(position[1])
        posText2 = "Max Difference Threshold: " + str(round(self._tmThresholdDisp, 5))
        cv.putText(dispFrame, posText, self._positionPos, self._font, self._fontScale, self._fontColor)
        cv.putText(dispFrame, posText2, self._threshPos, self._font, self._fontScale, self._fontColor)
        cv.imshow('Webcam Live', dispFrame)
    #endregion



