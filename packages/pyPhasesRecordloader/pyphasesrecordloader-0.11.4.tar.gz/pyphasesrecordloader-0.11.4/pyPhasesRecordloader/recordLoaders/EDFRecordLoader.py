from datetime import datetime

import pyedflib

from ..RecordLoader import ChannelsNotPresent, ParseError, RecordLoader
from ..RecordSignal import RecordSignal
from ..Signal import Signal


class EDFRecordLoader(RecordLoader):
    def __init__(self, filePath=".", targetSignals=None, targetSignalTypes=None, optionalSignals=None, combineChannels=None) -> None:
        super().__init__(
            filePath=filePath,
            targetSignals=targetSignals,
            targetSignalTypes=targetSignalTypes,
            optionalSignals=optionalSignals,
            combineChannels=combineChannels,
        )
        self.annotations = []
        self.channelMap = {}
        self.annotationSignal = None

    def getSignal(self, recordName):
        edfFile = self.getFilePathSignal(recordName)
        signal = self.loadSignal(edfFile)
        signal.recordId = recordName
        return signal
    
    def getSignalHeaders(self, recordName):
        edfFile = self.getFilePathSignal(recordName)
        return self.loadSignalHeaders(edfFile)

    def getAnnotationTimeByName(self, name, lastFirst=False):
        return self.getAnnotationTimeByNames([name],lastFirst=False)
    
    def getFirstAnnotationTimeByName(self, name):
        return self.getAnnotationTimeByName(name,lastFirst=False)

    def getLastAnnotationTimeByName(self, name):
        return self.getAnnotationTimeByName(name,lastFirst=False)
    
    def getAnnotationTimeByNames(self, names, lastFirst=False):
        if len(self.annotations) == 0:
            return None
        
        annotationList = zip(self.annotations[0], self.annotations[2])

        if lastFirst:
            annotationList = reversed(list(annotationList))

        for time, n in annotationList:
            if n in names:
                return time

        return None

    def loadSignal(self, edfFile, annotations=False):
        recordSignal = RecordSignal()
        headers, f = self.loadSignalHeadersAndHandle(edfFile)
        
        try:
            if f.annotations_in_file > 0:
                self.annotations = f.readAnnotations()
            
            for header in headers:
                signalName = header["signalName"]
                typeStr = header["type"]
                index = header["index"]
                
                signalArray = f.readSignal(index, digital=self.useDigitalSignals)
                frequency = header["sample_frequency"] if "sample_frequency" in header else header["sample_rate"]
                signal = Signal(signalName, signalArray, frequency=frequency)
                signal.typeStr = typeStr
                signal.setSignalTypeFromTypeStr()
                signal.isDigital = self.useDigitalSignals
                signal.digitalMin = header["digital_min"]
                signal.digitalMax = header["digital_max"]
                signal.physicalMin = header["physical_min"]
                signal.physicalMax = header["physical_max"]
                signal.dimension = header["dimension"]
                signal.sourceIndex = index
                signal.prefilter = header["prefilter"]
                recordSignal.addSignal(signal, signalName)
        finally:
            f.close()
        return recordSignal
    
    def loadSignalHeaders(self, edfFile, annotations=False):
        return self.loadSignalHeadersAndHandle(edfFile, annotations)[0]
    
    def loadSignalHeadersAndHandle(self, edfFile, annotations=False, checkTargetChannels=True):
        signalHeaders, f = self.loadEdf(edfFile, self.targetSignals)

        try:
            targetSignals = self.targetSignals if annotations is False else self.annotationSignal
            if checkTargetChannels and (targetSignals is None or len(targetSignals) == 0):
                raise Exception(
                    "The RecordLoader has no target signals to extract, please specificy 'sourceSignals' with the name of the channels"
                )
                
            expectedSignals = len(targetSignals) if targetSignals is not None else 0
            addedSignals = []
            ignoredChannels = []
            targetSignalHeaders = []

            for header in signalHeaders:
                channelLabel = header["label"]
                signalName = self.chanelNameAliasMap[channelLabel] if channelLabel in self.chanelNameAliasMap else channelLabel
                if header["signalName"] in targetSignals:
                    targetSignalHeaders.append(header)
                    addedSignals.append(signalName)
                else:
                    ignoredChannels.append(signalName)

            self.logDebug("Added %i signals, ignored: %s" % (len(addedSignals), ignoredChannels))
            if len(addedSignals) < expectedSignals:
                missingchannels = set(self.targetSignals) - set(addedSignals) - set(self.optionalSignals)
                if len(missingchannels) > 0:
                    raise ChannelsNotPresent(missingchannels, edfFile)

        except Exception:
            # Close file handle if an exception occurs during processing
            if f is not None:
                f.close()
            raise

        return targetSignalHeaders, f

    def loadEdf(self, edfFile, tailorChannels=None):
        f = None
        try:
            f = pyedflib.EdfReader(edfFile)
            self.logDebug("Read EDF Header %s" % edfFile)
            n = f.signals_in_file
            
            if f.annotations_in_file > 0:
                self.annotations = f.readAnnotations()
                
            signalHeaders = []
            self.startTime = f.getStartdatetime()
            for i in range(n):
                header = f.getSignalHeader(i)
                channelLabel = header["label"]
                signalName = self.chanelNameAliasMap[channelLabel] if channelLabel in self.chanelNameAliasMap else channelLabel

                if tailorChannels is None or signalName in tailorChannels:
                    header["signalName"] = signalName
                    header["type"] = self.getSignalTypeStrFromDict(signalName)
                    header["index"] = i
                    self.channelMap[signalName] = i
                    signalHeaders.append(header)

        except Exception as ex:
            if f is not None:
                f.close()
            raise ParseError("Failed to read EDF File %s: %s" % (edfFile, str(ex)))

        return signalHeaders, f
    
    def getMetaDataFromFile(self, edfFile):
        signalHeaders, f = self.loadEdf(edfFile)
        
        try:    
            metaData = {
                "patientCode": f.getPatientCode(),
                "patientName": f.getPatientName(),
                "birthdate": f.getBirthdate(),
                "sex": f.getSex(),
                "patientAdd": f.getPatientAdditional(),
                "start": f.getStartdatetime(),
                "technician": f.getTechnician(),
                "dataCount": f.datarecords_in_file,
            }

            metaData["channels"] = signalHeaders
        finally:
            f.close()

        return metaData

    def getMetaData(self, recordId) -> dict:
        edfFile = self.getFilePathSignal(recordId)
        
        metadata = self.getMetaDataFromFile(edfFile)
        metadata["recordId"] = recordId
        return metadata

    # If we only want the starttime this method is much faster than loading all metadata
    def get_edf_start_time_manual(self, edf_path):
        with open(edf_path, "rb") as f:
            # Seek directly to date field
            f.seek(168)
            date_str = f.read(8).decode("ascii").strip()

            time_str = f.read(8).decode("ascii").strip()

        # EDF date format: dd.mm.yy
        day, month, year = date_str.split(".")
        hour, minute, second = time_str.split(".")

        # EDF uses 2-digit years
        year = int(year)
        year += 1900 if year >= 85 else 2000

        return datetime(
            year=int(year),
            month=int(month),
            day=int(day),
            hour=int(hour),
            minute=int(minute),
            second=int(second),
        )
    
    # If we only want the datacount this method is much faster than loading all metadata
    def get_edf_data_count_manual(self, edf_path):
        with open(edf_path, "rb") as f:
            # Seek directly to data record count field
            f.seek(236)
            data_count_str = f.read(8).decode("ascii").strip()

        return int(data_count_str) if data_count_str.isdigit() else 0