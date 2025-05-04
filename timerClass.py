import time
import copy
import statistics
import matplotlib.pyplot as plt


class Timer:
    def __init__(self, name):
        # name
        self._name = name
        # start time end time
        self._startTime = 0
        self._endTime = 0
        # time differences
        self._difference = 0
        self._minDifference = float("inf")
        self._maxDifference = 0
        self._differenceSum = 0
        self._averageDifference = 0
        self._differenceList = []
        # refresh rate
        self._refreshRate = 0
        self._minRefreshRate = float("inf")
        self._maxRefreshRate = 0
        self._refreshRateSum = 0
        self._averageRefreshRate = 0
        self._refreshRateList = []
        # sample number
        self._sampleNumber = 0

    # Getters
    def GetRefreshRate(self):
        return self._refreshRate

    def GetSampleNumber(self):
        return self._sampleNumber

    def StartTimer(self):
        self._startTime = time.perf_counter_ns() / 1e9

    def EndTimer(self):
        self._endTime = time.perf_counter_ns() / 1e9


        if self._startTime != self._endTime:
            # difference
            self._difference = self._endTime - self._startTime
            self._differenceList.append(copy.deepcopy(self._difference))

            # refresh rate
            self._refreshRate = 1 / self._difference
            self._refreshRateList.append(copy.deepcopy(self._refreshRate))
            self._sampleNumber += 1

    def DisplayTimerResults(self):
        #deleting the first entrys from each list as they are always misrepresentitvly slow.(Probably has to do with the program starting up)
        if len(self._differenceList) > 1 and len(self._refreshRateList) > 1:
            del (self._differenceList[0])
            del (self._refreshRateList[0])
            decPlaces = 5
            print("_________________________________________")
            print("_________________________________________")
            print("_________________________________________")
            print("TIMER NAME: " + str(self._name))
            print("NUMBER OF SAMPLES: " + str(self._sampleNumber))
            print("TIME DIFFERENCE BETWEEN START AND END STATISTICS")
            print("average time difference:" + str(round(statistics.mean(self._differenceList), decPlaces)) + " secs")
            print("time differences std:" + str(round(statistics.stdev(self._differenceList), decPlaces)) + " secs")
            print("minimum time difference:" + str(round(min(self._differenceList), decPlaces)) + " secs")
            print("maximum time difference:" + str(round(max(self._differenceList), decPlaces)) + " secs")
            print("REFRESH RATE STATISTICS")
            print("average refresh rate:" + str(round(statistics.mean(self._refreshRateList), decPlaces)) + " hz")
            print("refresh rates std:" + str(round(statistics.stdev(self._refreshRateList), decPlaces)) + " hz")
            print("minimum refresh rate:" + str(round(min(self._refreshRateList), decPlaces)) + " hz")
            print("maximum refresh rate:" + str(round(max(self._refreshRateList), decPlaces)) + " hz")
            # histograms of the refresh rate and exection times
            hist1 = plt.figure()
            plt.hist(self._differenceList, bins=100, edgecolor='black')
            plt.title(self._name + " Differences Histogram   n=" + str(self._sampleNumber))
            plt.xlabel("Execution Time (Seconds)")
            plt.ylabel("Frequency")
            hist2 = plt.figure()
            plt.hist(self._refreshRateList, bins=100, edgecolor='black')
            plt.title(self._name + " Refresh Rates Histogram   n=" + str(self._sampleNumber))
            plt.xlabel("Refresh Rate (Hz)")
            plt.ylabel("Frequency")
            plt.show()
            print("_________________________________________")
            print("_________________________________________")
            print("_________________________________________")
        else:
            print("_________________________________________")
            print("_________________________________________")
            print("_________________________________________")
            print("THERE IS NO DATA RECORDED FOR THE " + self._name + " TIMER")
            print("_________________________________________")
            print("_________________________________________")
            print("_________________________________________")