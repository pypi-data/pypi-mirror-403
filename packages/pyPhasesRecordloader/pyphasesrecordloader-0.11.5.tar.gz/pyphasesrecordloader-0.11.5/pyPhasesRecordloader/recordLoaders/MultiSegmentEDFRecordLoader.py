import pyedflib
import numpy as np
from pathlib import Path
import glob

from .EDFRecordLoader import EDFRecordLoader
from ..RecordSignal import RecordSignal
from ..RecordLoader import ParseError


class MultiSegmentEDFRecordLoader(EDFRecordLoader):
    """
    A specialized EDF record loader that handles multi-segment EDF files
    by automatically detecting and concatenating segments into a single
    continuous signal. Maintains compatibility with the standard EDFRecordLoader
    interface while handling segmented files transparently.
    """
    
    def __init__(self, filePath=".", targetSignals=None, targetSignalTypes=None, 
                 optionalSignals=None, combineChannels=None, 
                 segment_pattern="_seg-*", task_variations=None) -> None:
        super().__init__(
            filePath=filePath,
            targetSignals=targetSignals,
            targetSignalTypes=targetSignalTypes,
            optionalSignals=optionalSignals,
            combineChannels=combineChannels,
        )
        self.segment_pattern = segment_pattern
        self.task_variations = task_variations or ['_task-PSG', '_task-psg']
        
    def _findSegmentedFiles(self, base_path):
        """Find all segmented EDF files for a given base path"""
        segmented_files = []
        
        for task_var in self.task_variations:
            pattern = f"{base_path}{self.segment_pattern}{task_var}_eeg.edf"
            matches = sorted(glob.glob(pattern))
            if matches:
                segmented_files = matches
                break
                
        return segmented_files if segmented_files else None
    
    def _isSegmentedFile(self, file_path):
        """Check if a file path represents a segmented recording"""
        if isinstance(file_path, str):
            base_path = file_path.replace('_eeg.edf', '').split('_task-')[0]
            segmented_files = self._findSegmentedFiles(base_path)
            return segmented_files is not None and len(segmented_files) > 1
        return False
    
    def getFilePathSignal(self, recordName):
        """Override to detect and return segmented files if present"""
        # First try the parent implementation
        single_file = super().getFilePathSignal(recordName)
        
        if single_file and Path(single_file).exists():
            # Check if this is actually part of a segmented recording
            if self._isSegmentedFile(single_file):
                base_path = single_file.replace('_eeg.edf', '').split('_task-')[0]
                segmented_files = self._findSegmentedFiles(base_path)
                return segmented_files if segmented_files else single_file
            return single_file
            
        # If single file doesn't exist, look for segmented files
        # Assume recordName is the base name for segmented files
        base_path = recordName if recordName.endswith('/') else f"{recordName}"
        segmented_files = self._findSegmentedFiles(base_path)
        
        return segmented_files if segmented_files else recordName
        
    def loadSignal(self, edfFile, annotations=False):
        """Override to handle both single files and segmented files"""
        if isinstance(edfFile, list):
            # Handle segmented files
            return self._loadSegmentedSignal(edfFile, annotations)
        else:
            # Handle single file - use parent implementation
            return super().loadSignal(edfFile, annotations)
    
    def _loadSegmentedSignal(self, segment_files, annotations=False):
        """Load and concatenate signals from multiple EDF segments"""
        if not segment_files:
            return None
            
        combined_signal = RecordSignal()
        segment_start_times = []
        current_time = 0.0
        total_datarecords = 0
        
        # Track segment information
        segment_info = []
        
        for i, segment_file in enumerate(segment_files):
            self.logDebug(f"Loading segment {i+1}/{len(segment_files)}: {Path(segment_file).name}")
            
            # Load this segment using parent's loadSignal method
            segment_signal = super().loadSignal(segment_file, annotations)
            segment_start_times.append(current_time)
            
            # Get segment metadata for dataCount calculation
            try:
                with pyedflib.EdfReader(segment_file) as f:
                    segment_datarecords = f.datarecords_in_file
                    segment_duration = segment_datarecords * f.getFileDuration() / f.datarecords_in_file if f.datarecords_in_file > 0 else 0
                    
                    segment_info.append({
                        'file': segment_file,
                        'start_time': current_time,
                        'duration': segment_duration,
                        'datarecords': segment_datarecords,
                        'start_stamp': total_datarecords
                    })
                    total_datarecords += segment_datarecords
                    current_time += segment_duration
                    
            except Exception as e:
                self.logWarning(f"Could not read segment metadata from {segment_file}: {e}")
            
            if i == 0:
                # First segment - initialize the combined signal
                combined_signal = segment_signal
                # Merge annotations if present
                if hasattr(segment_signal, 'annotations') and segment_signal.annotations:
                    combined_signal.annotations = segment_signal.annotations
            else:
                # Subsequent segments - concatenate signals
                if len(segment_signal.signals) != len(combined_signal.signals):
                    self.logWarning(f"Segment {i+1} has {len(segment_signal.signals)} signals, "
                                   f"expected {len(combined_signal.signals)}")
                    continue
                    
                for j, segment_sig in enumerate(segment_signal.signals):
                    if j < len(combined_signal.signals):
                        combined_sig = combined_signal.signals[j]
                        
                        # Verify signal compatibility
                        if segment_sig.frequency != combined_sig.frequency:
                            self.logWarning(f"Segment {i+1} signal {j} has different frequency: "
                                          f"{segment_sig.frequency} vs {combined_sig.frequency}")
                        
                        # Concatenate signal data
                        combined_sig.signal = np.concatenate([
                            combined_sig.signal.astype(np.float32), 
                            segment_sig.signal.astype(np.float32)
                        ]).astype(combined_sig.signal.dtype)
                
                # Merge annotations with time offset
                if hasattr(segment_signal, 'annotations') and segment_signal.annotations:
                    if not hasattr(combined_signal, 'annotations') or not combined_signal.annotations:
                        combined_signal.annotations = [[], [], []]  # onset, duration, description
                    
                    # Add time offset to annotations
                    segment_start = segment_start_times[i]
                    for k, onset in enumerate(segment_signal.annotations[0]):
                        combined_signal.annotations[0].append(onset + segment_start)
                        combined_signal.annotations[1].append(segment_signal.annotations[1][k])
                        combined_signal.annotations[2].append(segment_signal.annotations[2][k])
        
        combined_signal._segment_info = segment_info
        combined_signal._total_datarecords = total_datarecords
        combined_signal._is_segmented = True
        
        self.log(f"Successfully loaded {len(segment_files)} segments, "
                f"total duration: {current_time:.2f}s, "
                f"total datarecords: {total_datarecords}")
        
        return combined_signal
    
    def getMetaData(self, recordName):
        """Override to handle segmented files and provide merged dataCount"""
        # Get the file path (could be single file or list of segments)
        file_path = self.getFilePathSignal(recordName)
        
        if isinstance(file_path, list):
            # For segmented files, use the first segment for basic metadata
            # but calculate total dataCount from all segments
            return self._getSegmentedMetaData(file_path)
        else:
            # Single file - use parent implementation
            return super().getMetaData(recordName)
    
    def _getSegmentedMetaData(self, segment_files):
        """Get metadata for segmented files with merged dataCount"""
        if not segment_files:
            return {}
            
        # Use first segment for basic metadata
        first_segment = segment_files[0]
        
        metaData = self.getMetaDataFromFile(first_segment)
        
        # Calculate total dataCount from all segments
        total_datarecords = 0
        segment_details = []
        
        for i, segment_file in enumerate(segment_files):
            try:
                with pyedflib.EdfReader(segment_file) as f:
                    segment_datarecords = f.datarecords_in_file
                    
                    segment_details.append({
                        "segment": i + 1,
                        "file": Path(segment_file).name,
                        "datarecords": segment_datarecords,
                        "start": f.getStartdatetime(),
                        "start_stamp": total_datarecords
                    })

                    total_datarecords += segment_datarecords
                    
            except Exception as e:
                self.logWarning(f"Could not read datarecords from segment {segment_file}: {e}")
        
        metaData["dataCount"] = total_datarecords
        metaData["segments"] = segment_details
        
        return metaData
    
    def loadSignalHeaders(self, edfFile, annotations=False):
        """Override to handle segmented files"""
        if isinstance(edfFile, list):
            # For segmented files, use headers from first segment
            return super().loadSignalHeaders(edfFile[0], annotations)
        else:
            return super().loadSignalHeaders(edfFile, annotations)
    
    def loadSignalHeadersAndHandle(self, edfFile, annotations=False, checkTargetChannels=True):
        """Override to handle segmented files"""
        if isinstance(edfFile, list):
            # For segmented files, use first segment for headers but return special handle
            headers, f = super().loadSignalHeadersAndHandle(edfFile[0], annotations, checkTargetChannels)
            # Note: The file handle 'f' is only for the first segment
            # This might need special handling depending on usage
            return headers, f
        else:
            return super().loadSignalHeadersAndHandle(edfFile, annotations, checkTargetChannels)
