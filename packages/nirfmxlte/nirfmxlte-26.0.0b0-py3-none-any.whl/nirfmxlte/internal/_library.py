"""Wrapper around driver library.
Class will setup the correct ctypes information for every function on first call.
"""

import ctypes
import threading
from typing import Any

import nirfmxlte.errors as errors
import nirfmxlte.internal._custom_types as _custom_types


class Library(object):
    """Library

    Wrapper around driver library.
    Class will setup the correct ctypes information for every function on first call.
    """

    def __init__(self, ctypes_library):
        """Initialize the Library object."""
        self._func_lock = threading.Lock()
        self._library = ctypes_library
        # We cache the cfunc object from the ctypes.CDLL object
        self.RFmxLTE_ResetAttribute_cfunc = None
        self.RFmxLTE_GetError_cfunc = None
        self.RFmxLTE_GetErrorString_cfunc = None
        self.RFmxLTE_GetAttributeI8_cfunc = None
        self.RFmxLTE_SetAttributeI8_cfunc = None
        self.RFmxLTE_GetAttributeI8Array_cfunc = None
        self.RFmxLTE_SetAttributeI8Array_cfunc = None
        self.RFmxLTE_GetAttributeI16_cfunc = None
        self.RFmxLTE_SetAttributeI16_cfunc = None
        self.RFmxLTE_GetAttributeI32_cfunc = None
        self.RFmxLTE_SetAttributeI32_cfunc = None
        self.RFmxLTE_GetAttributeI32Array_cfunc = None
        self.RFmxLTE_SetAttributeI32Array_cfunc = None
        self.RFmxLTE_GetAttributeI64_cfunc = None
        self.RFmxLTE_SetAttributeI64_cfunc = None
        self.RFmxLTE_GetAttributeI64Array_cfunc = None
        self.RFmxLTE_SetAttributeI64Array_cfunc = None
        self.RFmxLTE_GetAttributeU8_cfunc = None
        self.RFmxLTE_SetAttributeU8_cfunc = None
        self.RFmxLTE_GetAttributeU8Array_cfunc = None
        self.RFmxLTE_SetAttributeU8Array_cfunc = None
        self.RFmxLTE_GetAttributeU16_cfunc = None
        self.RFmxLTE_SetAttributeU16_cfunc = None
        self.RFmxLTE_GetAttributeU32_cfunc = None
        self.RFmxLTE_SetAttributeU32_cfunc = None
        self.RFmxLTE_GetAttributeU32Array_cfunc = None
        self.RFmxLTE_SetAttributeU32Array_cfunc = None
        self.RFmxLTE_GetAttributeU64Array_cfunc = None
        self.RFmxLTE_SetAttributeU64Array_cfunc = None
        self.RFmxLTE_GetAttributeF32_cfunc = None
        self.RFmxLTE_SetAttributeF32_cfunc = None
        self.RFmxLTE_GetAttributeF32Array_cfunc = None
        self.RFmxLTE_SetAttributeF32Array_cfunc = None
        self.RFmxLTE_GetAttributeF64_cfunc = None
        self.RFmxLTE_SetAttributeF64_cfunc = None
        self.RFmxLTE_GetAttributeF64Array_cfunc = None
        self.RFmxLTE_SetAttributeF64Array_cfunc = None
        self.RFmxLTE_GetAttributeNIComplexSingleArray_cfunc = None
        self.RFmxLTE_SetAttributeNIComplexSingleArray_cfunc = None
        self.RFmxLTE_GetAttributeNIComplexDoubleArray_cfunc = None
        self.RFmxLTE_SetAttributeNIComplexDoubleArray_cfunc = None
        self.RFmxLTE_GetAttributeString_cfunc = None
        self.RFmxLTE_SetAttributeString_cfunc = None
        self.RFmxLTE_ACPValidateNoiseCalibrationData_cfunc = None
        self.RFmxLTE_CHPValidateNoiseCalibrationData_cfunc = None
        self.RFmxLTE_AbortMeasurements_cfunc = None
        self.RFmxLTE_AnalyzeIQ1Waveform_cfunc = None
        self.RFmxLTE_AnalyzeSpectrum1Waveform_cfunc = None
        self.RFmxLTE_AutoLevel_cfunc = None
        self.RFmxLTE_CheckMeasurementStatus_cfunc = None
        self.RFmxLTE_ClearAllNamedResults_cfunc = None
        self.RFmxLTE_ClearNamedResult_cfunc = None
        self.RFmxLTE_ClearNoiseCalibrationDatabase_cfunc = None
        self.RFmxLTE_CloneSignalConfiguration_cfunc = None
        self.RFmxLTE_Commit_cfunc = None
        self.RFmxLTE_CfgDigitalEdgeTrigger_cfunc = None
        self.RFmxLTE_CfgDownlinkAutoChannelDetection_cfunc = None
        self.RFmxLTE_CfgFrequencyEARFCN_cfunc = None
        self.RFmxLTE_CfgIQPowerEdgeTrigger_cfunc = None
        self.RFmxLTE_CfgSoftwareEdgeTrigger_cfunc = None
        self.RFmxLTE_CreateListStep_cfunc = None
        self.RFmxLTE_CreateList_cfunc = None
        self.RFmxLTE_CreateSignalConfiguration_cfunc = None
        self.RFmxLTE_DeleteList_cfunc = None
        self.RFmxLTE_DeleteSignalConfiguration_cfunc = None
        self.RFmxLTE_DisableTrigger_cfunc = None
        self.RFmxLTE_GetAllNamedResultNames_cfunc = None
        self.RFmxLTE_Initiate_cfunc = None
        self.RFmxLTE_ResetToDefault_cfunc = None
        self.RFmxLTE_SelectMeasurements_cfunc = None
        self.RFmxLTE_SendSoftwareEdgeTrigger_cfunc = None
        self.RFmxLTE_WaitForMeasurementComplete_cfunc = None
        self.RFmxLTE_ACPCfgAveraging_cfunc = None
        self.RFmxLTE_ACPCfgConfigurableNumberOfOffsetsEnabled_cfunc = None
        self.RFmxLTE_ACPCfgMeasurementMethod_cfunc = None
        self.RFmxLTE_ACPCfgNoiseCompensationEnabled_cfunc = None
        self.RFmxLTE_ACPCfgNumberOfEUTRAOffsets_cfunc = None
        self.RFmxLTE_ACPCfgNumberOfGSMOffsets_cfunc = None
        self.RFmxLTE_ACPCfgNumberOfUTRAOffsets_cfunc = None
        self.RFmxLTE_ACPCfgRBWFilter_cfunc = None
        self.RFmxLTE_ACPCfgSweepTime_cfunc = None
        self.RFmxLTE_ACPCfgUTRAAndEUTRAOffsets_cfunc = None
        self.RFmxLTE_ACPCfgPowerUnits_cfunc = None
        self.RFmxLTE_CHPCfgAveraging_cfunc = None
        self.RFmxLTE_CHPCfgIntegrationBandwidthType_cfunc = None
        self.RFmxLTE_CHPCfgRBWFilter_cfunc = None
        self.RFmxLTE_CHPCfgSweepTime_cfunc = None
        self.RFmxLTE_ModAccCfgAveraging_cfunc = None
        self.RFmxLTE_ModAccCfgCommonClockSourceEnabled_cfunc = None
        self.RFmxLTE_ModAccCfgEVMUnit_cfunc = None
        self.RFmxLTE_ModAccCfgFFTWindowOffset_cfunc = None
        self.RFmxLTE_ModAccCfgFFTWindowPosition_cfunc = None
        self.RFmxLTE_ModAccCfgInBandEmissionMaskType_cfunc = None
        self.RFmxLTE_ModAccCfgSynchronizationModeAndInterval_cfunc = None
        self.RFmxLTE_OBWCfgAveraging_cfunc = None
        self.RFmxLTE_OBWCfgRBWFilter_cfunc = None
        self.RFmxLTE_OBWCfgSweepTime_cfunc = None
        self.RFmxLTE_SEMCfgAveraging_cfunc = None
        self.RFmxLTE_SEMCfgComponentCarrierMaximumOutputPowerArray_cfunc = None
        self.RFmxLTE_SEMCfgComponentCarrierMaximumOutputPower_cfunc = None
        self.RFmxLTE_SEMCfgDownlinkMask_cfunc = None
        self.RFmxLTE_SEMCfgNumberOfOffsets_cfunc = None
        self.RFmxLTE_SEMCfgOffsetAbsoluteLimitArray_cfunc = None
        self.RFmxLTE_SEMCfgOffsetAbsoluteLimit_cfunc = None
        self.RFmxLTE_SEMCfgOffsetBandwidthIntegralArray_cfunc = None
        self.RFmxLTE_SEMCfgOffsetBandwidthIntegral_cfunc = None
        self.RFmxLTE_SEMCfgOffsetFrequencyArray_cfunc = None
        self.RFmxLTE_SEMCfgOffsetFrequency_cfunc = None
        self.RFmxLTE_SEMCfgOffsetLimitFailMaskArray_cfunc = None
        self.RFmxLTE_SEMCfgOffsetLimitFailMask_cfunc = None
        self.RFmxLTE_SEMCfgOffsetRBWFilterArray_cfunc = None
        self.RFmxLTE_SEMCfgOffsetRBWFilter_cfunc = None
        self.RFmxLTE_SEMCfgOffsetRelativeLimitArray_cfunc = None
        self.RFmxLTE_SEMCfgOffsetRelativeLimit_cfunc = None
        self.RFmxLTE_SEMCfgSweepTime_cfunc = None
        self.RFmxLTE_SEMCfgUplinkMaskType_cfunc = None
        self.RFmxLTE_PVTCfgAveraging_cfunc = None
        self.RFmxLTE_PVTCfgMeasurementMethod_cfunc = None
        self.RFmxLTE_PVTCfgOFFPowerExclusionPeriods_cfunc = None
        self.RFmxLTE_SlotPhaseCfgSynchronizationModeAndInterval_cfunc = None
        self.RFmxLTE_SlotPowerCfgMeasurementInterval_cfunc = None
        self.RFmxLTE_TXPCfgAveraging_cfunc = None
        self.RFmxLTE_TXPCfgMeasurementOffsetAndInterval_cfunc = None
        self.RFmxLTE_CfgAutoDMRSDetectionEnabled_cfunc = None
        self.RFmxLTE_CfgAutoNPUSCHChannelDetectionEnabled_cfunc = None
        self.RFmxLTE_CfgAutoResourceBlockDetectionEnabled_cfunc = None
        self.RFmxLTE_CfgBand_cfunc = None
        self.RFmxLTE_CfgCellSpecificRatio_cfunc = None
        self.RFmxLTE_CfgComponentCarrierArray_cfunc = None
        self.RFmxLTE_CfgComponentCarrierSpacing_cfunc = None
        self.RFmxLTE_CfgComponentCarrier_cfunc = None
        self.RFmxLTE_CfgDownlinkAutoCellIDDetectionEnabled_cfunc = None
        self.RFmxLTE_CfgDownlinkChannelConfigurationMode_cfunc = None
        self.RFmxLTE_CfgDownlinkNumberOfSubframes_cfunc = None
        self.RFmxLTE_CfgDownlinkSynchronizationSignal_cfunc = None
        self.RFmxLTE_CfgDownlinkTestModelArray_cfunc = None
        self.RFmxLTE_CfgDownlinkTestModel_cfunc = None
        self.RFmxLTE_CfgDuplexScheme_cfunc = None
        self.RFmxLTE_CfgEMTCAnalysisEnabled_cfunc = None
        self.RFmxLTE_CfgeNodeBCategory_cfunc = None
        self.RFmxLTE_CfgExternalAttenuation_cfunc = None
        self.RFmxLTE_CfgFrequency_cfunc = None
        self.RFmxLTE_CfgLinkDirection_cfunc = None
        self.RFmxLTE_CfgNBIoTComponentCarrier_cfunc = None
        self.RFmxLTE_CfgNPUSCHDMRS_cfunc = None
        self.RFmxLTE_CfgNPUSCHFormat_cfunc = None
        self.RFmxLTE_CfgNPUSCHStartingSlot_cfunc = None
        self.RFmxLTE_CfgNPUSCHTones_cfunc = None
        self.RFmxLTE_CfgNumberOfComponentCarriers_cfunc = None
        self.RFmxLTE_CfgNumberOfDUTAntennas_cfunc = None
        self.RFmxLTE_CfgNumberOfPDSCHChannels_cfunc = None
        self.RFmxLTE_CfgNumberOfPUSCHResourceBlockClusters_cfunc = None
        self.RFmxLTE_CfgNumberOfSubblocks_cfunc = None
        self.RFmxLTE_CfgPBCH_cfunc = None
        self.RFmxLTE_CfgPCFICH_cfunc = None
        self.RFmxLTE_CfgPDCCH_cfunc = None
        self.RFmxLTE_CfgPDSCH_cfunc = None
        self.RFmxLTE_CfgPHICH_cfunc = None
        self.RFmxLTE_CfgPSSCHModulationType_cfunc = None
        self.RFmxLTE_CfgPSSCHResourceBlocks_cfunc = None
        self.RFmxLTE_CfgPUSCHModulationType_cfunc = None
        self.RFmxLTE_CfgPUSCHResourceBlocks_cfunc = None
        self.RFmxLTE_CfgReferenceLevel_cfunc = None
        self.RFmxLTE_CfgRF_cfunc = None
        self.RFmxLTE_CfgTransmitAntennaToAnalyze_cfunc = None
        self.RFmxLTE_ACPFetchComponentCarrierMeasurement_cfunc = None
        self.RFmxLTE_ACPFetchOffsetMeasurement_cfunc = None
        self.RFmxLTE_ACPFetchSubblockMeasurement_cfunc = None
        self.RFmxLTE_ACPFetchTotalAggregatedPower_cfunc = None
        self.RFmxLTE_CHPFetchComponentCarrierMeasurement_cfunc = None
        self.RFmxLTE_CHPFetchSubblockMeasurement_cfunc = None
        self.RFmxLTE_CHPFetchTotalAggregatedPower_cfunc = None
        self.RFmxLTE_ModAccFetchCompositeEVM_cfunc = None
        self.RFmxLTE_ModAccFetchCompositeMagnitudeAndPhaseError_cfunc = None
        self.RFmxLTE_ModAccFetchCSRSEVM_cfunc = None
        self.RFmxLTE_ModAccFetchDownlinkDetectedCellID_cfunc = None
        self.RFmxLTE_ModAccFetchDownlinkTransmitPower_cfunc = None
        self.RFmxLTE_ModAccFetchInBandEmissionMargin_cfunc = None
        self.RFmxLTE_ModAccFetchIQImpairments_cfunc = None
        self.RFmxLTE_ModAccFetchNPUSCHDataEVM_cfunc = None
        self.RFmxLTE_ModAccFetchNPUSCHDMRSEVM_cfunc = None
        self.RFmxLTE_ModAccFetchNPUSCHSymbolPower_cfunc = None
        self.RFmxLTE_ModAccFetchPDSCH1024QAMEVM_cfunc = None
        self.RFmxLTE_ModAccFetchPDSCHEVM_cfunc = None
        self.RFmxLTE_ModAccFetchPSSCHDataEVM_cfunc = None
        self.RFmxLTE_ModAccFetchPSSCHDMRSEVM_cfunc = None
        self.RFmxLTE_ModAccFetchPSSCHSymbolPower_cfunc = None
        self.RFmxLTE_ModAccFetchPUSCHDataEVM_cfunc = None
        self.RFmxLTE_ModAccFetchPUSCHDMRSEVM_cfunc = None
        self.RFmxLTE_ModAccFetchPUSCHSymbolPower_cfunc = None
        self.RFmxLTE_ModAccFetchSpectralFlatness_cfunc = None
        self.RFmxLTE_ModAccFetchSRSEVM_cfunc = None
        self.RFmxLTE_ModAccFetchSubblockInBandEmissionMargin_cfunc = None
        self.RFmxLTE_ModAccFetchSubblockIQImpairments_cfunc = None
        self.RFmxLTE_ModAccFetchSynchronizationSignalEVM_cfunc = None
        self.RFmxLTE_OBWFetchMeasurement_cfunc = None
        self.RFmxLTE_SEMFetchComponentCarrierMeasurement_cfunc = None
        self.RFmxLTE_SEMFetchLowerOffsetMargin_cfunc = None
        self.RFmxLTE_SEMFetchLowerOffsetPower_cfunc = None
        self.RFmxLTE_SEMFetchMeasurementStatus_cfunc = None
        self.RFmxLTE_SEMFetchSubblockMeasurement_cfunc = None
        self.RFmxLTE_SEMFetchTotalAggregatedPower_cfunc = None
        self.RFmxLTE_SEMFetchUpperOffsetMargin_cfunc = None
        self.RFmxLTE_SEMFetchUpperOffsetPower_cfunc = None
        self.RFmxLTE_PVTFetchMeasurement_cfunc = None
        self.RFmxLTE_SlotPhaseFetchMaximumPhaseDiscontinuity_cfunc = None
        self.RFmxLTE_TXPFetchMeasurement_cfunc = None
        self.RFmxLTE_ACPFetchAbsolutePowersTrace_cfunc = None
        self.RFmxLTE_ACPFetchComponentCarrierMeasurementArray_cfunc = None
        self.RFmxLTE_ACPFetchOffsetMeasurementArray_cfunc = None
        self.RFmxLTE_ACPFetchRelativePowersTrace_cfunc = None
        self.RFmxLTE_ACPFetchSpectrum_cfunc = None
        self.RFmxLTE_CHPFetchComponentCarrierMeasurementArray_cfunc = None
        self.RFmxLTE_CHPFetchSpectrum_cfunc = None
        self.RFmxLTE_ModAccFetchCompositeEVMArray_cfunc = None
        self.RFmxLTE_ModAccFetchCompositeMagnitudeAndPhaseErrorArray_cfunc = None
        self.RFmxLTE_ModAccFetchCSRSConstellation_cfunc = None
        self.RFmxLTE_ModAccFetchCSRSEVMArray_cfunc = None
        self.RFmxLTE_ModAccFetchDownlinkDetectedCellIDArray_cfunc = None
        self.RFmxLTE_ModAccFetchDownlinkPBCHConstellation_cfunc = None
        self.RFmxLTE_ModAccFetchDownlinkPCFICHConstellation_cfunc = None
        self.RFmxLTE_ModAccFetchDownlinkPDCCHConstellation_cfunc = None
        self.RFmxLTE_ModAccFetchDownlinkPHICHConstellation_cfunc = None
        self.RFmxLTE_ModAccFetchDownlinkTransmitPowerArray_cfunc = None
        self.RFmxLTE_ModAccFetchEVMPerSlotTrace_cfunc = None
        self.RFmxLTE_ModAccFetchEVMPerSubcarrierTrace_cfunc = None
        self.RFmxLTE_ModAccFetchEVMPerSymbolTrace_cfunc = None
        self.RFmxLTE_ModAccFetchEVMHighPerSymbolTrace_cfunc = None
        self.RFmxLTE_ModAccFetchMaximumEVMHighPerSymbolTrace_cfunc = None
        self.RFmxLTE_ModAccFetchEVMLowPerSymbolTrace_cfunc = None
        self.RFmxLTE_ModAccFetchMaximumEVMLowPerSymbolTrace_cfunc = None
        self.RFmxLTE_ModAccFetchInBandEmissionMarginArray_cfunc = None
        self.RFmxLTE_ModAccFetchInBandEmissionTrace_cfunc = None
        self.RFmxLTE_ModAccFetchIQImpairmentsArray_cfunc = None
        self.RFmxLTE_ModAccFetchMaximumEVMPerSlotTrace_cfunc = None
        self.RFmxLTE_ModAccFetchMaximumEVMPerSubcarrierTrace_cfunc = None
        self.RFmxLTE_ModAccFetchMaximumEVMPerSymbolTrace_cfunc = None
        self.RFmxLTE_ModAccFetchMaximumMagnitudeErrorPerSymbolTrace_cfunc = None
        self.RFmxLTE_ModAccFetchMaximumPhaseErrorPerSymbolTrace_cfunc = None
        self.RFmxLTE_ModAccFetchNPUSCHConstellationTrace_cfunc = None
        self.RFmxLTE_ModAccFetchPDSCH1024QAMConstellation_cfunc = None
        self.RFmxLTE_ModAccFetchPDSCH1024QAMEVMArray_cfunc = None
        self.RFmxLTE_ModAccFetchPDSCH16QAMConstellation_cfunc = None
        self.RFmxLTE_ModAccFetchPDSCH256QAMConstellation_cfunc = None
        self.RFmxLTE_ModAccFetchPDSCH64QAMConstellation_cfunc = None
        self.RFmxLTE_ModAccFetchPDSCHEVMArray_cfunc = None
        self.RFmxLTE_ModAccFetchPDSCHQPSKConstellation_cfunc = None
        self.RFmxLTE_ModAccFetchPSSCHConstellationTrace_cfunc = None
        self.RFmxLTE_ModAccFetchPSSCHDataEVMArray_cfunc = None
        self.RFmxLTE_ModAccFetchPSSCHDMRSEVMArray_cfunc = None
        self.RFmxLTE_ModAccFetchPSSCHSymbolPowerArray_cfunc = None
        self.RFmxLTE_ModAccFetchPUSCHConstellationTrace_cfunc = None
        self.RFmxLTE_ModAccFetchPUSCHDataEVMArray_cfunc = None
        self.RFmxLTE_ModAccFetchPUSCHDemodulatedBits_cfunc = None
        self.RFmxLTE_ModAccFetchPUSCHDMRSEVMArray_cfunc = None
        self.RFmxLTE_ModAccFetchPUSCHSymbolPowerArray_cfunc = None
        self.RFmxLTE_ModAccFetchRMSMagnitudeErrorPerSymbolTrace_cfunc = None
        self.RFmxLTE_ModAccFetchRMSPhaseErrorPerSymbolTrace_cfunc = None
        self.RFmxLTE_ModAccFetchSpectralFlatnessArray_cfunc = None
        self.RFmxLTE_ModAccFetchSpectralFlatnessTrace_cfunc = None
        self.RFmxLTE_ModAccFetchSRSConstellation_cfunc = None
        self.RFmxLTE_ModAccFetchSRSEVMArray_cfunc = None
        self.RFmxLTE_ModAccFetchSubblockInBandEmissionTrace_cfunc = None
        self.RFmxLTE_ModAccFetchSynchronizationSignalConstellation_cfunc = None
        self.RFmxLTE_ModAccFetchSynchronizationSignalEVMArray_cfunc = None
        self.RFmxLTE_ModAccFetchMaximumFrequencyErrorPerSlotTrace_cfunc = None
        self.RFmxLTE_ModAccFetchNPDSCHQPSKConstellation_cfunc = None
        self.RFmxLTE_ModAccFetchNRSConstellation_cfunc = None
        self.RFmxLTE_ModAccFetchNBSynchronizationSignalConstellation_cfunc = None
        self.RFmxLTE_OBWFetchSpectrum_cfunc = None
        self.RFmxLTE_SEMFetchComponentCarrierMeasurementArray_cfunc = None
        self.RFmxLTE_SEMFetchLowerOffsetMarginArray_cfunc = None
        self.RFmxLTE_SEMFetchLowerOffsetPowerArray_cfunc = None
        self.RFmxLTE_SEMFetchSpectrum_cfunc = None
        self.RFmxLTE_SEMFetchUpperOffsetMarginArray_cfunc = None
        self.RFmxLTE_SEMFetchUpperOffsetPowerArray_cfunc = None
        self.RFmxLTE_PVTFetchMeasurementArray_cfunc = None
        self.RFmxLTE_PVTFetchSignalPowerTrace_cfunc = None
        self.RFmxLTE_SlotPhaseFetchMaximumPhaseDiscontinuityArray_cfunc = None
        self.RFmxLTE_SlotPhaseFetchPhaseDiscontinuities_cfunc = None
        self.RFmxLTE_SlotPhaseFetchSamplePhaseErrorLinearFitTrace_cfunc = None
        self.RFmxLTE_SlotPhaseFetchSamplePhaseError_cfunc = None
        self.RFmxLTE_SlotPowerFetchPowers_cfunc = None
        self.RFmxLTE_TXPFetchPowerTrace_cfunc = None

    def _get_library_function(self, name: str) -> Any:
        try:
            function = getattr(self._library, name)
        except AttributeError as e:
            raise errors.DriverTooOldError() from e  # type: ignore
        return function

    def RFmxLTE_ResetAttribute(self, vi, selector_string, attribute_id):
        """RFmxLTE_ResetAttribute."""
        with self._func_lock:
            if self.RFmxLTE_ResetAttribute_cfunc is None:
                self.RFmxLTE_ResetAttribute_cfunc = self._get_library_function(
                    "RFmxLTE_ResetAttribute"
                )
                self.RFmxLTE_ResetAttribute_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                ]
                self.RFmxLTE_ResetAttribute_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ResetAttribute_cfunc(vi, selector_string, attribute_id)

    def RFmxLTE_GetError(self, vi, error_code, error_description_buffer_size, error_description):
        """RFmxLTE_GetError."""
        with self._func_lock:
            if self.RFmxLTE_GetError_cfunc is None:
                self.RFmxLTE_GetError_cfunc = self._get_library_function("RFmxLTE_GetError")
                self.RFmxLTE_GetError_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_int32),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_char),
                ]
                self.RFmxLTE_GetError_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_GetError_cfunc(
            vi, error_code, error_description_buffer_size, error_description
        )

    def RFmxLTE_GetErrorString(
        self, vi, error_code, error_description_buffer_size, error_description
    ):
        """RFmxLTE_GetErrorString."""
        with self._func_lock:
            if self.RFmxLTE_GetErrorString_cfunc is None:
                self.RFmxLTE_GetErrorString_cfunc = self._get_library_function(
                    "RFmxLTE_GetErrorString"
                )
                self.RFmxLTE_GetErrorString_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.c_int32,
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_char),
                ]
                self.RFmxLTE_GetErrorString_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_GetErrorString_cfunc(
            vi, error_code, error_description_buffer_size, error_description
        )

    def RFmxLTE_GetAttributeI8(self, vi, selector_string, attribute_id, attr_val):
        """RFmxLTE_GetAttributeI8."""
        with self._func_lock:
            if self.RFmxLTE_GetAttributeI8_cfunc is None:
                self.RFmxLTE_GetAttributeI8_cfunc = self._get_library_function(
                    "RFmxLTE_GetAttributeI8"
                )
                self.RFmxLTE_GetAttributeI8_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_int8),
                ]
                self.RFmxLTE_GetAttributeI8_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_GetAttributeI8_cfunc(vi, selector_string, attribute_id, attr_val)

    def RFmxLTE_SetAttributeI8(self, vi, selector_string, attribute_id, attr_val):
        """RFmxLTE_SetAttributeI8."""
        with self._func_lock:
            if self.RFmxLTE_SetAttributeI8_cfunc is None:
                self.RFmxLTE_SetAttributeI8_cfunc = self._get_library_function(
                    "RFmxLTE_SetAttributeI8"
                )
                self.RFmxLTE_SetAttributeI8_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.c_int8,
                ]
                self.RFmxLTE_SetAttributeI8_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_SetAttributeI8_cfunc(vi, selector_string, attribute_id, attr_val)

    def RFmxLTE_GetAttributeI16(self, vi, selector_string, attribute_id, attr_val):
        """RFmxLTE_GetAttributeI16."""
        with self._func_lock:
            if self.RFmxLTE_GetAttributeI16_cfunc is None:
                self.RFmxLTE_GetAttributeI16_cfunc = self._get_library_function(
                    "RFmxLTE_GetAttributeI16"
                )
                self.RFmxLTE_GetAttributeI16_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_int16),
                ]
                self.RFmxLTE_GetAttributeI16_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_GetAttributeI16_cfunc(vi, selector_string, attribute_id, attr_val)

    def RFmxLTE_SetAttributeI16(self, vi, selector_string, attribute_id, attr_val):
        """RFmxLTE_SetAttributeI16."""
        with self._func_lock:
            if self.RFmxLTE_SetAttributeI16_cfunc is None:
                self.RFmxLTE_SetAttributeI16_cfunc = self._get_library_function(
                    "RFmxLTE_SetAttributeI16"
                )
                self.RFmxLTE_SetAttributeI16_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.c_int16,
                ]
                self.RFmxLTE_SetAttributeI16_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_SetAttributeI16_cfunc(vi, selector_string, attribute_id, attr_val)

    def RFmxLTE_GetAttributeI32(self, vi, selector_string, attribute_id, attr_val):
        """RFmxLTE_GetAttributeI32."""
        with self._func_lock:
            if self.RFmxLTE_GetAttributeI32_cfunc is None:
                self.RFmxLTE_GetAttributeI32_cfunc = self._get_library_function(
                    "RFmxLTE_GetAttributeI32"
                )
                self.RFmxLTE_GetAttributeI32_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxLTE_GetAttributeI32_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_GetAttributeI32_cfunc(vi, selector_string, attribute_id, attr_val)

    def RFmxLTE_SetAttributeI32(self, vi, selector_string, attribute_id, attr_val):
        """RFmxLTE_SetAttributeI32."""
        with self._func_lock:
            if self.RFmxLTE_SetAttributeI32_cfunc is None:
                self.RFmxLTE_SetAttributeI32_cfunc = self._get_library_function(
                    "RFmxLTE_SetAttributeI32"
                )
                self.RFmxLTE_SetAttributeI32_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.c_int32,
                ]
                self.RFmxLTE_SetAttributeI32_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_SetAttributeI32_cfunc(vi, selector_string, attribute_id, attr_val)

    def RFmxLTE_GetAttributeI64(self, vi, selector_string, attribute_id, attr_val):
        """RFmxLTE_GetAttributeI64."""
        with self._func_lock:
            if self.RFmxLTE_GetAttributeI64_cfunc is None:
                self.RFmxLTE_GetAttributeI64_cfunc = self._get_library_function(
                    "RFmxLTE_GetAttributeI64"
                )
                self.RFmxLTE_GetAttributeI64_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_int64),
                ]
                self.RFmxLTE_GetAttributeI64_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_GetAttributeI64_cfunc(vi, selector_string, attribute_id, attr_val)

    def RFmxLTE_SetAttributeI64(self, vi, selector_string, attribute_id, attr_val):
        """RFmxLTE_SetAttributeI64."""
        with self._func_lock:
            if self.RFmxLTE_SetAttributeI64_cfunc is None:
                self.RFmxLTE_SetAttributeI64_cfunc = self._get_library_function(
                    "RFmxLTE_SetAttributeI64"
                )
                self.RFmxLTE_SetAttributeI64_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.c_int64,
                ]
                self.RFmxLTE_SetAttributeI64_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_SetAttributeI64_cfunc(vi, selector_string, attribute_id, attr_val)

    def RFmxLTE_GetAttributeU8(self, vi, selector_string, attribute_id, attr_val):
        """RFmxLTE_GetAttributeU8."""
        with self._func_lock:
            if self.RFmxLTE_GetAttributeU8_cfunc is None:
                self.RFmxLTE_GetAttributeU8_cfunc = self._get_library_function(
                    "RFmxLTE_GetAttributeU8"
                )
                self.RFmxLTE_GetAttributeU8_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_uint8),
                ]
                self.RFmxLTE_GetAttributeU8_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_GetAttributeU8_cfunc(vi, selector_string, attribute_id, attr_val)

    def RFmxLTE_SetAttributeU8(self, vi, selector_string, attribute_id, attr_val):
        """RFmxLTE_SetAttributeU8."""
        with self._func_lock:
            if self.RFmxLTE_SetAttributeU8_cfunc is None:
                self.RFmxLTE_SetAttributeU8_cfunc = self._get_library_function(
                    "RFmxLTE_SetAttributeU8"
                )
                self.RFmxLTE_SetAttributeU8_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.c_uint8,
                ]
                self.RFmxLTE_SetAttributeU8_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_SetAttributeU8_cfunc(vi, selector_string, attribute_id, attr_val)

    def RFmxLTE_GetAttributeU16(self, vi, selector_string, attribute_id, attr_val):
        """RFmxLTE_GetAttributeU16."""
        with self._func_lock:
            if self.RFmxLTE_GetAttributeU16_cfunc is None:
                self.RFmxLTE_GetAttributeU16_cfunc = self._get_library_function(
                    "RFmxLTE_GetAttributeU16"
                )
                self.RFmxLTE_GetAttributeU16_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_uint16),
                ]
                self.RFmxLTE_GetAttributeU16_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_GetAttributeU16_cfunc(vi, selector_string, attribute_id, attr_val)

    def RFmxLTE_SetAttributeU16(self, vi, selector_string, attribute_id, attr_val):
        """RFmxLTE_SetAttributeU16."""
        with self._func_lock:
            if self.RFmxLTE_SetAttributeU16_cfunc is None:
                self.RFmxLTE_SetAttributeU16_cfunc = self._get_library_function(
                    "RFmxLTE_SetAttributeU16"
                )
                self.RFmxLTE_SetAttributeU16_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.c_uint16,
                ]
                self.RFmxLTE_SetAttributeU16_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_SetAttributeU16_cfunc(vi, selector_string, attribute_id, attr_val)

    def RFmxLTE_GetAttributeU32(self, vi, selector_string, attribute_id, attr_val):
        """RFmxLTE_GetAttributeU32."""
        with self._func_lock:
            if self.RFmxLTE_GetAttributeU32_cfunc is None:
                self.RFmxLTE_GetAttributeU32_cfunc = self._get_library_function(
                    "RFmxLTE_GetAttributeU32"
                )
                self.RFmxLTE_GetAttributeU32_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_uint32),
                ]
                self.RFmxLTE_GetAttributeU32_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_GetAttributeU32_cfunc(vi, selector_string, attribute_id, attr_val)

    def RFmxLTE_SetAttributeU32(self, vi, selector_string, attribute_id, attr_val):
        """RFmxLTE_SetAttributeU32."""
        with self._func_lock:
            if self.RFmxLTE_SetAttributeU32_cfunc is None:
                self.RFmxLTE_SetAttributeU32_cfunc = self._get_library_function(
                    "RFmxLTE_SetAttributeU32"
                )
                self.RFmxLTE_SetAttributeU32_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.c_uint32,
                ]
                self.RFmxLTE_SetAttributeU32_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_SetAttributeU32_cfunc(vi, selector_string, attribute_id, attr_val)

    def RFmxLTE_GetAttributeF32(self, vi, selector_string, attribute_id, attr_val):
        """RFmxLTE_GetAttributeF32."""
        with self._func_lock:
            if self.RFmxLTE_GetAttributeF32_cfunc is None:
                self.RFmxLTE_GetAttributeF32_cfunc = self._get_library_function(
                    "RFmxLTE_GetAttributeF32"
                )
                self.RFmxLTE_GetAttributeF32_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_float),
                ]
                self.RFmxLTE_GetAttributeF32_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_GetAttributeF32_cfunc(vi, selector_string, attribute_id, attr_val)

    def RFmxLTE_SetAttributeF32(self, vi, selector_string, attribute_id, attr_val):
        """RFmxLTE_SetAttributeF32."""
        with self._func_lock:
            if self.RFmxLTE_SetAttributeF32_cfunc is None:
                self.RFmxLTE_SetAttributeF32_cfunc = self._get_library_function(
                    "RFmxLTE_SetAttributeF32"
                )
                self.RFmxLTE_SetAttributeF32_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.c_float,
                ]
                self.RFmxLTE_SetAttributeF32_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_SetAttributeF32_cfunc(vi, selector_string, attribute_id, attr_val)

    def RFmxLTE_GetAttributeF64(self, vi, selector_string, attribute_id, attr_val):
        """RFmxLTE_GetAttributeF64."""
        with self._func_lock:
            if self.RFmxLTE_GetAttributeF64_cfunc is None:
                self.RFmxLTE_GetAttributeF64_cfunc = self._get_library_function(
                    "RFmxLTE_GetAttributeF64"
                )
                self.RFmxLTE_GetAttributeF64_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxLTE_GetAttributeF64_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_GetAttributeF64_cfunc(vi, selector_string, attribute_id, attr_val)

    def RFmxLTE_SetAttributeF64(self, vi, selector_string, attribute_id, attr_val):
        """RFmxLTE_SetAttributeF64."""
        with self._func_lock:
            if self.RFmxLTE_SetAttributeF64_cfunc is None:
                self.RFmxLTE_SetAttributeF64_cfunc = self._get_library_function(
                    "RFmxLTE_SetAttributeF64"
                )
                self.RFmxLTE_SetAttributeF64_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.c_double,
                ]
                self.RFmxLTE_SetAttributeF64_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_SetAttributeF64_cfunc(vi, selector_string, attribute_id, attr_val)

    def RFmxLTE_GetAttributeI8Array(
        self, vi, selector_string, attribute_id, attr_val, array_size, actual_array_size
    ):
        """RFmxLTE_GetAttributeI8Array."""
        with self._func_lock:
            if self.RFmxLTE_GetAttributeI8Array_cfunc is None:
                self.RFmxLTE_GetAttributeI8Array_cfunc = self._get_library_function(
                    "RFmxLTE_GetAttributeI8Array"
                )
                self.RFmxLTE_GetAttributeI8Array_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_int8),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxLTE_GetAttributeI8Array_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_GetAttributeI8Array_cfunc(
            vi, selector_string, attribute_id, attr_val, array_size, actual_array_size
        )

    def RFmxLTE_SetAttributeI8Array(self, vi, selector_string, attribute_id, attr_val, array_size):
        """RFmxLTE_SetAttributeI8Array."""
        with self._func_lock:
            if self.RFmxLTE_SetAttributeI8Array_cfunc is None:
                self.RFmxLTE_SetAttributeI8Array_cfunc = self._get_library_function(
                    "RFmxLTE_SetAttributeI8Array"
                )
                self.RFmxLTE_SetAttributeI8Array_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_int8),
                    ctypes.c_uint32,
                ]
                self.RFmxLTE_SetAttributeI8Array_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_SetAttributeI8Array_cfunc(
            vi, selector_string, attribute_id, attr_val, array_size
        )

    def RFmxLTE_GetAttributeI32Array(
        self, vi, selector_string, attribute_id, attr_val, array_size, actual_array_size
    ):
        """RFmxLTE_GetAttributeI32Array."""
        with self._func_lock:
            if self.RFmxLTE_GetAttributeI32Array_cfunc is None:
                self.RFmxLTE_GetAttributeI32Array_cfunc = self._get_library_function(
                    "RFmxLTE_GetAttributeI32Array"
                )
                self.RFmxLTE_GetAttributeI32Array_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_int32),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxLTE_GetAttributeI32Array_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_GetAttributeI32Array_cfunc(
            vi, selector_string, attribute_id, attr_val, array_size, actual_array_size
        )

    def RFmxLTE_SetAttributeI32Array(self, vi, selector_string, attribute_id, attr_val, array_size):
        """RFmxLTE_SetAttributeI32Array."""
        with self._func_lock:
            if self.RFmxLTE_SetAttributeI32Array_cfunc is None:
                self.RFmxLTE_SetAttributeI32Array_cfunc = self._get_library_function(
                    "RFmxLTE_SetAttributeI32Array"
                )
                self.RFmxLTE_SetAttributeI32Array_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_int32),
                    ctypes.c_uint32,
                ]
                self.RFmxLTE_SetAttributeI32Array_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_SetAttributeI32Array_cfunc(
            vi, selector_string, attribute_id, attr_val, array_size
        )

    def RFmxLTE_GetAttributeI64Array(
        self, vi, selector_string, attribute_id, attr_val, array_size, actual_array_size
    ):
        """RFmxLTE_GetAttributeI64Array."""
        with self._func_lock:
            if self.RFmxLTE_GetAttributeI64Array_cfunc is None:
                self.RFmxLTE_GetAttributeI64Array_cfunc = self._get_library_function(
                    "RFmxLTE_GetAttributeI64Array"
                )
                self.RFmxLTE_GetAttributeI64Array_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_int64),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxLTE_GetAttributeI64Array_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_GetAttributeI64Array_cfunc(
            vi, selector_string, attribute_id, attr_val, array_size, actual_array_size
        )

    def RFmxLTE_SetAttributeI64Array(self, vi, selector_string, attribute_id, attr_val, array_size):
        """RFmxLTE_SetAttributeI64Array."""
        with self._func_lock:
            if self.RFmxLTE_SetAttributeI64Array_cfunc is None:
                self.RFmxLTE_SetAttributeI64Array_cfunc = self._get_library_function(
                    "RFmxLTE_SetAttributeI64Array"
                )
                self.RFmxLTE_SetAttributeI64Array_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_int64),
                    ctypes.c_uint32,
                ]
                self.RFmxLTE_SetAttributeI64Array_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_SetAttributeI64Array_cfunc(
            vi, selector_string, attribute_id, attr_val, array_size
        )

    def RFmxLTE_GetAttributeU8Array(
        self, vi, selector_string, attribute_id, attr_val, array_size, actual_array_size
    ):
        """RFmxLTE_GetAttributeU8Array."""
        with self._func_lock:
            if self.RFmxLTE_GetAttributeU8Array_cfunc is None:
                self.RFmxLTE_GetAttributeU8Array_cfunc = self._get_library_function(
                    "RFmxLTE_GetAttributeU8Array"
                )
                self.RFmxLTE_GetAttributeU8Array_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_uint8),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxLTE_GetAttributeU8Array_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_GetAttributeU8Array_cfunc(
            vi, selector_string, attribute_id, attr_val, array_size, actual_array_size
        )

    def RFmxLTE_SetAttributeU8Array(self, vi, selector_string, attribute_id, attr_val, array_size):
        """RFmxLTE_SetAttributeU8Array."""
        with self._func_lock:
            if self.RFmxLTE_SetAttributeU8Array_cfunc is None:
                self.RFmxLTE_SetAttributeU8Array_cfunc = self._get_library_function(
                    "RFmxLTE_SetAttributeU8Array"
                )
                self.RFmxLTE_SetAttributeU8Array_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_uint8),
                    ctypes.c_uint32,
                ]
                self.RFmxLTE_SetAttributeU8Array_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_SetAttributeU8Array_cfunc(
            vi, selector_string, attribute_id, attr_val, array_size
        )

    def RFmxLTE_GetAttributeU32Array(
        self, vi, selector_string, attribute_id, attr_val, array_size, actual_array_size
    ):
        """RFmxLTE_GetAttributeU32Array."""
        with self._func_lock:
            if self.RFmxLTE_GetAttributeU32Array_cfunc is None:
                self.RFmxLTE_GetAttributeU32Array_cfunc = self._get_library_function(
                    "RFmxLTE_GetAttributeU32Array"
                )
                self.RFmxLTE_GetAttributeU32Array_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_uint32),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxLTE_GetAttributeU32Array_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_GetAttributeU32Array_cfunc(
            vi, selector_string, attribute_id, attr_val, array_size, actual_array_size
        )

    def RFmxLTE_SetAttributeU32Array(self, vi, selector_string, attribute_id, attr_val, array_size):
        """RFmxLTE_SetAttributeU32Array."""
        with self._func_lock:
            if self.RFmxLTE_SetAttributeU32Array_cfunc is None:
                self.RFmxLTE_SetAttributeU32Array_cfunc = self._get_library_function(
                    "RFmxLTE_SetAttributeU32Array"
                )
                self.RFmxLTE_SetAttributeU32Array_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_uint32),
                    ctypes.c_uint32,
                ]
                self.RFmxLTE_SetAttributeU32Array_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_SetAttributeU32Array_cfunc(
            vi, selector_string, attribute_id, attr_val, array_size
        )

    def RFmxLTE_GetAttributeU64Array(
        self, vi, selector_string, attribute_id, attr_val, array_size, actual_array_size
    ):
        """RFmxLTE_GetAttributeU64Array."""
        with self._func_lock:
            if self.RFmxLTE_GetAttributeU64Array_cfunc is None:
                self.RFmxLTE_GetAttributeU64Array_cfunc = self._get_library_function(
                    "RFmxLTE_GetAttributeU64Array"
                )
                self.RFmxLTE_GetAttributeU64Array_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_uint64),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxLTE_GetAttributeU64Array_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_GetAttributeU64Array_cfunc(
            vi, selector_string, attribute_id, attr_val, array_size, actual_array_size
        )

    def RFmxLTE_SetAttributeU64Array(self, vi, selector_string, attribute_id, attr_val, array_size):
        """RFmxLTE_SetAttributeU64Array."""
        with self._func_lock:
            if self.RFmxLTE_SetAttributeU64Array_cfunc is None:
                self.RFmxLTE_SetAttributeU64Array_cfunc = self._get_library_function(
                    "RFmxLTE_SetAttributeU64Array"
                )
                self.RFmxLTE_SetAttributeU64Array_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_uint64),
                    ctypes.c_uint32,
                ]
                self.RFmxLTE_SetAttributeU64Array_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_SetAttributeU64Array_cfunc(
            vi, selector_string, attribute_id, attr_val, array_size
        )

    def RFmxLTE_GetAttributeF32Array(
        self, vi, selector_string, attribute_id, attr_val, array_size, actual_array_size
    ):
        """RFmxLTE_GetAttributeF32Array."""
        with self._func_lock:
            if self.RFmxLTE_GetAttributeF32Array_cfunc is None:
                self.RFmxLTE_GetAttributeF32Array_cfunc = self._get_library_function(
                    "RFmxLTE_GetAttributeF32Array"
                )
                self.RFmxLTE_GetAttributeF32Array_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxLTE_GetAttributeF32Array_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_GetAttributeF32Array_cfunc(
            vi, selector_string, attribute_id, attr_val, array_size, actual_array_size
        )

    def RFmxLTE_SetAttributeF32Array(self, vi, selector_string, attribute_id, attr_val, array_size):
        """RFmxLTE_SetAttributeF32Array."""
        with self._func_lock:
            if self.RFmxLTE_SetAttributeF32Array_cfunc is None:
                self.RFmxLTE_SetAttributeF32Array_cfunc = self._get_library_function(
                    "RFmxLTE_SetAttributeF32Array"
                )
                self.RFmxLTE_SetAttributeF32Array_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_uint32,
                ]
                self.RFmxLTE_SetAttributeF32Array_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_SetAttributeF32Array_cfunc(
            vi, selector_string, attribute_id, attr_val, array_size
        )

    def RFmxLTE_GetAttributeF64Array(
        self, vi, selector_string, attribute_id, attr_val, array_size, actual_array_size
    ):
        """RFmxLTE_GetAttributeF64Array."""
        with self._func_lock:
            if self.RFmxLTE_GetAttributeF64Array_cfunc is None:
                self.RFmxLTE_GetAttributeF64Array_cfunc = self._get_library_function(
                    "RFmxLTE_GetAttributeF64Array"
                )
                self.RFmxLTE_GetAttributeF64Array_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxLTE_GetAttributeF64Array_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_GetAttributeF64Array_cfunc(
            vi, selector_string, attribute_id, attr_val, array_size, actual_array_size
        )

    def RFmxLTE_SetAttributeF64Array(self, vi, selector_string, attribute_id, attr_val, array_size):
        """RFmxLTE_SetAttributeF64Array."""
        with self._func_lock:
            if self.RFmxLTE_SetAttributeF64Array_cfunc is None:
                self.RFmxLTE_SetAttributeF64Array_cfunc = self._get_library_function(
                    "RFmxLTE_SetAttributeF64Array"
                )
                self.RFmxLTE_SetAttributeF64Array_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.c_uint32,
                ]
                self.RFmxLTE_SetAttributeF64Array_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_SetAttributeF64Array_cfunc(
            vi, selector_string, attribute_id, attr_val, array_size
        )

    def RFmxLTE_GetAttributeNIComplexSingleArray(
        self, vi, selector_string, attribute_id, attr_val, array_size, actual_array_size
    ):
        """RFmxLTE_GetAttributeNIComplexSingleArray."""
        with self._func_lock:
            if self.RFmxLTE_GetAttributeNIComplexSingleArray_cfunc is None:
                self.RFmxLTE_GetAttributeNIComplexSingleArray_cfunc = self._get_library_function(
                    "RFmxLTE_GetAttributeNIComplexSingleArray"
                )
                self.RFmxLTE_GetAttributeNIComplexSingleArray_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxLTE_GetAttributeNIComplexSingleArray_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_GetAttributeNIComplexSingleArray_cfunc(
            vi, selector_string, attribute_id, attr_val, array_size, actual_array_size
        )

    def RFmxLTE_SetAttributeNIComplexSingleArray(
        self, vi, selector_string, attribute_id, attr_val, array_size
    ):
        """RFmxLTE_SetAttributeNIComplexSingleArray."""
        with self._func_lock:
            if self.RFmxLTE_SetAttributeNIComplexSingleArray_cfunc is None:
                self.RFmxLTE_SetAttributeNIComplexSingleArray_cfunc = self._get_library_function(
                    "RFmxLTE_SetAttributeNIComplexSingleArray"
                )
                self.RFmxLTE_SetAttributeNIComplexSingleArray_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_uint32,
                ]
                self.RFmxLTE_SetAttributeNIComplexSingleArray_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_SetAttributeNIComplexSingleArray_cfunc(
            vi, selector_string, attribute_id, attr_val, array_size
        )

    def RFmxLTE_GetAttributeNIComplexDoubleArray(
        self, vi, selector_string, attribute_id, attr_val, array_size, actual_array_size
    ):
        """RFmxLTE_GetAttributeNIComplexDoubleArray."""
        with self._func_lock:
            if self.RFmxLTE_GetAttributeNIComplexDoubleArray_cfunc is None:
                self.RFmxLTE_GetAttributeNIComplexDoubleArray_cfunc = self._get_library_function(
                    "RFmxLTE_GetAttributeNIComplexDoubleArray"
                )
                self.RFmxLTE_GetAttributeNIComplexDoubleArray_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxLTE_GetAttributeNIComplexDoubleArray_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_GetAttributeNIComplexDoubleArray_cfunc(
            vi, selector_string, attribute_id, attr_val, array_size, actual_array_size
        )

    def RFmxLTE_SetAttributeNIComplexDoubleArray(
        self, vi, selector_string, attribute_id, attr_val, array_size
    ):
        """RFmxLTE_SetAttributeNIComplexDoubleArray."""
        with self._func_lock:
            if self.RFmxLTE_SetAttributeNIComplexDoubleArray_cfunc is None:
                self.RFmxLTE_SetAttributeNIComplexDoubleArray_cfunc = self._get_library_function(
                    "RFmxLTE_SetAttributeNIComplexDoubleArray"
                )
                self.RFmxLTE_SetAttributeNIComplexDoubleArray_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.c_uint32,
                ]
                self.RFmxLTE_SetAttributeNIComplexDoubleArray_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_SetAttributeNIComplexDoubleArray_cfunc(
            vi, selector_string, attribute_id, attr_val, array_size
        )

    def RFmxLTE_GetAttributeString(self, vi, selector_string, attribute_id, array_size, attr_val):
        """RFmxLTE_GetAttributeString."""
        with self._func_lock:
            if self.RFmxLTE_GetAttributeString_cfunc is None:
                self.RFmxLTE_GetAttributeString_cfunc = self._get_library_function(
                    "RFmxLTE_GetAttributeString"
                )
                self.RFmxLTE_GetAttributeString_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_char),
                ]
                self.RFmxLTE_GetAttributeString_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_GetAttributeString_cfunc(
            vi, selector_string, attribute_id, array_size, attr_val
        )

    def RFmxLTE_SetAttributeString(self, vi, selector_string, attribute_id, attr_val):
        """RFmxLTE_SetAttributeString."""
        with self._func_lock:
            if self.RFmxLTE_SetAttributeString_cfunc is None:
                self.RFmxLTE_SetAttributeString_cfunc = self._get_library_function(
                    "RFmxLTE_SetAttributeString"
                )
                self.RFmxLTE_SetAttributeString_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                ]
                self.RFmxLTE_SetAttributeString_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_SetAttributeString_cfunc(vi, selector_string, attribute_id, attr_val)

    def RFmxLTE_ACPValidateNoiseCalibrationData(
        self, vi, selector_string, noise_calibration_data_valid
    ):
        """RFmxLTE_ACPValidateNoiseCalibrationData."""
        with self._func_lock:
            if self.RFmxLTE_ACPValidateNoiseCalibrationData_cfunc is None:
                self.RFmxLTE_ACPValidateNoiseCalibrationData_cfunc = self._get_library_function(
                    "RFmxLTE_ACPValidateNoiseCalibrationData"
                )
                self.RFmxLTE_ACPValidateNoiseCalibrationData_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxLTE_ACPValidateNoiseCalibrationData_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ACPValidateNoiseCalibrationData_cfunc(
            vi, selector_string, noise_calibration_data_valid
        )

    def RFmxLTE_CHPValidateNoiseCalibrationData(
        self, vi, selector_string, noise_calibration_data_valid
    ):
        """RFmxLTE_CHPValidateNoiseCalibrationData."""
        with self._func_lock:
            if self.RFmxLTE_CHPValidateNoiseCalibrationData_cfunc is None:
                self.RFmxLTE_CHPValidateNoiseCalibrationData_cfunc = self._get_library_function(
                    "RFmxLTE_CHPValidateNoiseCalibrationData"
                )
                self.RFmxLTE_CHPValidateNoiseCalibrationData_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxLTE_CHPValidateNoiseCalibrationData_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_CHPValidateNoiseCalibrationData_cfunc(
            vi, selector_string, noise_calibration_data_valid
        )

    def RFmxLTE_AbortMeasurements(self, vi, selector_string):
        """RFmxLTE_AbortMeasurements."""
        with self._func_lock:
            if self.RFmxLTE_AbortMeasurements_cfunc is None:
                self.RFmxLTE_AbortMeasurements_cfunc = self._get_library_function(
                    "RFmxLTE_AbortMeasurements"
                )
                self.RFmxLTE_AbortMeasurements_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                ]
                self.RFmxLTE_AbortMeasurements_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_AbortMeasurements_cfunc(vi, selector_string)

    def RFmxLTE_AutoLevel(self, vi, selector_string, measurement_interval, reference_level):
        """RFmxLTE_AutoLevel."""
        with self._func_lock:
            if self.RFmxLTE_AutoLevel_cfunc is None:
                self.RFmxLTE_AutoLevel_cfunc = self._get_library_function("RFmxLTE_AutoLevel")
                self.RFmxLTE_AutoLevel_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxLTE_AutoLevel_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_AutoLevel_cfunc(
            vi, selector_string, measurement_interval, reference_level
        )

    def RFmxLTE_CheckMeasurementStatus(self, vi, selector_string, is_done):
        """RFmxLTE_CheckMeasurementStatus."""
        with self._func_lock:
            if self.RFmxLTE_CheckMeasurementStatus_cfunc is None:
                self.RFmxLTE_CheckMeasurementStatus_cfunc = self._get_library_function(
                    "RFmxLTE_CheckMeasurementStatus"
                )
                self.RFmxLTE_CheckMeasurementStatus_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxLTE_CheckMeasurementStatus_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_CheckMeasurementStatus_cfunc(vi, selector_string, is_done)

    def RFmxLTE_ClearAllNamedResults(self, vi, selector_string):
        """RFmxLTE_ClearAllNamedResults."""
        with self._func_lock:
            if self.RFmxLTE_ClearAllNamedResults_cfunc is None:
                self.RFmxLTE_ClearAllNamedResults_cfunc = self._get_library_function(
                    "RFmxLTE_ClearAllNamedResults"
                )
                self.RFmxLTE_ClearAllNamedResults_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                ]
                self.RFmxLTE_ClearAllNamedResults_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ClearAllNamedResults_cfunc(vi, selector_string)

    def RFmxLTE_ClearNamedResult(self, vi, selector_string):
        """RFmxLTE_ClearNamedResult."""
        with self._func_lock:
            if self.RFmxLTE_ClearNamedResult_cfunc is None:
                self.RFmxLTE_ClearNamedResult_cfunc = self._get_library_function(
                    "RFmxLTE_ClearNamedResult"
                )
                self.RFmxLTE_ClearNamedResult_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                ]
                self.RFmxLTE_ClearNamedResult_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ClearNamedResult_cfunc(vi, selector_string)

    def RFmxLTE_Commit(self, vi, selector_string):
        """RFmxLTE_Commit."""
        with self._func_lock:
            if self.RFmxLTE_Commit_cfunc is None:
                self.RFmxLTE_Commit_cfunc = self._get_library_function("RFmxLTE_Commit")
                self.RFmxLTE_Commit_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                ]
                self.RFmxLTE_Commit_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_Commit_cfunc(vi, selector_string)

    def RFmxLTE_CfgDigitalEdgeTrigger(
        self, vi, selector_string, digital_edge_source, digital_edge, trigger_delay, enable_trigger
    ):
        """RFmxLTE_CfgDigitalEdgeTrigger."""
        with self._func_lock:
            if self.RFmxLTE_CfgDigitalEdgeTrigger_cfunc is None:
                self.RFmxLTE_CfgDigitalEdgeTrigger_cfunc = self._get_library_function(
                    "RFmxLTE_CfgDigitalEdgeTrigger"
                )
                self.RFmxLTE_CfgDigitalEdgeTrigger_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                    ctypes.c_double,
                    ctypes.c_int32,
                ]
                self.RFmxLTE_CfgDigitalEdgeTrigger_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_CfgDigitalEdgeTrigger_cfunc(
            vi, selector_string, digital_edge_source, digital_edge, trigger_delay, enable_trigger
        )

    def RFmxLTE_CfgFrequencyEARFCN(self, vi, selector_string, link_direction, band, earfcn):
        """RFmxLTE_CfgFrequencyEARFCN."""
        with self._func_lock:
            if self.RFmxLTE_CfgFrequencyEARFCN_cfunc is None:
                self.RFmxLTE_CfgFrequencyEARFCN_cfunc = self._get_library_function(
                    "RFmxLTE_CfgFrequencyEARFCN"
                )
                self.RFmxLTE_CfgFrequencyEARFCN_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                    ctypes.c_int32,
                    ctypes.c_int32,
                ]
                self.RFmxLTE_CfgFrequencyEARFCN_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_CfgFrequencyEARFCN_cfunc(
            vi, selector_string, link_direction, band, earfcn
        )

    def RFmxLTE_CfgIQPowerEdgeTrigger(
        self,
        vi,
        selector_string,
        iq_power_edge_source,
        iq_power_edge_slope,
        iq_power_edge_level,
        trigger_delay,
        trigger_min_quiet_time_mode,
        trigger_min_quiet_time_duration,
        iq_power_edge_level_type,
        enable_trigger,
    ):
        """RFmxLTE_CfgIQPowerEdgeTrigger."""
        with self._func_lock:
            if self.RFmxLTE_CfgIQPowerEdgeTrigger_cfunc is None:
                self.RFmxLTE_CfgIQPowerEdgeTrigger_cfunc = self._get_library_function(
                    "RFmxLTE_CfgIQPowerEdgeTrigger"
                )
                self.RFmxLTE_CfgIQPowerEdgeTrigger_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                    ctypes.c_double,
                    ctypes.c_double,
                    ctypes.c_int32,
                    ctypes.c_double,
                    ctypes.c_int32,
                    ctypes.c_int32,
                ]
                self.RFmxLTE_CfgIQPowerEdgeTrigger_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_CfgIQPowerEdgeTrigger_cfunc(
            vi,
            selector_string,
            iq_power_edge_source,
            iq_power_edge_slope,
            iq_power_edge_level,
            trigger_delay,
            trigger_min_quiet_time_mode,
            trigger_min_quiet_time_duration,
            iq_power_edge_level_type,
            enable_trigger,
        )

    def RFmxLTE_CfgSoftwareEdgeTrigger(self, vi, selector_string, trigger_delay, enable_trigger):
        """RFmxLTE_CfgSoftwareEdgeTrigger."""
        with self._func_lock:
            if self.RFmxLTE_CfgSoftwareEdgeTrigger_cfunc is None:
                self.RFmxLTE_CfgSoftwareEdgeTrigger_cfunc = self._get_library_function(
                    "RFmxLTE_CfgSoftwareEdgeTrigger"
                )
                self.RFmxLTE_CfgSoftwareEdgeTrigger_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.c_int32,
                ]
                self.RFmxLTE_CfgSoftwareEdgeTrigger_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_CfgSoftwareEdgeTrigger_cfunc(
            vi, selector_string, trigger_delay, enable_trigger
        )

    def RFmxLTE_CreateListStep(self, vi, selector_string, created_step_index):
        """RFmxLTE_CreateListStep."""
        with self._func_lock:
            if self.RFmxLTE_CreateListStep_cfunc is None:
                self.RFmxLTE_CreateListStep_cfunc = self._get_library_function(
                    "RFmxLTE_CreateListStep"
                )
                self.RFmxLTE_CreateListStep_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxLTE_CreateListStep_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_CreateListStep_cfunc(vi, selector_string, created_step_index)

    def RFmxLTE_CreateList(self, vi, list_name):
        """RFmxLTE_CreateList."""
        with self._func_lock:
            if self.RFmxLTE_CreateList_cfunc is None:
                self.RFmxLTE_CreateList_cfunc = self._get_library_function("RFmxLTE_CreateList")
                self.RFmxLTE_CreateList_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                ]
                self.RFmxLTE_CreateList_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_CreateList_cfunc(vi, list_name)

    def RFmxLTE_CreateSignalConfiguration(self, vi, signal_name):
        """RFmxLTE_CreateSignalConfiguration."""
        with self._func_lock:
            if self.RFmxLTE_CreateSignalConfiguration_cfunc is None:
                self.RFmxLTE_CreateSignalConfiguration_cfunc = self._get_library_function(
                    "RFmxLTE_CreateSignalConfiguration"
                )
                self.RFmxLTE_CreateSignalConfiguration_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                ]
                self.RFmxLTE_CreateSignalConfiguration_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_CreateSignalConfiguration_cfunc(vi, signal_name)

    def RFmxLTE_DeleteList(self, vi, list_name):
        """RFmxLTE_DeleteList."""
        with self._func_lock:
            if self.RFmxLTE_DeleteList_cfunc is None:
                self.RFmxLTE_DeleteList_cfunc = self._get_library_function("RFmxLTE_DeleteList")
                self.RFmxLTE_DeleteList_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                ]
                self.RFmxLTE_DeleteList_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_DeleteList_cfunc(vi, list_name)

    def RFmxLTE_DisableTrigger(self, vi, selector_string):
        """RFmxLTE_DisableTrigger."""
        with self._func_lock:
            if self.RFmxLTE_DisableTrigger_cfunc is None:
                self.RFmxLTE_DisableTrigger_cfunc = self._get_library_function(
                    "RFmxLTE_DisableTrigger"
                )
                self.RFmxLTE_DisableTrigger_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                ]
                self.RFmxLTE_DisableTrigger_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_DisableTrigger_cfunc(vi, selector_string)

    def RFmxLTE_Initiate(self, vi, selector_string, result_name):
        """RFmxLTE_Initiate."""
        with self._func_lock:
            if self.RFmxLTE_Initiate_cfunc is None:
                self.RFmxLTE_Initiate_cfunc = self._get_library_function("RFmxLTE_Initiate")
                self.RFmxLTE_Initiate_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.POINTER(ctypes.c_char),
                ]
                self.RFmxLTE_Initiate_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_Initiate_cfunc(vi, selector_string, result_name)

    def RFmxLTE_ResetToDefault(self, vi, selector_string):
        """RFmxLTE_ResetToDefault."""
        with self._func_lock:
            if self.RFmxLTE_ResetToDefault_cfunc is None:
                self.RFmxLTE_ResetToDefault_cfunc = self._get_library_function(
                    "RFmxLTE_ResetToDefault"
                )
                self.RFmxLTE_ResetToDefault_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                ]
                self.RFmxLTE_ResetToDefault_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ResetToDefault_cfunc(vi, selector_string)

    def RFmxLTE_SelectMeasurements(self, vi, selector_string, measurements, enable_all_traces):
        """RFmxLTE_SelectMeasurements."""
        with self._func_lock:
            if self.RFmxLTE_SelectMeasurements_cfunc is None:
                self.RFmxLTE_SelectMeasurements_cfunc = self._get_library_function(
                    "RFmxLTE_SelectMeasurements"
                )
                self.RFmxLTE_SelectMeasurements_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.c_int32,
                ]
                self.RFmxLTE_SelectMeasurements_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_SelectMeasurements_cfunc(
            vi, selector_string, measurements, enable_all_traces
        )

    def RFmxLTE_WaitForMeasurementComplete(self, vi, selector_string, timeout):
        """RFmxLTE_WaitForMeasurementComplete."""
        with self._func_lock:
            if self.RFmxLTE_WaitForMeasurementComplete_cfunc is None:
                self.RFmxLTE_WaitForMeasurementComplete_cfunc = self._get_library_function(
                    "RFmxLTE_WaitForMeasurementComplete"
                )
                self.RFmxLTE_WaitForMeasurementComplete_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                ]
                self.RFmxLTE_WaitForMeasurementComplete_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_WaitForMeasurementComplete_cfunc(vi, selector_string, timeout)

    def RFmxLTE_ACPCfgAveraging(
        self, vi, selector_string, averaging_enabled, averaging_count, averaging_type
    ):
        """RFmxLTE_ACPCfgAveraging."""
        with self._func_lock:
            if self.RFmxLTE_ACPCfgAveraging_cfunc is None:
                self.RFmxLTE_ACPCfgAveraging_cfunc = self._get_library_function(
                    "RFmxLTE_ACPCfgAveraging"
                )
                self.RFmxLTE_ACPCfgAveraging_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                    ctypes.c_int32,
                    ctypes.c_int32,
                ]
                self.RFmxLTE_ACPCfgAveraging_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ACPCfgAveraging_cfunc(
            vi, selector_string, averaging_enabled, averaging_count, averaging_type
        )

    def RFmxLTE_ACPCfgConfigurableNumberOfOffsetsEnabled(
        self, vi, selector_string, configurable_number_of_offsets_enabled
    ):
        """RFmxLTE_ACPCfgConfigurableNumberOfOffsetsEnabled."""
        with self._func_lock:
            if self.RFmxLTE_ACPCfgConfigurableNumberOfOffsetsEnabled_cfunc is None:
                self.RFmxLTE_ACPCfgConfigurableNumberOfOffsetsEnabled_cfunc = (
                    self._get_library_function("RFmxLTE_ACPCfgConfigurableNumberOfOffsetsEnabled")
                )
                self.RFmxLTE_ACPCfgConfigurableNumberOfOffsetsEnabled_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                ]
                self.RFmxLTE_ACPCfgConfigurableNumberOfOffsetsEnabled_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ACPCfgConfigurableNumberOfOffsetsEnabled_cfunc(
            vi, selector_string, configurable_number_of_offsets_enabled
        )

    def RFmxLTE_ACPCfgMeasurementMethod(self, vi, selector_string, measurement_method):
        """RFmxLTE_ACPCfgMeasurementMethod."""
        with self._func_lock:
            if self.RFmxLTE_ACPCfgMeasurementMethod_cfunc is None:
                self.RFmxLTE_ACPCfgMeasurementMethod_cfunc = self._get_library_function(
                    "RFmxLTE_ACPCfgMeasurementMethod"
                )
                self.RFmxLTE_ACPCfgMeasurementMethod_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                ]
                self.RFmxLTE_ACPCfgMeasurementMethod_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ACPCfgMeasurementMethod_cfunc(vi, selector_string, measurement_method)

    def RFmxLTE_ACPCfgNoiseCompensationEnabled(
        self, vi, selector_string, noise_compensation_enabled
    ):
        """RFmxLTE_ACPCfgNoiseCompensationEnabled."""
        with self._func_lock:
            if self.RFmxLTE_ACPCfgNoiseCompensationEnabled_cfunc is None:
                self.RFmxLTE_ACPCfgNoiseCompensationEnabled_cfunc = self._get_library_function(
                    "RFmxLTE_ACPCfgNoiseCompensationEnabled"
                )
                self.RFmxLTE_ACPCfgNoiseCompensationEnabled_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                ]
                self.RFmxLTE_ACPCfgNoiseCompensationEnabled_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ACPCfgNoiseCompensationEnabled_cfunc(
            vi, selector_string, noise_compensation_enabled
        )

    def RFmxLTE_ACPCfgNumberOfEUTRAOffsets(self, vi, selector_string, number_of_eutra_offsets):
        """RFmxLTE_ACPCfgNumberOfEUTRAOffsets."""
        with self._func_lock:
            if self.RFmxLTE_ACPCfgNumberOfEUTRAOffsets_cfunc is None:
                self.RFmxLTE_ACPCfgNumberOfEUTRAOffsets_cfunc = self._get_library_function(
                    "RFmxLTE_ACPCfgNumberOfEUTRAOffsets"
                )
                self.RFmxLTE_ACPCfgNumberOfEUTRAOffsets_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                ]
                self.RFmxLTE_ACPCfgNumberOfEUTRAOffsets_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ACPCfgNumberOfEUTRAOffsets_cfunc(
            vi, selector_string, number_of_eutra_offsets
        )

    def RFmxLTE_ACPCfgNumberOfGSMOffsets(self, vi, selector_string, number_of_gsm_offsets):
        """RFmxLTE_ACPCfgNumberOfGSMOffsets."""
        with self._func_lock:
            if self.RFmxLTE_ACPCfgNumberOfGSMOffsets_cfunc is None:
                self.RFmxLTE_ACPCfgNumberOfGSMOffsets_cfunc = self._get_library_function(
                    "RFmxLTE_ACPCfgNumberOfGSMOffsets"
                )
                self.RFmxLTE_ACPCfgNumberOfGSMOffsets_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                ]
                self.RFmxLTE_ACPCfgNumberOfGSMOffsets_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ACPCfgNumberOfGSMOffsets_cfunc(
            vi, selector_string, number_of_gsm_offsets
        )

    def RFmxLTE_ACPCfgNumberOfUTRAOffsets(self, vi, selector_string, number_of_utra_offsets):
        """RFmxLTE_ACPCfgNumberOfUTRAOffsets."""
        with self._func_lock:
            if self.RFmxLTE_ACPCfgNumberOfUTRAOffsets_cfunc is None:
                self.RFmxLTE_ACPCfgNumberOfUTRAOffsets_cfunc = self._get_library_function(
                    "RFmxLTE_ACPCfgNumberOfUTRAOffsets"
                )
                self.RFmxLTE_ACPCfgNumberOfUTRAOffsets_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                ]
                self.RFmxLTE_ACPCfgNumberOfUTRAOffsets_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ACPCfgNumberOfUTRAOffsets_cfunc(
            vi, selector_string, number_of_utra_offsets
        )

    def RFmxLTE_ACPCfgRBWFilter(self, vi, selector_string, rbw_auto, rbw, rbw_filter_type):
        """RFmxLTE_ACPCfgRBWFilter."""
        with self._func_lock:
            if self.RFmxLTE_ACPCfgRBWFilter_cfunc is None:
                self.RFmxLTE_ACPCfgRBWFilter_cfunc = self._get_library_function(
                    "RFmxLTE_ACPCfgRBWFilter"
                )
                self.RFmxLTE_ACPCfgRBWFilter_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                    ctypes.c_double,
                    ctypes.c_int32,
                ]
                self.RFmxLTE_ACPCfgRBWFilter_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ACPCfgRBWFilter_cfunc(
            vi, selector_string, rbw_auto, rbw, rbw_filter_type
        )

    def RFmxLTE_ACPCfgSweepTime(self, vi, selector_string, sweep_time_auto, sweep_time_interval):
        """RFmxLTE_ACPCfgSweepTime."""
        with self._func_lock:
            if self.RFmxLTE_ACPCfgSweepTime_cfunc is None:
                self.RFmxLTE_ACPCfgSweepTime_cfunc = self._get_library_function(
                    "RFmxLTE_ACPCfgSweepTime"
                )
                self.RFmxLTE_ACPCfgSweepTime_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                    ctypes.c_double,
                ]
                self.RFmxLTE_ACPCfgSweepTime_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ACPCfgSweepTime_cfunc(
            vi, selector_string, sweep_time_auto, sweep_time_interval
        )

    def RFmxLTE_ACPCfgUTRAAndEUTRAOffsets(
        self, vi, selector_string, number_of_utra_offsets, number_of_eutra_offsets
    ):
        """RFmxLTE_ACPCfgUTRAAndEUTRAOffsets."""
        with self._func_lock:
            if self.RFmxLTE_ACPCfgUTRAAndEUTRAOffsets_cfunc is None:
                self.RFmxLTE_ACPCfgUTRAAndEUTRAOffsets_cfunc = self._get_library_function(
                    "RFmxLTE_ACPCfgUTRAAndEUTRAOffsets"
                )
                self.RFmxLTE_ACPCfgUTRAAndEUTRAOffsets_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                    ctypes.c_int32,
                ]
                self.RFmxLTE_ACPCfgUTRAAndEUTRAOffsets_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ACPCfgUTRAAndEUTRAOffsets_cfunc(
            vi, selector_string, number_of_utra_offsets, number_of_eutra_offsets
        )

    def RFmxLTE_ACPCfgPowerUnits(self, vi, selector_string, power_units):
        """RFmxLTE_ACPCfgPowerUnits."""
        with self._func_lock:
            if self.RFmxLTE_ACPCfgPowerUnits_cfunc is None:
                self.RFmxLTE_ACPCfgPowerUnits_cfunc = self._get_library_function(
                    "RFmxLTE_ACPCfgPowerUnits"
                )
                self.RFmxLTE_ACPCfgPowerUnits_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                ]
                self.RFmxLTE_ACPCfgPowerUnits_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ACPCfgPowerUnits_cfunc(vi, selector_string, power_units)

    def RFmxLTE_CHPCfgAveraging(
        self, vi, selector_string, averaging_enabled, averaging_count, averaging_type
    ):
        """RFmxLTE_CHPCfgAveraging."""
        with self._func_lock:
            if self.RFmxLTE_CHPCfgAveraging_cfunc is None:
                self.RFmxLTE_CHPCfgAveraging_cfunc = self._get_library_function(
                    "RFmxLTE_CHPCfgAveraging"
                )
                self.RFmxLTE_CHPCfgAveraging_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                    ctypes.c_int32,
                    ctypes.c_int32,
                ]
                self.RFmxLTE_CHPCfgAveraging_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_CHPCfgAveraging_cfunc(
            vi, selector_string, averaging_enabled, averaging_count, averaging_type
        )

    def RFmxLTE_CHPCfgIntegrationBandwidthType(
        self, vi, selector_string, integration_bandwidth_type
    ):
        """RFmxLTE_CHPCfgIntegrationBandwidthType."""
        with self._func_lock:
            if self.RFmxLTE_CHPCfgIntegrationBandwidthType_cfunc is None:
                self.RFmxLTE_CHPCfgIntegrationBandwidthType_cfunc = self._get_library_function(
                    "RFmxLTE_CHPCfgIntegrationBandwidthType"
                )
                self.RFmxLTE_CHPCfgIntegrationBandwidthType_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                ]
                self.RFmxLTE_CHPCfgIntegrationBandwidthType_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_CHPCfgIntegrationBandwidthType_cfunc(
            vi, selector_string, integration_bandwidth_type
        )

    def RFmxLTE_CHPCfgRBWFilter(self, vi, selector_string, rbw_auto, rbw, rbw_filter_type):
        """RFmxLTE_CHPCfgRBWFilter."""
        with self._func_lock:
            if self.RFmxLTE_CHPCfgRBWFilter_cfunc is None:
                self.RFmxLTE_CHPCfgRBWFilter_cfunc = self._get_library_function(
                    "RFmxLTE_CHPCfgRBWFilter"
                )
                self.RFmxLTE_CHPCfgRBWFilter_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                    ctypes.c_double,
                    ctypes.c_int32,
                ]
                self.RFmxLTE_CHPCfgRBWFilter_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_CHPCfgRBWFilter_cfunc(
            vi, selector_string, rbw_auto, rbw, rbw_filter_type
        )

    def RFmxLTE_CHPCfgSweepTime(self, vi, selector_string, sweep_time_auto, sweep_time_interval):
        """RFmxLTE_CHPCfgSweepTime."""
        with self._func_lock:
            if self.RFmxLTE_CHPCfgSweepTime_cfunc is None:
                self.RFmxLTE_CHPCfgSweepTime_cfunc = self._get_library_function(
                    "RFmxLTE_CHPCfgSweepTime"
                )
                self.RFmxLTE_CHPCfgSweepTime_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                    ctypes.c_double,
                ]
                self.RFmxLTE_CHPCfgSweepTime_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_CHPCfgSweepTime_cfunc(
            vi, selector_string, sweep_time_auto, sweep_time_interval
        )

    def RFmxLTE_ModAccCfgAveraging(self, vi, selector_string, averaging_enabled, averaging_count):
        """RFmxLTE_ModAccCfgAveraging."""
        with self._func_lock:
            if self.RFmxLTE_ModAccCfgAveraging_cfunc is None:
                self.RFmxLTE_ModAccCfgAveraging_cfunc = self._get_library_function(
                    "RFmxLTE_ModAccCfgAveraging"
                )
                self.RFmxLTE_ModAccCfgAveraging_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                    ctypes.c_int32,
                ]
                self.RFmxLTE_ModAccCfgAveraging_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ModAccCfgAveraging_cfunc(
            vi, selector_string, averaging_enabled, averaging_count
        )

    def RFmxLTE_ModAccCfgCommonClockSourceEnabled(
        self, vi, selector_string, common_clock_source_enabled
    ):
        """RFmxLTE_ModAccCfgCommonClockSourceEnabled."""
        with self._func_lock:
            if self.RFmxLTE_ModAccCfgCommonClockSourceEnabled_cfunc is None:
                self.RFmxLTE_ModAccCfgCommonClockSourceEnabled_cfunc = self._get_library_function(
                    "RFmxLTE_ModAccCfgCommonClockSourceEnabled"
                )
                self.RFmxLTE_ModAccCfgCommonClockSourceEnabled_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                ]
                self.RFmxLTE_ModAccCfgCommonClockSourceEnabled_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ModAccCfgCommonClockSourceEnabled_cfunc(
            vi, selector_string, common_clock_source_enabled
        )

    def RFmxLTE_ModAccCfgEVMUnit(self, vi, selector_string, evm_unit):
        """RFmxLTE_ModAccCfgEVMUnit."""
        with self._func_lock:
            if self.RFmxLTE_ModAccCfgEVMUnit_cfunc is None:
                self.RFmxLTE_ModAccCfgEVMUnit_cfunc = self._get_library_function(
                    "RFmxLTE_ModAccCfgEVMUnit"
                )
                self.RFmxLTE_ModAccCfgEVMUnit_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                ]
                self.RFmxLTE_ModAccCfgEVMUnit_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ModAccCfgEVMUnit_cfunc(vi, selector_string, evm_unit)

    def RFmxLTE_ModAccCfgFFTWindowOffset(self, vi, selector_string, fft_window_offset):
        """RFmxLTE_ModAccCfgFFTWindowOffset."""
        with self._func_lock:
            if self.RFmxLTE_ModAccCfgFFTWindowOffset_cfunc is None:
                self.RFmxLTE_ModAccCfgFFTWindowOffset_cfunc = self._get_library_function(
                    "RFmxLTE_ModAccCfgFFTWindowOffset"
                )
                self.RFmxLTE_ModAccCfgFFTWindowOffset_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                ]
                self.RFmxLTE_ModAccCfgFFTWindowOffset_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ModAccCfgFFTWindowOffset_cfunc(vi, selector_string, fft_window_offset)

    def RFmxLTE_ModAccCfgFFTWindowPosition(
        self, vi, selector_string, fft_window_type, fft_window_offset, fft_window_length
    ):
        """RFmxLTE_ModAccCfgFFTWindowPosition."""
        with self._func_lock:
            if self.RFmxLTE_ModAccCfgFFTWindowPosition_cfunc is None:
                self.RFmxLTE_ModAccCfgFFTWindowPosition_cfunc = self._get_library_function(
                    "RFmxLTE_ModAccCfgFFTWindowPosition"
                )
                self.RFmxLTE_ModAccCfgFFTWindowPosition_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                    ctypes.c_double,
                    ctypes.c_double,
                ]
                self.RFmxLTE_ModAccCfgFFTWindowPosition_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ModAccCfgFFTWindowPosition_cfunc(
            vi, selector_string, fft_window_type, fft_window_offset, fft_window_length
        )

    def RFmxLTE_ModAccCfgInBandEmissionMaskType(
        self, vi, selector_string, in_band_emission_mask_type
    ):
        """RFmxLTE_ModAccCfgInBandEmissionMaskType."""
        with self._func_lock:
            if self.RFmxLTE_ModAccCfgInBandEmissionMaskType_cfunc is None:
                self.RFmxLTE_ModAccCfgInBandEmissionMaskType_cfunc = self._get_library_function(
                    "RFmxLTE_ModAccCfgInBandEmissionMaskType"
                )
                self.RFmxLTE_ModAccCfgInBandEmissionMaskType_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                ]
                self.RFmxLTE_ModAccCfgInBandEmissionMaskType_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ModAccCfgInBandEmissionMaskType_cfunc(
            vi, selector_string, in_band_emission_mask_type
        )

    def RFmxLTE_ModAccCfgSynchronizationModeAndInterval(
        self, vi, selector_string, synchronization_mode, measurement_offset, measurement_length
    ):
        """RFmxLTE_ModAccCfgSynchronizationModeAndInterval."""
        with self._func_lock:
            if self.RFmxLTE_ModAccCfgSynchronizationModeAndInterval_cfunc is None:
                self.RFmxLTE_ModAccCfgSynchronizationModeAndInterval_cfunc = (
                    self._get_library_function("RFmxLTE_ModAccCfgSynchronizationModeAndInterval")
                )
                self.RFmxLTE_ModAccCfgSynchronizationModeAndInterval_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                    ctypes.c_int32,
                    ctypes.c_int32,
                ]
                self.RFmxLTE_ModAccCfgSynchronizationModeAndInterval_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ModAccCfgSynchronizationModeAndInterval_cfunc(
            vi, selector_string, synchronization_mode, measurement_offset, measurement_length
        )

    def RFmxLTE_OBWCfgAveraging(
        self, vi, selector_string, averaging_enabled, averaging_count, averaging_type
    ):
        """RFmxLTE_OBWCfgAveraging."""
        with self._func_lock:
            if self.RFmxLTE_OBWCfgAveraging_cfunc is None:
                self.RFmxLTE_OBWCfgAveraging_cfunc = self._get_library_function(
                    "RFmxLTE_OBWCfgAveraging"
                )
                self.RFmxLTE_OBWCfgAveraging_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                    ctypes.c_int32,
                    ctypes.c_int32,
                ]
                self.RFmxLTE_OBWCfgAveraging_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_OBWCfgAveraging_cfunc(
            vi, selector_string, averaging_enabled, averaging_count, averaging_type
        )

    def RFmxLTE_OBWCfgRBWFilter(self, vi, selector_string, rbw_auto, rbw, rbw_filter_type):
        """RFmxLTE_OBWCfgRBWFilter."""
        with self._func_lock:
            if self.RFmxLTE_OBWCfgRBWFilter_cfunc is None:
                self.RFmxLTE_OBWCfgRBWFilter_cfunc = self._get_library_function(
                    "RFmxLTE_OBWCfgRBWFilter"
                )
                self.RFmxLTE_OBWCfgRBWFilter_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                    ctypes.c_double,
                    ctypes.c_int32,
                ]
                self.RFmxLTE_OBWCfgRBWFilter_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_OBWCfgRBWFilter_cfunc(
            vi, selector_string, rbw_auto, rbw, rbw_filter_type
        )

    def RFmxLTE_OBWCfgSweepTime(self, vi, selector_string, sweep_time_auto, sweep_time_interval):
        """RFmxLTE_OBWCfgSweepTime."""
        with self._func_lock:
            if self.RFmxLTE_OBWCfgSweepTime_cfunc is None:
                self.RFmxLTE_OBWCfgSweepTime_cfunc = self._get_library_function(
                    "RFmxLTE_OBWCfgSweepTime"
                )
                self.RFmxLTE_OBWCfgSweepTime_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                    ctypes.c_double,
                ]
                self.RFmxLTE_OBWCfgSweepTime_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_OBWCfgSweepTime_cfunc(
            vi, selector_string, sweep_time_auto, sweep_time_interval
        )

    def RFmxLTE_SEMCfgAveraging(
        self, vi, selector_string, averaging_enabled, averaging_count, averaging_type
    ):
        """RFmxLTE_SEMCfgAveraging."""
        with self._func_lock:
            if self.RFmxLTE_SEMCfgAveraging_cfunc is None:
                self.RFmxLTE_SEMCfgAveraging_cfunc = self._get_library_function(
                    "RFmxLTE_SEMCfgAveraging"
                )
                self.RFmxLTE_SEMCfgAveraging_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                    ctypes.c_int32,
                    ctypes.c_int32,
                ]
                self.RFmxLTE_SEMCfgAveraging_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_SEMCfgAveraging_cfunc(
            vi, selector_string, averaging_enabled, averaging_count, averaging_type
        )

    def RFmxLTE_SEMCfgComponentCarrierMaximumOutputPowerArray(
        self, vi, selector_string, component_carrier_maximum_output_power, number_of_elements
    ):
        """RFmxLTE_SEMCfgComponentCarrierMaximumOutputPowerArray."""
        with self._func_lock:
            if self.RFmxLTE_SEMCfgComponentCarrierMaximumOutputPowerArray_cfunc is None:
                self.RFmxLTE_SEMCfgComponentCarrierMaximumOutputPowerArray_cfunc = (
                    self._get_library_function(
                        "RFmxLTE_SEMCfgComponentCarrierMaximumOutputPowerArray"
                    )
                )
                self.RFmxLTE_SEMCfgComponentCarrierMaximumOutputPowerArray_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.c_int32,
                ]
                self.RFmxLTE_SEMCfgComponentCarrierMaximumOutputPowerArray_cfunc.restype = (
                    ctypes.c_int32
                )
        return self.RFmxLTE_SEMCfgComponentCarrierMaximumOutputPowerArray_cfunc(
            vi, selector_string, component_carrier_maximum_output_power, number_of_elements
        )

    def RFmxLTE_SEMCfgComponentCarrierMaximumOutputPower(
        self, vi, selector_string, component_carrier_maximum_output_power
    ):
        """RFmxLTE_SEMCfgComponentCarrierMaximumOutputPower."""
        with self._func_lock:
            if self.RFmxLTE_SEMCfgComponentCarrierMaximumOutputPower_cfunc is None:
                self.RFmxLTE_SEMCfgComponentCarrierMaximumOutputPower_cfunc = (
                    self._get_library_function("RFmxLTE_SEMCfgComponentCarrierMaximumOutputPower")
                )
                self.RFmxLTE_SEMCfgComponentCarrierMaximumOutputPower_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                ]
                self.RFmxLTE_SEMCfgComponentCarrierMaximumOutputPower_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_SEMCfgComponentCarrierMaximumOutputPower_cfunc(
            vi, selector_string, component_carrier_maximum_output_power
        )

    def RFmxLTE_SEMCfgDownlinkMask(
        self, vi, selector_string, downlink_mask_type, delta_f_maximum, aggregated_maximum_power
    ):
        """RFmxLTE_SEMCfgDownlinkMask."""
        with self._func_lock:
            if self.RFmxLTE_SEMCfgDownlinkMask_cfunc is None:
                self.RFmxLTE_SEMCfgDownlinkMask_cfunc = self._get_library_function(
                    "RFmxLTE_SEMCfgDownlinkMask"
                )
                self.RFmxLTE_SEMCfgDownlinkMask_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                    ctypes.c_double,
                    ctypes.c_double,
                ]
                self.RFmxLTE_SEMCfgDownlinkMask_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_SEMCfgDownlinkMask_cfunc(
            vi, selector_string, downlink_mask_type, delta_f_maximum, aggregated_maximum_power
        )

    def RFmxLTE_SEMCfgNumberOfOffsets(self, vi, selector_string, number_of_offsets):
        """RFmxLTE_SEMCfgNumberOfOffsets."""
        with self._func_lock:
            if self.RFmxLTE_SEMCfgNumberOfOffsets_cfunc is None:
                self.RFmxLTE_SEMCfgNumberOfOffsets_cfunc = self._get_library_function(
                    "RFmxLTE_SEMCfgNumberOfOffsets"
                )
                self.RFmxLTE_SEMCfgNumberOfOffsets_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                ]
                self.RFmxLTE_SEMCfgNumberOfOffsets_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_SEMCfgNumberOfOffsets_cfunc(vi, selector_string, number_of_offsets)

    def RFmxLTE_SEMCfgOffsetAbsoluteLimitArray(
        self,
        vi,
        selector_string,
        offset_absolute_limit_start,
        offset_absolute_limit_stop,
        number_of_elements,
    ):
        """RFmxLTE_SEMCfgOffsetAbsoluteLimitArray."""
        with self._func_lock:
            if self.RFmxLTE_SEMCfgOffsetAbsoluteLimitArray_cfunc is None:
                self.RFmxLTE_SEMCfgOffsetAbsoluteLimitArray_cfunc = self._get_library_function(
                    "RFmxLTE_SEMCfgOffsetAbsoluteLimitArray"
                )
                self.RFmxLTE_SEMCfgOffsetAbsoluteLimitArray_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.c_int32,
                ]
                self.RFmxLTE_SEMCfgOffsetAbsoluteLimitArray_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_SEMCfgOffsetAbsoluteLimitArray_cfunc(
            vi,
            selector_string,
            offset_absolute_limit_start,
            offset_absolute_limit_stop,
            number_of_elements,
        )

    def RFmxLTE_SEMCfgOffsetAbsoluteLimit(
        self, vi, selector_string, offset_absolute_limit_start, offset_absolute_limit_stop
    ):
        """RFmxLTE_SEMCfgOffsetAbsoluteLimit."""
        with self._func_lock:
            if self.RFmxLTE_SEMCfgOffsetAbsoluteLimit_cfunc is None:
                self.RFmxLTE_SEMCfgOffsetAbsoluteLimit_cfunc = self._get_library_function(
                    "RFmxLTE_SEMCfgOffsetAbsoluteLimit"
                )
                self.RFmxLTE_SEMCfgOffsetAbsoluteLimit_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.c_double,
                ]
                self.RFmxLTE_SEMCfgOffsetAbsoluteLimit_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_SEMCfgOffsetAbsoluteLimit_cfunc(
            vi, selector_string, offset_absolute_limit_start, offset_absolute_limit_stop
        )

    def RFmxLTE_SEMCfgOffsetBandwidthIntegralArray(
        self, vi, selector_string, offset_bandwidth_integral, number_of_elements
    ):
        """RFmxLTE_SEMCfgOffsetBandwidthIntegralArray."""
        with self._func_lock:
            if self.RFmxLTE_SEMCfgOffsetBandwidthIntegralArray_cfunc is None:
                self.RFmxLTE_SEMCfgOffsetBandwidthIntegralArray_cfunc = self._get_library_function(
                    "RFmxLTE_SEMCfgOffsetBandwidthIntegralArray"
                )
                self.RFmxLTE_SEMCfgOffsetBandwidthIntegralArray_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.POINTER(ctypes.c_int32),
                    ctypes.c_int32,
                ]
                self.RFmxLTE_SEMCfgOffsetBandwidthIntegralArray_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_SEMCfgOffsetBandwidthIntegralArray_cfunc(
            vi, selector_string, offset_bandwidth_integral, number_of_elements
        )

    def RFmxLTE_SEMCfgOffsetBandwidthIntegral(self, vi, selector_string, offset_bandwidth_integral):
        """RFmxLTE_SEMCfgOffsetBandwidthIntegral."""
        with self._func_lock:
            if self.RFmxLTE_SEMCfgOffsetBandwidthIntegral_cfunc is None:
                self.RFmxLTE_SEMCfgOffsetBandwidthIntegral_cfunc = self._get_library_function(
                    "RFmxLTE_SEMCfgOffsetBandwidthIntegral"
                )
                self.RFmxLTE_SEMCfgOffsetBandwidthIntegral_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                ]
                self.RFmxLTE_SEMCfgOffsetBandwidthIntegral_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_SEMCfgOffsetBandwidthIntegral_cfunc(
            vi, selector_string, offset_bandwidth_integral
        )

    def RFmxLTE_SEMCfgOffsetFrequencyArray(
        self,
        vi,
        selector_string,
        offset_start_frequency,
        offset_stop_frequency,
        offset_sideband,
        number_of_elements,
    ):
        """RFmxLTE_SEMCfgOffsetFrequencyArray."""
        with self._func_lock:
            if self.RFmxLTE_SEMCfgOffsetFrequencyArray_cfunc is None:
                self.RFmxLTE_SEMCfgOffsetFrequencyArray_cfunc = self._get_library_function(
                    "RFmxLTE_SEMCfgOffsetFrequencyArray"
                )
                self.RFmxLTE_SEMCfgOffsetFrequencyArray_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_int32),
                    ctypes.c_int32,
                ]
                self.RFmxLTE_SEMCfgOffsetFrequencyArray_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_SEMCfgOffsetFrequencyArray_cfunc(
            vi,
            selector_string,
            offset_start_frequency,
            offset_stop_frequency,
            offset_sideband,
            number_of_elements,
        )

    def RFmxLTE_SEMCfgOffsetFrequency(
        self, vi, selector_string, offset_start_frequency, offset_stop_frequency, offset_sideband
    ):
        """RFmxLTE_SEMCfgOffsetFrequency."""
        with self._func_lock:
            if self.RFmxLTE_SEMCfgOffsetFrequency_cfunc is None:
                self.RFmxLTE_SEMCfgOffsetFrequency_cfunc = self._get_library_function(
                    "RFmxLTE_SEMCfgOffsetFrequency"
                )
                self.RFmxLTE_SEMCfgOffsetFrequency_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.c_double,
                    ctypes.c_int32,
                ]
                self.RFmxLTE_SEMCfgOffsetFrequency_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_SEMCfgOffsetFrequency_cfunc(
            vi, selector_string, offset_start_frequency, offset_stop_frequency, offset_sideband
        )

    def RFmxLTE_SEMCfgOffsetLimitFailMaskArray(
        self, vi, selector_string, limit_fail_mask, number_of_elements
    ):
        """RFmxLTE_SEMCfgOffsetLimitFailMaskArray."""
        with self._func_lock:
            if self.RFmxLTE_SEMCfgOffsetLimitFailMaskArray_cfunc is None:
                self.RFmxLTE_SEMCfgOffsetLimitFailMaskArray_cfunc = self._get_library_function(
                    "RFmxLTE_SEMCfgOffsetLimitFailMaskArray"
                )
                self.RFmxLTE_SEMCfgOffsetLimitFailMaskArray_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.POINTER(ctypes.c_int32),
                    ctypes.c_int32,
                ]
                self.RFmxLTE_SEMCfgOffsetLimitFailMaskArray_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_SEMCfgOffsetLimitFailMaskArray_cfunc(
            vi, selector_string, limit_fail_mask, number_of_elements
        )

    def RFmxLTE_SEMCfgOffsetLimitFailMask(self, vi, selector_string, limit_fail_mask):
        """RFmxLTE_SEMCfgOffsetLimitFailMask."""
        with self._func_lock:
            if self.RFmxLTE_SEMCfgOffsetLimitFailMask_cfunc is None:
                self.RFmxLTE_SEMCfgOffsetLimitFailMask_cfunc = self._get_library_function(
                    "RFmxLTE_SEMCfgOffsetLimitFailMask"
                )
                self.RFmxLTE_SEMCfgOffsetLimitFailMask_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                ]
                self.RFmxLTE_SEMCfgOffsetLimitFailMask_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_SEMCfgOffsetLimitFailMask_cfunc(vi, selector_string, limit_fail_mask)

    def RFmxLTE_SEMCfgOffsetRBWFilterArray(
        self, vi, selector_string, offset_rbw, offset_rbw_filter_type, number_of_elements
    ):
        """RFmxLTE_SEMCfgOffsetRBWFilterArray."""
        with self._func_lock:
            if self.RFmxLTE_SEMCfgOffsetRBWFilterArray_cfunc is None:
                self.RFmxLTE_SEMCfgOffsetRBWFilterArray_cfunc = self._get_library_function(
                    "RFmxLTE_SEMCfgOffsetRBWFilterArray"
                )
                self.RFmxLTE_SEMCfgOffsetRBWFilterArray_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_int32),
                    ctypes.c_int32,
                ]
                self.RFmxLTE_SEMCfgOffsetRBWFilterArray_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_SEMCfgOffsetRBWFilterArray_cfunc(
            vi, selector_string, offset_rbw, offset_rbw_filter_type, number_of_elements
        )

    def RFmxLTE_SEMCfgOffsetRBWFilter(
        self, vi, selector_string, offset_rbw, offset_rbw_filter_type
    ):
        """RFmxLTE_SEMCfgOffsetRBWFilter."""
        with self._func_lock:
            if self.RFmxLTE_SEMCfgOffsetRBWFilter_cfunc is None:
                self.RFmxLTE_SEMCfgOffsetRBWFilter_cfunc = self._get_library_function(
                    "RFmxLTE_SEMCfgOffsetRBWFilter"
                )
                self.RFmxLTE_SEMCfgOffsetRBWFilter_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.c_int32,
                ]
                self.RFmxLTE_SEMCfgOffsetRBWFilter_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_SEMCfgOffsetRBWFilter_cfunc(
            vi, selector_string, offset_rbw, offset_rbw_filter_type
        )

    def RFmxLTE_SEMCfgOffsetRelativeLimitArray(
        self, vi, selector_string, relative_limit_start, relative_limit_stop, number_of_elements
    ):
        """RFmxLTE_SEMCfgOffsetRelativeLimitArray."""
        with self._func_lock:
            if self.RFmxLTE_SEMCfgOffsetRelativeLimitArray_cfunc is None:
                self.RFmxLTE_SEMCfgOffsetRelativeLimitArray_cfunc = self._get_library_function(
                    "RFmxLTE_SEMCfgOffsetRelativeLimitArray"
                )
                self.RFmxLTE_SEMCfgOffsetRelativeLimitArray_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.c_int32,
                ]
                self.RFmxLTE_SEMCfgOffsetRelativeLimitArray_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_SEMCfgOffsetRelativeLimitArray_cfunc(
            vi, selector_string, relative_limit_start, relative_limit_stop, number_of_elements
        )

    def RFmxLTE_SEMCfgOffsetRelativeLimit(
        self, vi, selector_string, relative_limit_start, relative_limit_stop
    ):
        """RFmxLTE_SEMCfgOffsetRelativeLimit."""
        with self._func_lock:
            if self.RFmxLTE_SEMCfgOffsetRelativeLimit_cfunc is None:
                self.RFmxLTE_SEMCfgOffsetRelativeLimit_cfunc = self._get_library_function(
                    "RFmxLTE_SEMCfgOffsetRelativeLimit"
                )
                self.RFmxLTE_SEMCfgOffsetRelativeLimit_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.c_double,
                ]
                self.RFmxLTE_SEMCfgOffsetRelativeLimit_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_SEMCfgOffsetRelativeLimit_cfunc(
            vi, selector_string, relative_limit_start, relative_limit_stop
        )

    def RFmxLTE_SEMCfgSweepTime(self, vi, selector_string, sweep_time_auto, sweep_time_interval):
        """RFmxLTE_SEMCfgSweepTime."""
        with self._func_lock:
            if self.RFmxLTE_SEMCfgSweepTime_cfunc is None:
                self.RFmxLTE_SEMCfgSweepTime_cfunc = self._get_library_function(
                    "RFmxLTE_SEMCfgSweepTime"
                )
                self.RFmxLTE_SEMCfgSweepTime_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                    ctypes.c_double,
                ]
                self.RFmxLTE_SEMCfgSweepTime_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_SEMCfgSweepTime_cfunc(
            vi, selector_string, sweep_time_auto, sweep_time_interval
        )

    def RFmxLTE_SEMCfgUplinkMaskType(self, vi, selector_string, uplink_mask_type):
        """RFmxLTE_SEMCfgUplinkMaskType."""
        with self._func_lock:
            if self.RFmxLTE_SEMCfgUplinkMaskType_cfunc is None:
                self.RFmxLTE_SEMCfgUplinkMaskType_cfunc = self._get_library_function(
                    "RFmxLTE_SEMCfgUplinkMaskType"
                )
                self.RFmxLTE_SEMCfgUplinkMaskType_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                ]
                self.RFmxLTE_SEMCfgUplinkMaskType_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_SEMCfgUplinkMaskType_cfunc(vi, selector_string, uplink_mask_type)

    def RFmxLTE_PVTCfgAveraging(
        self, vi, selector_string, averaging_enabled, averaging_count, averaging_type
    ):
        """RFmxLTE_PVTCfgAveraging."""
        with self._func_lock:
            if self.RFmxLTE_PVTCfgAveraging_cfunc is None:
                self.RFmxLTE_PVTCfgAveraging_cfunc = self._get_library_function(
                    "RFmxLTE_PVTCfgAveraging"
                )
                self.RFmxLTE_PVTCfgAveraging_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                    ctypes.c_int32,
                    ctypes.c_int32,
                ]
                self.RFmxLTE_PVTCfgAveraging_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_PVTCfgAveraging_cfunc(
            vi, selector_string, averaging_enabled, averaging_count, averaging_type
        )

    def RFmxLTE_PVTCfgMeasurementMethod(self, vi, selector_string, measurement_method):
        """RFmxLTE_PVTCfgMeasurementMethod."""
        with self._func_lock:
            if self.RFmxLTE_PVTCfgMeasurementMethod_cfunc is None:
                self.RFmxLTE_PVTCfgMeasurementMethod_cfunc = self._get_library_function(
                    "RFmxLTE_PVTCfgMeasurementMethod"
                )
                self.RFmxLTE_PVTCfgMeasurementMethod_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                ]
                self.RFmxLTE_PVTCfgMeasurementMethod_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_PVTCfgMeasurementMethod_cfunc(vi, selector_string, measurement_method)

    def RFmxLTE_PVTCfgOFFPowerExclusionPeriods(
        self, vi, selector_string, off_power_exclusion_before, off_power_exclusion_after
    ):
        """RFmxLTE_PVTCfgOFFPowerExclusionPeriods."""
        with self._func_lock:
            if self.RFmxLTE_PVTCfgOFFPowerExclusionPeriods_cfunc is None:
                self.RFmxLTE_PVTCfgOFFPowerExclusionPeriods_cfunc = self._get_library_function(
                    "RFmxLTE_PVTCfgOFFPowerExclusionPeriods"
                )
                self.RFmxLTE_PVTCfgOFFPowerExclusionPeriods_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.c_double,
                ]
                self.RFmxLTE_PVTCfgOFFPowerExclusionPeriods_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_PVTCfgOFFPowerExclusionPeriods_cfunc(
            vi, selector_string, off_power_exclusion_before, off_power_exclusion_after
        )

    def RFmxLTE_SlotPhaseCfgSynchronizationModeAndInterval(
        self, vi, selector_string, synchronization_mode, measurement_offset, measurement_length
    ):
        """RFmxLTE_SlotPhaseCfgSynchronizationModeAndInterval."""
        with self._func_lock:
            if self.RFmxLTE_SlotPhaseCfgSynchronizationModeAndInterval_cfunc is None:
                self.RFmxLTE_SlotPhaseCfgSynchronizationModeAndInterval_cfunc = (
                    self._get_library_function("RFmxLTE_SlotPhaseCfgSynchronizationModeAndInterval")
                )
                self.RFmxLTE_SlotPhaseCfgSynchronizationModeAndInterval_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                    ctypes.c_int32,
                    ctypes.c_int32,
                ]
                self.RFmxLTE_SlotPhaseCfgSynchronizationModeAndInterval_cfunc.restype = (
                    ctypes.c_int32
                )
        return self.RFmxLTE_SlotPhaseCfgSynchronizationModeAndInterval_cfunc(
            vi, selector_string, synchronization_mode, measurement_offset, measurement_length
        )

    def RFmxLTE_SlotPowerCfgMeasurementInterval(
        self, vi, selector_string, measurement_offset, measurement_length
    ):
        """RFmxLTE_SlotPowerCfgMeasurementInterval."""
        with self._func_lock:
            if self.RFmxLTE_SlotPowerCfgMeasurementInterval_cfunc is None:
                self.RFmxLTE_SlotPowerCfgMeasurementInterval_cfunc = self._get_library_function(
                    "RFmxLTE_SlotPowerCfgMeasurementInterval"
                )
                self.RFmxLTE_SlotPowerCfgMeasurementInterval_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                    ctypes.c_int32,
                ]
                self.RFmxLTE_SlotPowerCfgMeasurementInterval_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_SlotPowerCfgMeasurementInterval_cfunc(
            vi, selector_string, measurement_offset, measurement_length
        )

    def RFmxLTE_TXPCfgAveraging(self, vi, selector_string, averaging_enabled, averaging_count):
        """RFmxLTE_TXPCfgAveraging."""
        with self._func_lock:
            if self.RFmxLTE_TXPCfgAveraging_cfunc is None:
                self.RFmxLTE_TXPCfgAveraging_cfunc = self._get_library_function(
                    "RFmxLTE_TXPCfgAveraging"
                )
                self.RFmxLTE_TXPCfgAveraging_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                    ctypes.c_int32,
                ]
                self.RFmxLTE_TXPCfgAveraging_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_TXPCfgAveraging_cfunc(
            vi, selector_string, averaging_enabled, averaging_count
        )

    def RFmxLTE_TXPCfgMeasurementOffsetAndInterval(
        self, vi, selector_string, measurement_offset, measurement_interval
    ):
        """RFmxLTE_TXPCfgMeasurementOffsetAndInterval."""
        with self._func_lock:
            if self.RFmxLTE_TXPCfgMeasurementOffsetAndInterval_cfunc is None:
                self.RFmxLTE_TXPCfgMeasurementOffsetAndInterval_cfunc = self._get_library_function(
                    "RFmxLTE_TXPCfgMeasurementOffsetAndInterval"
                )
                self.RFmxLTE_TXPCfgMeasurementOffsetAndInterval_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.c_double,
                ]
                self.RFmxLTE_TXPCfgMeasurementOffsetAndInterval_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_TXPCfgMeasurementOffsetAndInterval_cfunc(
            vi, selector_string, measurement_offset, measurement_interval
        )

    def RFmxLTE_CfgAutoDMRSDetectionEnabled(self, vi, selector_string, auto_dmrs_detection_enabled):
        """RFmxLTE_CfgAutoDMRSDetectionEnabled."""
        with self._func_lock:
            if self.RFmxLTE_CfgAutoDMRSDetectionEnabled_cfunc is None:
                self.RFmxLTE_CfgAutoDMRSDetectionEnabled_cfunc = self._get_library_function(
                    "RFmxLTE_CfgAutoDMRSDetectionEnabled"
                )
                self.RFmxLTE_CfgAutoDMRSDetectionEnabled_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                ]
                self.RFmxLTE_CfgAutoDMRSDetectionEnabled_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_CfgAutoDMRSDetectionEnabled_cfunc(
            vi, selector_string, auto_dmrs_detection_enabled
        )

    def RFmxLTE_CfgAutoNPUSCHChannelDetectionEnabled(
        self, vi, selector_string, auto_npusch_channel_detection_enabled
    ):
        """RFmxLTE_CfgAutoNPUSCHChannelDetectionEnabled."""
        with self._func_lock:
            if self.RFmxLTE_CfgAutoNPUSCHChannelDetectionEnabled_cfunc is None:
                self.RFmxLTE_CfgAutoNPUSCHChannelDetectionEnabled_cfunc = (
                    self._get_library_function("RFmxLTE_CfgAutoNPUSCHChannelDetectionEnabled")
                )
                self.RFmxLTE_CfgAutoNPUSCHChannelDetectionEnabled_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                ]
                self.RFmxLTE_CfgAutoNPUSCHChannelDetectionEnabled_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_CfgAutoNPUSCHChannelDetectionEnabled_cfunc(
            vi, selector_string, auto_npusch_channel_detection_enabled
        )

    def RFmxLTE_CfgAutoResourceBlockDetectionEnabled(
        self, vi, selector_string, auto_resource_block_detection_enabled
    ):
        """RFmxLTE_CfgAutoResourceBlockDetectionEnabled."""
        with self._func_lock:
            if self.RFmxLTE_CfgAutoResourceBlockDetectionEnabled_cfunc is None:
                self.RFmxLTE_CfgAutoResourceBlockDetectionEnabled_cfunc = (
                    self._get_library_function("RFmxLTE_CfgAutoResourceBlockDetectionEnabled")
                )
                self.RFmxLTE_CfgAutoResourceBlockDetectionEnabled_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                ]
                self.RFmxLTE_CfgAutoResourceBlockDetectionEnabled_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_CfgAutoResourceBlockDetectionEnabled_cfunc(
            vi, selector_string, auto_resource_block_detection_enabled
        )

    def RFmxLTE_CfgBand(self, vi, selector_string, band):
        """RFmxLTE_CfgBand."""
        with self._func_lock:
            if self.RFmxLTE_CfgBand_cfunc is None:
                self.RFmxLTE_CfgBand_cfunc = self._get_library_function("RFmxLTE_CfgBand")
                self.RFmxLTE_CfgBand_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                ]
                self.RFmxLTE_CfgBand_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_CfgBand_cfunc(vi, selector_string, band)

    def RFmxLTE_CfgCellSpecificRatio(self, vi, selector_string, cell_specific_ratio):
        """RFmxLTE_CfgCellSpecificRatio."""
        with self._func_lock:
            if self.RFmxLTE_CfgCellSpecificRatio_cfunc is None:
                self.RFmxLTE_CfgCellSpecificRatio_cfunc = self._get_library_function(
                    "RFmxLTE_CfgCellSpecificRatio"
                )
                self.RFmxLTE_CfgCellSpecificRatio_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                ]
                self.RFmxLTE_CfgCellSpecificRatio_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_CfgCellSpecificRatio_cfunc(vi, selector_string, cell_specific_ratio)

    def RFmxLTE_CfgComponentCarrierArray(
        self,
        vi,
        selector_string,
        component_carrier_bandwidth,
        component_carrier_frequency,
        cell_id,
        number_of_elements,
    ):
        """RFmxLTE_CfgComponentCarrierArray."""
        with self._func_lock:
            if self.RFmxLTE_CfgComponentCarrierArray_cfunc is None:
                self.RFmxLTE_CfgComponentCarrierArray_cfunc = self._get_library_function(
                    "RFmxLTE_CfgComponentCarrierArray"
                )
                self.RFmxLTE_CfgComponentCarrierArray_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_int32),
                    ctypes.c_int32,
                ]
                self.RFmxLTE_CfgComponentCarrierArray_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_CfgComponentCarrierArray_cfunc(
            vi,
            selector_string,
            component_carrier_bandwidth,
            component_carrier_frequency,
            cell_id,
            number_of_elements,
        )

    def RFmxLTE_CfgComponentCarrierSpacing(
        self,
        vi,
        selector_string,
        component_carrier_spacing_type,
        component_carrier_at_center_frequency,
    ):
        """RFmxLTE_CfgComponentCarrierSpacing."""
        with self._func_lock:
            if self.RFmxLTE_CfgComponentCarrierSpacing_cfunc is None:
                self.RFmxLTE_CfgComponentCarrierSpacing_cfunc = self._get_library_function(
                    "RFmxLTE_CfgComponentCarrierSpacing"
                )
                self.RFmxLTE_CfgComponentCarrierSpacing_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                    ctypes.c_int32,
                ]
                self.RFmxLTE_CfgComponentCarrierSpacing_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_CfgComponentCarrierSpacing_cfunc(
            vi,
            selector_string,
            component_carrier_spacing_type,
            component_carrier_at_center_frequency,
        )

    def RFmxLTE_CfgComponentCarrier(
        self, vi, selector_string, component_carrier_bandwidth, component_carrier_frequency, cell_id
    ):
        """RFmxLTE_CfgComponentCarrier."""
        with self._func_lock:
            if self.RFmxLTE_CfgComponentCarrier_cfunc is None:
                self.RFmxLTE_CfgComponentCarrier_cfunc = self._get_library_function(
                    "RFmxLTE_CfgComponentCarrier"
                )
                self.RFmxLTE_CfgComponentCarrier_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.c_double,
                    ctypes.c_int32,
                ]
                self.RFmxLTE_CfgComponentCarrier_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_CfgComponentCarrier_cfunc(
            vi, selector_string, component_carrier_bandwidth, component_carrier_frequency, cell_id
        )

    def RFmxLTE_CfgDownlinkAutoCellIDDetectionEnabled(
        self, vi, selector_string, auto_cell_id_detection_enabled
    ):
        """RFmxLTE_CfgDownlinkAutoCellIDDetectionEnabled."""
        with self._func_lock:
            if self.RFmxLTE_CfgDownlinkAutoCellIDDetectionEnabled_cfunc is None:
                self.RFmxLTE_CfgDownlinkAutoCellIDDetectionEnabled_cfunc = (
                    self._get_library_function("RFmxLTE_CfgDownlinkAutoCellIDDetectionEnabled")
                )
                self.RFmxLTE_CfgDownlinkAutoCellIDDetectionEnabled_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                ]
                self.RFmxLTE_CfgDownlinkAutoCellIDDetectionEnabled_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_CfgDownlinkAutoCellIDDetectionEnabled_cfunc(
            vi, selector_string, auto_cell_id_detection_enabled
        )

    def RFmxLTE_CfgDownlinkChannelConfigurationMode(
        self, vi, selector_string, channel_configuration_mode
    ):
        """RFmxLTE_CfgDownlinkChannelConfigurationMode."""
        with self._func_lock:
            if self.RFmxLTE_CfgDownlinkChannelConfigurationMode_cfunc is None:
                self.RFmxLTE_CfgDownlinkChannelConfigurationMode_cfunc = self._get_library_function(
                    "RFmxLTE_CfgDownlinkChannelConfigurationMode"
                )
                self.RFmxLTE_CfgDownlinkChannelConfigurationMode_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                ]
                self.RFmxLTE_CfgDownlinkChannelConfigurationMode_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_CfgDownlinkChannelConfigurationMode_cfunc(
            vi, selector_string, channel_configuration_mode
        )

    def RFmxLTE_CfgDownlinkNumberOfSubframes(self, vi, selector_string, number_of_subframes):
        """RFmxLTE_CfgDownlinkNumberOfSubframes."""
        with self._func_lock:
            if self.RFmxLTE_CfgDownlinkNumberOfSubframes_cfunc is None:
                self.RFmxLTE_CfgDownlinkNumberOfSubframes_cfunc = self._get_library_function(
                    "RFmxLTE_CfgDownlinkNumberOfSubframes"
                )
                self.RFmxLTE_CfgDownlinkNumberOfSubframes_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                ]
                self.RFmxLTE_CfgDownlinkNumberOfSubframes_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_CfgDownlinkNumberOfSubframes_cfunc(
            vi, selector_string, number_of_subframes
        )

    def RFmxLTE_CfgDownlinkSynchronizationSignal(self, vi, selector_string, pss_power, sss_power):
        """RFmxLTE_CfgDownlinkSynchronizationSignal."""
        with self._func_lock:
            if self.RFmxLTE_CfgDownlinkSynchronizationSignal_cfunc is None:
                self.RFmxLTE_CfgDownlinkSynchronizationSignal_cfunc = self._get_library_function(
                    "RFmxLTE_CfgDownlinkSynchronizationSignal"
                )
                self.RFmxLTE_CfgDownlinkSynchronizationSignal_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.c_double,
                ]
                self.RFmxLTE_CfgDownlinkSynchronizationSignal_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_CfgDownlinkSynchronizationSignal_cfunc(
            vi, selector_string, pss_power, sss_power
        )

    def RFmxLTE_CfgDownlinkTestModelArray(
        self, vi, selector_string, downlink_test_model, number_of_elements
    ):
        """RFmxLTE_CfgDownlinkTestModelArray."""
        with self._func_lock:
            if self.RFmxLTE_CfgDownlinkTestModelArray_cfunc is None:
                self.RFmxLTE_CfgDownlinkTestModelArray_cfunc = self._get_library_function(
                    "RFmxLTE_CfgDownlinkTestModelArray"
                )
                self.RFmxLTE_CfgDownlinkTestModelArray_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.POINTER(ctypes.c_int32),
                    ctypes.c_int32,
                ]
                self.RFmxLTE_CfgDownlinkTestModelArray_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_CfgDownlinkTestModelArray_cfunc(
            vi, selector_string, downlink_test_model, number_of_elements
        )

    def RFmxLTE_CfgDownlinkTestModel(self, vi, selector_string, downlink_test_model):
        """RFmxLTE_CfgDownlinkTestModel."""
        with self._func_lock:
            if self.RFmxLTE_CfgDownlinkTestModel_cfunc is None:
                self.RFmxLTE_CfgDownlinkTestModel_cfunc = self._get_library_function(
                    "RFmxLTE_CfgDownlinkTestModel"
                )
                self.RFmxLTE_CfgDownlinkTestModel_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                ]
                self.RFmxLTE_CfgDownlinkTestModel_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_CfgDownlinkTestModel_cfunc(vi, selector_string, downlink_test_model)

    def RFmxLTE_CfgDuplexScheme(
        self, vi, selector_string, duplex_scheme, uplink_downlink_configuration
    ):
        """RFmxLTE_CfgDuplexScheme."""
        with self._func_lock:
            if self.RFmxLTE_CfgDuplexScheme_cfunc is None:
                self.RFmxLTE_CfgDuplexScheme_cfunc = self._get_library_function(
                    "RFmxLTE_CfgDuplexScheme"
                )
                self.RFmxLTE_CfgDuplexScheme_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                    ctypes.c_int32,
                ]
                self.RFmxLTE_CfgDuplexScheme_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_CfgDuplexScheme_cfunc(
            vi, selector_string, duplex_scheme, uplink_downlink_configuration
        )

    def RFmxLTE_CfgEMTCAnalysisEnabled(self, vi, selector_string, emtc_analysis_enabled):
        """RFmxLTE_CfgEMTCAnalysisEnabled."""
        with self._func_lock:
            if self.RFmxLTE_CfgEMTCAnalysisEnabled_cfunc is None:
                self.RFmxLTE_CfgEMTCAnalysisEnabled_cfunc = self._get_library_function(
                    "RFmxLTE_CfgEMTCAnalysisEnabled"
                )
                self.RFmxLTE_CfgEMTCAnalysisEnabled_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                ]
                self.RFmxLTE_CfgEMTCAnalysisEnabled_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_CfgEMTCAnalysisEnabled_cfunc(vi, selector_string, emtc_analysis_enabled)

    def RFmxLTE_CfgeNodeBCategory(self, vi, selector_string, enodeb_category):
        """RFmxLTE_CfgeNodeBCategory."""
        with self._func_lock:
            if self.RFmxLTE_CfgeNodeBCategory_cfunc is None:
                self.RFmxLTE_CfgeNodeBCategory_cfunc = self._get_library_function(
                    "RFmxLTE_CfgeNodeBCategory"
                )
                self.RFmxLTE_CfgeNodeBCategory_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                ]
                self.RFmxLTE_CfgeNodeBCategory_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_CfgeNodeBCategory_cfunc(vi, selector_string, enodeb_category)

    def RFmxLTE_CfgExternalAttenuation(self, vi, selector_string, external_attenuation):
        """RFmxLTE_CfgExternalAttenuation."""
        with self._func_lock:
            if self.RFmxLTE_CfgExternalAttenuation_cfunc is None:
                self.RFmxLTE_CfgExternalAttenuation_cfunc = self._get_library_function(
                    "RFmxLTE_CfgExternalAttenuation"
                )
                self.RFmxLTE_CfgExternalAttenuation_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                ]
                self.RFmxLTE_CfgExternalAttenuation_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_CfgExternalAttenuation_cfunc(vi, selector_string, external_attenuation)

    def RFmxLTE_CfgFrequency(self, vi, selector_string, center_frequency):
        """RFmxLTE_CfgFrequency."""
        with self._func_lock:
            if self.RFmxLTE_CfgFrequency_cfunc is None:
                self.RFmxLTE_CfgFrequency_cfunc = self._get_library_function("RFmxLTE_CfgFrequency")
                self.RFmxLTE_CfgFrequency_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                ]
                self.RFmxLTE_CfgFrequency_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_CfgFrequency_cfunc(vi, selector_string, center_frequency)

    def RFmxLTE_CfgLinkDirection(self, vi, selector_string, link_direction):
        """RFmxLTE_CfgLinkDirection."""
        with self._func_lock:
            if self.RFmxLTE_CfgLinkDirection_cfunc is None:
                self.RFmxLTE_CfgLinkDirection_cfunc = self._get_library_function(
                    "RFmxLTE_CfgLinkDirection"
                )
                self.RFmxLTE_CfgLinkDirection_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                ]
                self.RFmxLTE_CfgLinkDirection_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_CfgLinkDirection_cfunc(vi, selector_string, link_direction)

    def RFmxLTE_CfgNBIoTComponentCarrier(
        self, vi, selector_string, n_cell_id, uplink_subcarrier_spacing
    ):
        """RFmxLTE_CfgNBIoTComponentCarrier."""
        with self._func_lock:
            if self.RFmxLTE_CfgNBIoTComponentCarrier_cfunc is None:
                self.RFmxLTE_CfgNBIoTComponentCarrier_cfunc = self._get_library_function(
                    "RFmxLTE_CfgNBIoTComponentCarrier"
                )
                self.RFmxLTE_CfgNBIoTComponentCarrier_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                    ctypes.c_int32,
                ]
                self.RFmxLTE_CfgNBIoTComponentCarrier_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_CfgNBIoTComponentCarrier_cfunc(
            vi, selector_string, n_cell_id, uplink_subcarrier_spacing
        )

    def RFmxLTE_CfgNPUSCHDMRS(
        self,
        vi,
        selector_string,
        npusch_dmrs_base_sequence_mode,
        npusch_dmrs_base_sequence_index,
        npusch_dmrs_cyclic_shift,
        npusch_dmrs_group_hopping_enabled,
        npusch_dmrs_delta_ss,
    ):
        """RFmxLTE_CfgNPUSCHDMRS."""
        with self._func_lock:
            if self.RFmxLTE_CfgNPUSCHDMRS_cfunc is None:
                self.RFmxLTE_CfgNPUSCHDMRS_cfunc = self._get_library_function(
                    "RFmxLTE_CfgNPUSCHDMRS"
                )
                self.RFmxLTE_CfgNPUSCHDMRS_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                    ctypes.c_int32,
                    ctypes.c_int32,
                    ctypes.c_int32,
                    ctypes.c_int32,
                ]
                self.RFmxLTE_CfgNPUSCHDMRS_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_CfgNPUSCHDMRS_cfunc(
            vi,
            selector_string,
            npusch_dmrs_base_sequence_mode,
            npusch_dmrs_base_sequence_index,
            npusch_dmrs_cyclic_shift,
            npusch_dmrs_group_hopping_enabled,
            npusch_dmrs_delta_ss,
        )

    def RFmxLTE_CfgNPUSCHFormat(self, vi, selector_string, format):
        """RFmxLTE_CfgNPUSCHFormat."""
        with self._func_lock:
            if self.RFmxLTE_CfgNPUSCHFormat_cfunc is None:
                self.RFmxLTE_CfgNPUSCHFormat_cfunc = self._get_library_function(
                    "RFmxLTE_CfgNPUSCHFormat"
                )
                self.RFmxLTE_CfgNPUSCHFormat_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                ]
                self.RFmxLTE_CfgNPUSCHFormat_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_CfgNPUSCHFormat_cfunc(vi, selector_string, format)

    def RFmxLTE_CfgNPUSCHStartingSlot(self, vi, selector_string, starting_slot):
        """RFmxLTE_CfgNPUSCHStartingSlot."""
        with self._func_lock:
            if self.RFmxLTE_CfgNPUSCHStartingSlot_cfunc is None:
                self.RFmxLTE_CfgNPUSCHStartingSlot_cfunc = self._get_library_function(
                    "RFmxLTE_CfgNPUSCHStartingSlot"
                )
                self.RFmxLTE_CfgNPUSCHStartingSlot_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                ]
                self.RFmxLTE_CfgNPUSCHStartingSlot_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_CfgNPUSCHStartingSlot_cfunc(vi, selector_string, starting_slot)

    def RFmxLTE_CfgNPUSCHTones(
        self, vi, selector_string, tone_offset, number_of_tones, modulation_type
    ):
        """RFmxLTE_CfgNPUSCHTones."""
        with self._func_lock:
            if self.RFmxLTE_CfgNPUSCHTones_cfunc is None:
                self.RFmxLTE_CfgNPUSCHTones_cfunc = self._get_library_function(
                    "RFmxLTE_CfgNPUSCHTones"
                )
                self.RFmxLTE_CfgNPUSCHTones_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                    ctypes.c_int32,
                    ctypes.c_int32,
                ]
                self.RFmxLTE_CfgNPUSCHTones_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_CfgNPUSCHTones_cfunc(
            vi, selector_string, tone_offset, number_of_tones, modulation_type
        )

    def RFmxLTE_CfgNumberOfComponentCarriers(
        self, vi, selector_string, number_of_component_carriers
    ):
        """RFmxLTE_CfgNumberOfComponentCarriers."""
        with self._func_lock:
            if self.RFmxLTE_CfgNumberOfComponentCarriers_cfunc is None:
                self.RFmxLTE_CfgNumberOfComponentCarriers_cfunc = self._get_library_function(
                    "RFmxLTE_CfgNumberOfComponentCarriers"
                )
                self.RFmxLTE_CfgNumberOfComponentCarriers_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                ]
                self.RFmxLTE_CfgNumberOfComponentCarriers_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_CfgNumberOfComponentCarriers_cfunc(
            vi, selector_string, number_of_component_carriers
        )

    def RFmxLTE_CfgNumberOfDUTAntennas(self, vi, selector_string, number_of_dut_antennas):
        """RFmxLTE_CfgNumberOfDUTAntennas."""
        with self._func_lock:
            if self.RFmxLTE_CfgNumberOfDUTAntennas_cfunc is None:
                self.RFmxLTE_CfgNumberOfDUTAntennas_cfunc = self._get_library_function(
                    "RFmxLTE_CfgNumberOfDUTAntennas"
                )
                self.RFmxLTE_CfgNumberOfDUTAntennas_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                ]
                self.RFmxLTE_CfgNumberOfDUTAntennas_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_CfgNumberOfDUTAntennas_cfunc(
            vi, selector_string, number_of_dut_antennas
        )

    def RFmxLTE_CfgNumberOfPDSCHChannels(self, vi, selector_string, number_of_pdsch_channels):
        """RFmxLTE_CfgNumberOfPDSCHChannels."""
        with self._func_lock:
            if self.RFmxLTE_CfgNumberOfPDSCHChannels_cfunc is None:
                self.RFmxLTE_CfgNumberOfPDSCHChannels_cfunc = self._get_library_function(
                    "RFmxLTE_CfgNumberOfPDSCHChannels"
                )
                self.RFmxLTE_CfgNumberOfPDSCHChannels_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                ]
                self.RFmxLTE_CfgNumberOfPDSCHChannels_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_CfgNumberOfPDSCHChannels_cfunc(
            vi, selector_string, number_of_pdsch_channels
        )

    def RFmxLTE_CfgNumberOfPUSCHResourceBlockClusters(
        self, vi, selector_string, number_of_resource_block_clusters
    ):
        """RFmxLTE_CfgNumberOfPUSCHResourceBlockClusters."""
        with self._func_lock:
            if self.RFmxLTE_CfgNumberOfPUSCHResourceBlockClusters_cfunc is None:
                self.RFmxLTE_CfgNumberOfPUSCHResourceBlockClusters_cfunc = (
                    self._get_library_function("RFmxLTE_CfgNumberOfPUSCHResourceBlockClusters")
                )
                self.RFmxLTE_CfgNumberOfPUSCHResourceBlockClusters_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                ]
                self.RFmxLTE_CfgNumberOfPUSCHResourceBlockClusters_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_CfgNumberOfPUSCHResourceBlockClusters_cfunc(
            vi, selector_string, number_of_resource_block_clusters
        )

    def RFmxLTE_CfgNumberOfSubblocks(self, vi, selector_string, number_of_subblocks):
        """RFmxLTE_CfgNumberOfSubblocks."""
        with self._func_lock:
            if self.RFmxLTE_CfgNumberOfSubblocks_cfunc is None:
                self.RFmxLTE_CfgNumberOfSubblocks_cfunc = self._get_library_function(
                    "RFmxLTE_CfgNumberOfSubblocks"
                )
                self.RFmxLTE_CfgNumberOfSubblocks_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                ]
                self.RFmxLTE_CfgNumberOfSubblocks_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_CfgNumberOfSubblocks_cfunc(vi, selector_string, number_of_subblocks)

    def RFmxLTE_CfgPBCH(self, vi, selector_string, pbch_power):
        """RFmxLTE_CfgPBCH."""
        with self._func_lock:
            if self.RFmxLTE_CfgPBCH_cfunc is None:
                self.RFmxLTE_CfgPBCH_cfunc = self._get_library_function("RFmxLTE_CfgPBCH")
                self.RFmxLTE_CfgPBCH_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                ]
                self.RFmxLTE_CfgPBCH_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_CfgPBCH_cfunc(vi, selector_string, pbch_power)

    def RFmxLTE_CfgPCFICH(self, vi, selector_string, cfi, power):
        """RFmxLTE_CfgPCFICH."""
        with self._func_lock:
            if self.RFmxLTE_CfgPCFICH_cfunc is None:
                self.RFmxLTE_CfgPCFICH_cfunc = self._get_library_function("RFmxLTE_CfgPCFICH")
                self.RFmxLTE_CfgPCFICH_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                    ctypes.c_double,
                ]
                self.RFmxLTE_CfgPCFICH_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_CfgPCFICH_cfunc(vi, selector_string, cfi, power)

    def RFmxLTE_CfgPDCCH(self, vi, selector_string, pdcch_power):
        """RFmxLTE_CfgPDCCH."""
        with self._func_lock:
            if self.RFmxLTE_CfgPDCCH_cfunc is None:
                self.RFmxLTE_CfgPDCCH_cfunc = self._get_library_function("RFmxLTE_CfgPDCCH")
                self.RFmxLTE_CfgPDCCH_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                ]
                self.RFmxLTE_CfgPDCCH_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_CfgPDCCH_cfunc(vi, selector_string, pdcch_power)

    def RFmxLTE_CfgPDSCH(
        self, vi, selector_string, cw0_modulation_type, resource_block_allocation, power
    ):
        """RFmxLTE_CfgPDSCH."""
        with self._func_lock:
            if self.RFmxLTE_CfgPDSCH_cfunc is None:
                self.RFmxLTE_CfgPDSCH_cfunc = self._get_library_function("RFmxLTE_CfgPDSCH")
                self.RFmxLTE_CfgPDSCH_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                ]
                self.RFmxLTE_CfgPDSCH_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_CfgPDSCH_cfunc(
            vi, selector_string, cw0_modulation_type, resource_block_allocation, power
        )

    def RFmxLTE_CfgPHICH(self, vi, selector_string, resource, duration, power):
        """RFmxLTE_CfgPHICH."""
        with self._func_lock:
            if self.RFmxLTE_CfgPHICH_cfunc is None:
                self.RFmxLTE_CfgPHICH_cfunc = self._get_library_function("RFmxLTE_CfgPHICH")
                self.RFmxLTE_CfgPHICH_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                    ctypes.c_int32,
                    ctypes.c_double,
                ]
                self.RFmxLTE_CfgPHICH_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_CfgPHICH_cfunc(vi, selector_string, resource, duration, power)

    def RFmxLTE_CfgPSSCHModulationType(self, vi, selector_string, modulation_type):
        """RFmxLTE_CfgPSSCHModulationType."""
        with self._func_lock:
            if self.RFmxLTE_CfgPSSCHModulationType_cfunc is None:
                self.RFmxLTE_CfgPSSCHModulationType_cfunc = self._get_library_function(
                    "RFmxLTE_CfgPSSCHModulationType"
                )
                self.RFmxLTE_CfgPSSCHModulationType_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                ]
                self.RFmxLTE_CfgPSSCHModulationType_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_CfgPSSCHModulationType_cfunc(vi, selector_string, modulation_type)

    def RFmxLTE_CfgPSSCHResourceBlocks(
        self, vi, selector_string, resource_block_offset, number_of_resource_blocks
    ):
        """RFmxLTE_CfgPSSCHResourceBlocks."""
        with self._func_lock:
            if self.RFmxLTE_CfgPSSCHResourceBlocks_cfunc is None:
                self.RFmxLTE_CfgPSSCHResourceBlocks_cfunc = self._get_library_function(
                    "RFmxLTE_CfgPSSCHResourceBlocks"
                )
                self.RFmxLTE_CfgPSSCHResourceBlocks_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                    ctypes.c_int32,
                ]
                self.RFmxLTE_CfgPSSCHResourceBlocks_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_CfgPSSCHResourceBlocks_cfunc(
            vi, selector_string, resource_block_offset, number_of_resource_blocks
        )

    def RFmxLTE_CfgPUSCHModulationType(self, vi, selector_string, modulation_type):
        """RFmxLTE_CfgPUSCHModulationType."""
        with self._func_lock:
            if self.RFmxLTE_CfgPUSCHModulationType_cfunc is None:
                self.RFmxLTE_CfgPUSCHModulationType_cfunc = self._get_library_function(
                    "RFmxLTE_CfgPUSCHModulationType"
                )
                self.RFmxLTE_CfgPUSCHModulationType_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                ]
                self.RFmxLTE_CfgPUSCHModulationType_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_CfgPUSCHModulationType_cfunc(vi, selector_string, modulation_type)

    def RFmxLTE_CfgPUSCHResourceBlocks(
        self, vi, selector_string, resource_block_offset, number_of_resource_blocks
    ):
        """RFmxLTE_CfgPUSCHResourceBlocks."""
        with self._func_lock:
            if self.RFmxLTE_CfgPUSCHResourceBlocks_cfunc is None:
                self.RFmxLTE_CfgPUSCHResourceBlocks_cfunc = self._get_library_function(
                    "RFmxLTE_CfgPUSCHResourceBlocks"
                )
                self.RFmxLTE_CfgPUSCHResourceBlocks_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                    ctypes.c_int32,
                ]
                self.RFmxLTE_CfgPUSCHResourceBlocks_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_CfgPUSCHResourceBlocks_cfunc(
            vi, selector_string, resource_block_offset, number_of_resource_blocks
        )

    def RFmxLTE_CfgReferenceLevel(self, vi, selector_string, reference_level):
        """RFmxLTE_CfgReferenceLevel."""
        with self._func_lock:
            if self.RFmxLTE_CfgReferenceLevel_cfunc is None:
                self.RFmxLTE_CfgReferenceLevel_cfunc = self._get_library_function(
                    "RFmxLTE_CfgReferenceLevel"
                )
                self.RFmxLTE_CfgReferenceLevel_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                ]
                self.RFmxLTE_CfgReferenceLevel_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_CfgReferenceLevel_cfunc(vi, selector_string, reference_level)

    def RFmxLTE_CfgRF(
        self, vi, selector_string, center_frequency, reference_level, external_attenuation
    ):
        """RFmxLTE_CfgRF."""
        with self._func_lock:
            if self.RFmxLTE_CfgRF_cfunc is None:
                self.RFmxLTE_CfgRF_cfunc = self._get_library_function("RFmxLTE_CfgRF")
                self.RFmxLTE_CfgRF_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.c_double,
                    ctypes.c_double,
                ]
                self.RFmxLTE_CfgRF_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_CfgRF_cfunc(
            vi, selector_string, center_frequency, reference_level, external_attenuation
        )

    def RFmxLTE_CfgTransmitAntennaToAnalyze(self, vi, selector_string, transmit_antenna_to_analyze):
        """RFmxLTE_CfgTransmitAntennaToAnalyze."""
        with self._func_lock:
            if self.RFmxLTE_CfgTransmitAntennaToAnalyze_cfunc is None:
                self.RFmxLTE_CfgTransmitAntennaToAnalyze_cfunc = self._get_library_function(
                    "RFmxLTE_CfgTransmitAntennaToAnalyze"
                )
                self.RFmxLTE_CfgTransmitAntennaToAnalyze_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                ]
                self.RFmxLTE_CfgTransmitAntennaToAnalyze_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_CfgTransmitAntennaToAnalyze_cfunc(
            vi, selector_string, transmit_antenna_to_analyze
        )

    def RFmxLTE_ACPFetchComponentCarrierMeasurement(
        self, vi, selector_string, timeout, absolute_power, relative_power
    ):
        """RFmxLTE_ACPFetchComponentCarrierMeasurement."""
        with self._func_lock:
            if self.RFmxLTE_ACPFetchComponentCarrierMeasurement_cfunc is None:
                self.RFmxLTE_ACPFetchComponentCarrierMeasurement_cfunc = self._get_library_function(
                    "RFmxLTE_ACPFetchComponentCarrierMeasurement"
                )
                self.RFmxLTE_ACPFetchComponentCarrierMeasurement_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxLTE_ACPFetchComponentCarrierMeasurement_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ACPFetchComponentCarrierMeasurement_cfunc(
            vi, selector_string, timeout, absolute_power, relative_power
        )

    def RFmxLTE_ACPFetchOffsetMeasurement(
        self,
        vi,
        selector_string,
        timeout,
        lower_relative_power,
        upper_relative_power,
        lower_absolute_power,
        upper_absolute_power,
    ):
        """RFmxLTE_ACPFetchOffsetMeasurement."""
        with self._func_lock:
            if self.RFmxLTE_ACPFetchOffsetMeasurement_cfunc is None:
                self.RFmxLTE_ACPFetchOffsetMeasurement_cfunc = self._get_library_function(
                    "RFmxLTE_ACPFetchOffsetMeasurement"
                )
                self.RFmxLTE_ACPFetchOffsetMeasurement_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxLTE_ACPFetchOffsetMeasurement_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ACPFetchOffsetMeasurement_cfunc(
            vi,
            selector_string,
            timeout,
            lower_relative_power,
            upper_relative_power,
            lower_absolute_power,
            upper_absolute_power,
        )

    def RFmxLTE_ACPFetchSubblockMeasurement(
        self, vi, selector_string, timeout, subblock_power, integration_bandwidth, frequency
    ):
        """RFmxLTE_ACPFetchSubblockMeasurement."""
        with self._func_lock:
            if self.RFmxLTE_ACPFetchSubblockMeasurement_cfunc is None:
                self.RFmxLTE_ACPFetchSubblockMeasurement_cfunc = self._get_library_function(
                    "RFmxLTE_ACPFetchSubblockMeasurement"
                )
                self.RFmxLTE_ACPFetchSubblockMeasurement_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxLTE_ACPFetchSubblockMeasurement_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ACPFetchSubblockMeasurement_cfunc(
            vi, selector_string, timeout, subblock_power, integration_bandwidth, frequency
        )

    def RFmxLTE_ACPFetchTotalAggregatedPower(
        self, vi, selector_string, timeout, total_aggregated_power
    ):
        """RFmxLTE_ACPFetchTotalAggregatedPower."""
        with self._func_lock:
            if self.RFmxLTE_ACPFetchTotalAggregatedPower_cfunc is None:
                self.RFmxLTE_ACPFetchTotalAggregatedPower_cfunc = self._get_library_function(
                    "RFmxLTE_ACPFetchTotalAggregatedPower"
                )
                self.RFmxLTE_ACPFetchTotalAggregatedPower_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxLTE_ACPFetchTotalAggregatedPower_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ACPFetchTotalAggregatedPower_cfunc(
            vi, selector_string, timeout, total_aggregated_power
        )

    def RFmxLTE_CHPFetchComponentCarrierMeasurement(
        self, vi, selector_string, timeout, absolute_power, relative_power
    ):
        """RFmxLTE_CHPFetchComponentCarrierMeasurement."""
        with self._func_lock:
            if self.RFmxLTE_CHPFetchComponentCarrierMeasurement_cfunc is None:
                self.RFmxLTE_CHPFetchComponentCarrierMeasurement_cfunc = self._get_library_function(
                    "RFmxLTE_CHPFetchComponentCarrierMeasurement"
                )
                self.RFmxLTE_CHPFetchComponentCarrierMeasurement_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxLTE_CHPFetchComponentCarrierMeasurement_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_CHPFetchComponentCarrierMeasurement_cfunc(
            vi, selector_string, timeout, absolute_power, relative_power
        )

    def RFmxLTE_CHPFetchSubblockMeasurement(
        self, vi, selector_string, timeout, subblock_power, integration_bandwidth, frequency
    ):
        """RFmxLTE_CHPFetchSubblockMeasurement."""
        with self._func_lock:
            if self.RFmxLTE_CHPFetchSubblockMeasurement_cfunc is None:
                self.RFmxLTE_CHPFetchSubblockMeasurement_cfunc = self._get_library_function(
                    "RFmxLTE_CHPFetchSubblockMeasurement"
                )
                self.RFmxLTE_CHPFetchSubblockMeasurement_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxLTE_CHPFetchSubblockMeasurement_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_CHPFetchSubblockMeasurement_cfunc(
            vi, selector_string, timeout, subblock_power, integration_bandwidth, frequency
        )

    def RFmxLTE_CHPFetchTotalAggregatedPower(
        self, vi, selector_string, timeout, total_aggregated_power
    ):
        """RFmxLTE_CHPFetchTotalAggregatedPower."""
        with self._func_lock:
            if self.RFmxLTE_CHPFetchTotalAggregatedPower_cfunc is None:
                self.RFmxLTE_CHPFetchTotalAggregatedPower_cfunc = self._get_library_function(
                    "RFmxLTE_CHPFetchTotalAggregatedPower"
                )
                self.RFmxLTE_CHPFetchTotalAggregatedPower_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxLTE_CHPFetchTotalAggregatedPower_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_CHPFetchTotalAggregatedPower_cfunc(
            vi, selector_string, timeout, total_aggregated_power
        )

    def RFmxLTE_ModAccFetchCompositeEVM(
        self,
        vi,
        selector_string,
        timeout,
        mean_rms_composite_evm,
        maximum_peak_composite_evm,
        mean_frequency_error,
        peak_composite_evm_symbol_index,
        peak_composite_evm_subcarrier_index,
        peak_composite_evm_slot_index,
    ):
        """RFmxLTE_ModAccFetchCompositeEVM."""
        with self._func_lock:
            if self.RFmxLTE_ModAccFetchCompositeEVM_cfunc is None:
                self.RFmxLTE_ModAccFetchCompositeEVM_cfunc = self._get_library_function(
                    "RFmxLTE_ModAccFetchCompositeEVM"
                )
                self.RFmxLTE_ModAccFetchCompositeEVM_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_int32),
                    ctypes.POINTER(ctypes.c_int32),
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxLTE_ModAccFetchCompositeEVM_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ModAccFetchCompositeEVM_cfunc(
            vi,
            selector_string,
            timeout,
            mean_rms_composite_evm,
            maximum_peak_composite_evm,
            mean_frequency_error,
            peak_composite_evm_symbol_index,
            peak_composite_evm_subcarrier_index,
            peak_composite_evm_slot_index,
        )

    def RFmxLTE_ModAccFetchCompositeMagnitudeAndPhaseError(
        self,
        vi,
        selector_string,
        timeout,
        mean_rms_composite_magnitude_error,
        maximum_peak_composite_magnitude_error,
        mean_rms_composite_phase_error,
        maximum_peak_composite_phase_error,
    ):
        """RFmxLTE_ModAccFetchCompositeMagnitudeAndPhaseError."""
        with self._func_lock:
            if self.RFmxLTE_ModAccFetchCompositeMagnitudeAndPhaseError_cfunc is None:
                self.RFmxLTE_ModAccFetchCompositeMagnitudeAndPhaseError_cfunc = (
                    self._get_library_function("RFmxLTE_ModAccFetchCompositeMagnitudeAndPhaseError")
                )
                self.RFmxLTE_ModAccFetchCompositeMagnitudeAndPhaseError_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxLTE_ModAccFetchCompositeMagnitudeAndPhaseError_cfunc.restype = (
                    ctypes.c_int32
                )
        return self.RFmxLTE_ModAccFetchCompositeMagnitudeAndPhaseError_cfunc(
            vi,
            selector_string,
            timeout,
            mean_rms_composite_magnitude_error,
            maximum_peak_composite_magnitude_error,
            mean_rms_composite_phase_error,
            maximum_peak_composite_phase_error,
        )

    def RFmxLTE_ModAccFetchCSRSEVM(self, vi, selector_string, timeout, mean_rms_csrs_evm):
        """RFmxLTE_ModAccFetchCSRSEVM."""
        with self._func_lock:
            if self.RFmxLTE_ModAccFetchCSRSEVM_cfunc is None:
                self.RFmxLTE_ModAccFetchCSRSEVM_cfunc = self._get_library_function(
                    "RFmxLTE_ModAccFetchCSRSEVM"
                )
                self.RFmxLTE_ModAccFetchCSRSEVM_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxLTE_ModAccFetchCSRSEVM_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ModAccFetchCSRSEVM_cfunc(
            vi, selector_string, timeout, mean_rms_csrs_evm
        )

    def RFmxLTE_ModAccFetchDownlinkDetectedCellID(
        self, vi, selector_string, timeout, detected_cell_id
    ):
        """RFmxLTE_ModAccFetchDownlinkDetectedCellID."""
        with self._func_lock:
            if self.RFmxLTE_ModAccFetchDownlinkDetectedCellID_cfunc is None:
                self.RFmxLTE_ModAccFetchDownlinkDetectedCellID_cfunc = self._get_library_function(
                    "RFmxLTE_ModAccFetchDownlinkDetectedCellID"
                )
                self.RFmxLTE_ModAccFetchDownlinkDetectedCellID_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxLTE_ModAccFetchDownlinkDetectedCellID_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ModAccFetchDownlinkDetectedCellID_cfunc(
            vi, selector_string, timeout, detected_cell_id
        )

    def RFmxLTE_ModAccFetchDownlinkTransmitPower(
        self,
        vi,
        selector_string,
        timeout,
        rs_transmit_power,
        ofdm_symbol_transmit_power,
        reserved_1,
        reserved_2,
    ):
        """RFmxLTE_ModAccFetchDownlinkTransmitPower."""
        with self._func_lock:
            if self.RFmxLTE_ModAccFetchDownlinkTransmitPower_cfunc is None:
                self.RFmxLTE_ModAccFetchDownlinkTransmitPower_cfunc = self._get_library_function(
                    "RFmxLTE_ModAccFetchDownlinkTransmitPower"
                )
                self.RFmxLTE_ModAccFetchDownlinkTransmitPower_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxLTE_ModAccFetchDownlinkTransmitPower_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ModAccFetchDownlinkTransmitPower_cfunc(
            vi,
            selector_string,
            timeout,
            rs_transmit_power,
            ofdm_symbol_transmit_power,
            reserved_1,
            reserved_2,
        )

    def RFmxLTE_ModAccFetchInBandEmissionMargin(
        self, vi, selector_string, timeout, in_band_emission_margin
    ):
        """RFmxLTE_ModAccFetchInBandEmissionMargin."""
        with self._func_lock:
            if self.RFmxLTE_ModAccFetchInBandEmissionMargin_cfunc is None:
                self.RFmxLTE_ModAccFetchInBandEmissionMargin_cfunc = self._get_library_function(
                    "RFmxLTE_ModAccFetchInBandEmissionMargin"
                )
                self.RFmxLTE_ModAccFetchInBandEmissionMargin_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxLTE_ModAccFetchInBandEmissionMargin_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ModAccFetchInBandEmissionMargin_cfunc(
            vi, selector_string, timeout, in_band_emission_margin
        )

    def RFmxLTE_ModAccFetchIQImpairments(
        self,
        vi,
        selector_string,
        timeout,
        mean_iq_origin_offset,
        mean_iq_gain_imbalance,
        mean_iq_quadrature_error,
    ):
        """RFmxLTE_ModAccFetchIQImpairments."""
        with self._func_lock:
            if self.RFmxLTE_ModAccFetchIQImpairments_cfunc is None:
                self.RFmxLTE_ModAccFetchIQImpairments_cfunc = self._get_library_function(
                    "RFmxLTE_ModAccFetchIQImpairments"
                )
                self.RFmxLTE_ModAccFetchIQImpairments_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxLTE_ModAccFetchIQImpairments_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ModAccFetchIQImpairments_cfunc(
            vi,
            selector_string,
            timeout,
            mean_iq_origin_offset,
            mean_iq_gain_imbalance,
            mean_iq_quadrature_error,
        )

    def RFmxLTE_ModAccFetchNPUSCHDataEVM(
        self, vi, selector_string, timeout, npusch_mean_rms_data_evm, npusch_maximum_peak_data_evm
    ):
        """RFmxLTE_ModAccFetchNPUSCHDataEVM."""
        with self._func_lock:
            if self.RFmxLTE_ModAccFetchNPUSCHDataEVM_cfunc is None:
                self.RFmxLTE_ModAccFetchNPUSCHDataEVM_cfunc = self._get_library_function(
                    "RFmxLTE_ModAccFetchNPUSCHDataEVM"
                )
                self.RFmxLTE_ModAccFetchNPUSCHDataEVM_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxLTE_ModAccFetchNPUSCHDataEVM_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ModAccFetchNPUSCHDataEVM_cfunc(
            vi, selector_string, timeout, npusch_mean_rms_data_evm, npusch_maximum_peak_data_evm
        )

    def RFmxLTE_ModAccFetchNPUSCHDMRSEVM(
        self, vi, selector_string, timeout, npusch_mean_rms_dmrs_evm, npusch_maximum_peak_dmrs_evm
    ):
        """RFmxLTE_ModAccFetchNPUSCHDMRSEVM."""
        with self._func_lock:
            if self.RFmxLTE_ModAccFetchNPUSCHDMRSEVM_cfunc is None:
                self.RFmxLTE_ModAccFetchNPUSCHDMRSEVM_cfunc = self._get_library_function(
                    "RFmxLTE_ModAccFetchNPUSCHDMRSEVM"
                )
                self.RFmxLTE_ModAccFetchNPUSCHDMRSEVM_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxLTE_ModAccFetchNPUSCHDMRSEVM_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ModAccFetchNPUSCHDMRSEVM_cfunc(
            vi, selector_string, timeout, npusch_mean_rms_dmrs_evm, npusch_maximum_peak_dmrs_evm
        )

    def RFmxLTE_ModAccFetchNPUSCHSymbolPower(
        self, vi, selector_string, timeout, npusch_mean_data_power, npusch_mean_dmrs_power
    ):
        """RFmxLTE_ModAccFetchNPUSCHSymbolPower."""
        with self._func_lock:
            if self.RFmxLTE_ModAccFetchNPUSCHSymbolPower_cfunc is None:
                self.RFmxLTE_ModAccFetchNPUSCHSymbolPower_cfunc = self._get_library_function(
                    "RFmxLTE_ModAccFetchNPUSCHSymbolPower"
                )
                self.RFmxLTE_ModAccFetchNPUSCHSymbolPower_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxLTE_ModAccFetchNPUSCHSymbolPower_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ModAccFetchNPUSCHSymbolPower_cfunc(
            vi, selector_string, timeout, npusch_mean_data_power, npusch_mean_dmrs_power
        )

    def RFmxLTE_ModAccFetchPDSCH1024QAMEVM(
        self, vi, selector_string, timeout, mean_rms_1024qam_evm
    ):
        """RFmxLTE_ModAccFetchPDSCH1024QAMEVM."""
        with self._func_lock:
            if self.RFmxLTE_ModAccFetchPDSCH1024QAMEVM_cfunc is None:
                self.RFmxLTE_ModAccFetchPDSCH1024QAMEVM_cfunc = self._get_library_function(
                    "RFmxLTE_ModAccFetchPDSCH1024QAMEVM"
                )
                self.RFmxLTE_ModAccFetchPDSCH1024QAMEVM_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxLTE_ModAccFetchPDSCH1024QAMEVM_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ModAccFetchPDSCH1024QAMEVM_cfunc(
            vi, selector_string, timeout, mean_rms_1024qam_evm
        )

    def RFmxLTE_ModAccFetchPDSCHEVM(
        self,
        vi,
        selector_string,
        timeout,
        mean_rms_evm,
        mean_rms_qpsk_evm,
        mean_rms_16qam_evm,
        mean_rms_64qam_evm,
        mean_rms_256qam_evm,
    ):
        """RFmxLTE_ModAccFetchPDSCHEVM."""
        with self._func_lock:
            if self.RFmxLTE_ModAccFetchPDSCHEVM_cfunc is None:
                self.RFmxLTE_ModAccFetchPDSCHEVM_cfunc = self._get_library_function(
                    "RFmxLTE_ModAccFetchPDSCHEVM"
                )
                self.RFmxLTE_ModAccFetchPDSCHEVM_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxLTE_ModAccFetchPDSCHEVM_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ModAccFetchPDSCHEVM_cfunc(
            vi,
            selector_string,
            timeout,
            mean_rms_evm,
            mean_rms_qpsk_evm,
            mean_rms_16qam_evm,
            mean_rms_64qam_evm,
            mean_rms_256qam_evm,
        )

    def RFmxLTE_ModAccFetchPSSCHDataEVM(
        self, vi, selector_string, timeout, pssch_mean_rms_data_evm, pssch_maximum_peak_data_evm
    ):
        """RFmxLTE_ModAccFetchPSSCHDataEVM."""
        with self._func_lock:
            if self.RFmxLTE_ModAccFetchPSSCHDataEVM_cfunc is None:
                self.RFmxLTE_ModAccFetchPSSCHDataEVM_cfunc = self._get_library_function(
                    "RFmxLTE_ModAccFetchPSSCHDataEVM"
                )
                self.RFmxLTE_ModAccFetchPSSCHDataEVM_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxLTE_ModAccFetchPSSCHDataEVM_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ModAccFetchPSSCHDataEVM_cfunc(
            vi, selector_string, timeout, pssch_mean_rms_data_evm, pssch_maximum_peak_data_evm
        )

    def RFmxLTE_ModAccFetchPSSCHDMRSEVM(
        self, vi, selector_string, timeout, pssch_mean_rms_dmrs_evm, pssch_maximum_peak_dmrs_evm
    ):
        """RFmxLTE_ModAccFetchPSSCHDMRSEVM."""
        with self._func_lock:
            if self.RFmxLTE_ModAccFetchPSSCHDMRSEVM_cfunc is None:
                self.RFmxLTE_ModAccFetchPSSCHDMRSEVM_cfunc = self._get_library_function(
                    "RFmxLTE_ModAccFetchPSSCHDMRSEVM"
                )
                self.RFmxLTE_ModAccFetchPSSCHDMRSEVM_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxLTE_ModAccFetchPSSCHDMRSEVM_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ModAccFetchPSSCHDMRSEVM_cfunc(
            vi, selector_string, timeout, pssch_mean_rms_dmrs_evm, pssch_maximum_peak_dmrs_evm
        )

    def RFmxLTE_ModAccFetchPSSCHSymbolPower(
        self, vi, selector_string, timeout, pssch_mean_data_power, pssch_mean_dmrs_power
    ):
        """RFmxLTE_ModAccFetchPSSCHSymbolPower."""
        with self._func_lock:
            if self.RFmxLTE_ModAccFetchPSSCHSymbolPower_cfunc is None:
                self.RFmxLTE_ModAccFetchPSSCHSymbolPower_cfunc = self._get_library_function(
                    "RFmxLTE_ModAccFetchPSSCHSymbolPower"
                )
                self.RFmxLTE_ModAccFetchPSSCHSymbolPower_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxLTE_ModAccFetchPSSCHSymbolPower_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ModAccFetchPSSCHSymbolPower_cfunc(
            vi, selector_string, timeout, pssch_mean_data_power, pssch_mean_dmrs_power
        )

    def RFmxLTE_ModAccFetchPUSCHDataEVM(
        self, vi, selector_string, timeout, mean_rms_data_evm, maximum_peak_data_evm
    ):
        """RFmxLTE_ModAccFetchPUSCHDataEVM."""
        with self._func_lock:
            if self.RFmxLTE_ModAccFetchPUSCHDataEVM_cfunc is None:
                self.RFmxLTE_ModAccFetchPUSCHDataEVM_cfunc = self._get_library_function(
                    "RFmxLTE_ModAccFetchPUSCHDataEVM"
                )
                self.RFmxLTE_ModAccFetchPUSCHDataEVM_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxLTE_ModAccFetchPUSCHDataEVM_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ModAccFetchPUSCHDataEVM_cfunc(
            vi, selector_string, timeout, mean_rms_data_evm, maximum_peak_data_evm
        )

    def RFmxLTE_ModAccFetchPUSCHDMRSEVM(
        self, vi, selector_string, timeout, mean_rms_dmrs_evm, maximum_peak_dmrs_evm
    ):
        """RFmxLTE_ModAccFetchPUSCHDMRSEVM."""
        with self._func_lock:
            if self.RFmxLTE_ModAccFetchPUSCHDMRSEVM_cfunc is None:
                self.RFmxLTE_ModAccFetchPUSCHDMRSEVM_cfunc = self._get_library_function(
                    "RFmxLTE_ModAccFetchPUSCHDMRSEVM"
                )
                self.RFmxLTE_ModAccFetchPUSCHDMRSEVM_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxLTE_ModAccFetchPUSCHDMRSEVM_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ModAccFetchPUSCHDMRSEVM_cfunc(
            vi, selector_string, timeout, mean_rms_dmrs_evm, maximum_peak_dmrs_evm
        )

    def RFmxLTE_ModAccFetchPUSCHSymbolPower(
        self, vi, selector_string, timeout, pusch_mean_data_power, pusch_mean_dmrs_power
    ):
        """RFmxLTE_ModAccFetchPUSCHSymbolPower."""
        with self._func_lock:
            if self.RFmxLTE_ModAccFetchPUSCHSymbolPower_cfunc is None:
                self.RFmxLTE_ModAccFetchPUSCHSymbolPower_cfunc = self._get_library_function(
                    "RFmxLTE_ModAccFetchPUSCHSymbolPower"
                )
                self.RFmxLTE_ModAccFetchPUSCHSymbolPower_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxLTE_ModAccFetchPUSCHSymbolPower_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ModAccFetchPUSCHSymbolPower_cfunc(
            vi, selector_string, timeout, pusch_mean_data_power, pusch_mean_dmrs_power
        )

    def RFmxLTE_ModAccFetchSpectralFlatness(
        self,
        vi,
        selector_string,
        timeout,
        range1_maximum_to_range1_minimum,
        range2_maximum_to_range2_minimum,
        range1_maximum_to_range2_minimum,
        range2_maximum_to_range1_minimum,
    ):
        """RFmxLTE_ModAccFetchSpectralFlatness."""
        with self._func_lock:
            if self.RFmxLTE_ModAccFetchSpectralFlatness_cfunc is None:
                self.RFmxLTE_ModAccFetchSpectralFlatness_cfunc = self._get_library_function(
                    "RFmxLTE_ModAccFetchSpectralFlatness"
                )
                self.RFmxLTE_ModAccFetchSpectralFlatness_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxLTE_ModAccFetchSpectralFlatness_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ModAccFetchSpectralFlatness_cfunc(
            vi,
            selector_string,
            timeout,
            range1_maximum_to_range1_minimum,
            range2_maximum_to_range2_minimum,
            range1_maximum_to_range2_minimum,
            range2_maximum_to_range1_minimum,
        )

    def RFmxLTE_ModAccFetchSRSEVM(
        self, vi, selector_string, timeout, mean_rms_srs_evm, mean_srs_power
    ):
        """RFmxLTE_ModAccFetchSRSEVM."""
        with self._func_lock:
            if self.RFmxLTE_ModAccFetchSRSEVM_cfunc is None:
                self.RFmxLTE_ModAccFetchSRSEVM_cfunc = self._get_library_function(
                    "RFmxLTE_ModAccFetchSRSEVM"
                )
                self.RFmxLTE_ModAccFetchSRSEVM_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxLTE_ModAccFetchSRSEVM_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ModAccFetchSRSEVM_cfunc(
            vi, selector_string, timeout, mean_rms_srs_evm, mean_srs_power
        )

    def RFmxLTE_ModAccFetchSubblockInBandEmissionMargin(
        self, vi, selector_string, timeout, subblock_in_band_emission_margin
    ):
        """RFmxLTE_ModAccFetchSubblockInBandEmissionMargin."""
        with self._func_lock:
            if self.RFmxLTE_ModAccFetchSubblockInBandEmissionMargin_cfunc is None:
                self.RFmxLTE_ModAccFetchSubblockInBandEmissionMargin_cfunc = (
                    self._get_library_function("RFmxLTE_ModAccFetchSubblockInBandEmissionMargin")
                )
                self.RFmxLTE_ModAccFetchSubblockInBandEmissionMargin_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxLTE_ModAccFetchSubblockInBandEmissionMargin_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ModAccFetchSubblockInBandEmissionMargin_cfunc(
            vi, selector_string, timeout, subblock_in_band_emission_margin
        )

    def RFmxLTE_ModAccFetchSubblockIQImpairments(
        self,
        vi,
        selector_string,
        timeout,
        subblock_mean_iq_origin_offset,
        subblock_mean_iq_gain_imbalance,
        subblock_mean_iq_quadrature_error,
    ):
        """RFmxLTE_ModAccFetchSubblockIQImpairments."""
        with self._func_lock:
            if self.RFmxLTE_ModAccFetchSubblockIQImpairments_cfunc is None:
                self.RFmxLTE_ModAccFetchSubblockIQImpairments_cfunc = self._get_library_function(
                    "RFmxLTE_ModAccFetchSubblockIQImpairments"
                )
                self.RFmxLTE_ModAccFetchSubblockIQImpairments_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxLTE_ModAccFetchSubblockIQImpairments_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ModAccFetchSubblockIQImpairments_cfunc(
            vi,
            selector_string,
            timeout,
            subblock_mean_iq_origin_offset,
            subblock_mean_iq_gain_imbalance,
            subblock_mean_iq_quadrature_error,
        )

    def RFmxLTE_ModAccFetchSynchronizationSignalEVM(
        self, vi, selector_string, timeout, mean_rms_pss_evm, mean_rms_sss_evm
    ):
        """RFmxLTE_ModAccFetchSynchronizationSignalEVM."""
        with self._func_lock:
            if self.RFmxLTE_ModAccFetchSynchronizationSignalEVM_cfunc is None:
                self.RFmxLTE_ModAccFetchSynchronizationSignalEVM_cfunc = self._get_library_function(
                    "RFmxLTE_ModAccFetchSynchronizationSignalEVM"
                )
                self.RFmxLTE_ModAccFetchSynchronizationSignalEVM_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxLTE_ModAccFetchSynchronizationSignalEVM_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ModAccFetchSynchronizationSignalEVM_cfunc(
            vi, selector_string, timeout, mean_rms_pss_evm, mean_rms_sss_evm
        )

    def RFmxLTE_OBWFetchMeasurement(
        self,
        vi,
        selector_string,
        timeout,
        occupied_bandwidth,
        absolute_power,
        start_frequency,
        stop_frequency,
    ):
        """RFmxLTE_OBWFetchMeasurement."""
        with self._func_lock:
            if self.RFmxLTE_OBWFetchMeasurement_cfunc is None:
                self.RFmxLTE_OBWFetchMeasurement_cfunc = self._get_library_function(
                    "RFmxLTE_OBWFetchMeasurement"
                )
                self.RFmxLTE_OBWFetchMeasurement_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxLTE_OBWFetchMeasurement_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_OBWFetchMeasurement_cfunc(
            vi,
            selector_string,
            timeout,
            occupied_bandwidth,
            absolute_power,
            start_frequency,
            stop_frequency,
        )

    def RFmxLTE_SEMFetchComponentCarrierMeasurement(
        self, vi, selector_string, timeout, absolute_integrated_power, relative_integrated_power
    ):
        """RFmxLTE_SEMFetchComponentCarrierMeasurement."""
        with self._func_lock:
            if self.RFmxLTE_SEMFetchComponentCarrierMeasurement_cfunc is None:
                self.RFmxLTE_SEMFetchComponentCarrierMeasurement_cfunc = self._get_library_function(
                    "RFmxLTE_SEMFetchComponentCarrierMeasurement"
                )
                self.RFmxLTE_SEMFetchComponentCarrierMeasurement_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxLTE_SEMFetchComponentCarrierMeasurement_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_SEMFetchComponentCarrierMeasurement_cfunc(
            vi, selector_string, timeout, absolute_integrated_power, relative_integrated_power
        )

    def RFmxLTE_SEMFetchLowerOffsetMargin(
        self,
        vi,
        selector_string,
        timeout,
        measurement_status,
        margin,
        margin_frequency,
        margin_absolute_power,
        margin_relative_power,
    ):
        """RFmxLTE_SEMFetchLowerOffsetMargin."""
        with self._func_lock:
            if self.RFmxLTE_SEMFetchLowerOffsetMargin_cfunc is None:
                self.RFmxLTE_SEMFetchLowerOffsetMargin_cfunc = self._get_library_function(
                    "RFmxLTE_SEMFetchLowerOffsetMargin"
                )
                self.RFmxLTE_SEMFetchLowerOffsetMargin_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_int32),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxLTE_SEMFetchLowerOffsetMargin_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_SEMFetchLowerOffsetMargin_cfunc(
            vi,
            selector_string,
            timeout,
            measurement_status,
            margin,
            margin_frequency,
            margin_absolute_power,
            margin_relative_power,
        )

    def RFmxLTE_SEMFetchLowerOffsetPower(
        self,
        vi,
        selector_string,
        timeout,
        absolute_integrated_power,
        relative_integrated_power,
        absolute_peak_power,
        peak_frequency,
        relative_peak_power,
    ):
        """RFmxLTE_SEMFetchLowerOffsetPower."""
        with self._func_lock:
            if self.RFmxLTE_SEMFetchLowerOffsetPower_cfunc is None:
                self.RFmxLTE_SEMFetchLowerOffsetPower_cfunc = self._get_library_function(
                    "RFmxLTE_SEMFetchLowerOffsetPower"
                )
                self.RFmxLTE_SEMFetchLowerOffsetPower_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxLTE_SEMFetchLowerOffsetPower_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_SEMFetchLowerOffsetPower_cfunc(
            vi,
            selector_string,
            timeout,
            absolute_integrated_power,
            relative_integrated_power,
            absolute_peak_power,
            peak_frequency,
            relative_peak_power,
        )

    def RFmxLTE_SEMFetchMeasurementStatus(self, vi, selector_string, timeout, measurement_status):
        """RFmxLTE_SEMFetchMeasurementStatus."""
        with self._func_lock:
            if self.RFmxLTE_SEMFetchMeasurementStatus_cfunc is None:
                self.RFmxLTE_SEMFetchMeasurementStatus_cfunc = self._get_library_function(
                    "RFmxLTE_SEMFetchMeasurementStatus"
                )
                self.RFmxLTE_SEMFetchMeasurementStatus_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxLTE_SEMFetchMeasurementStatus_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_SEMFetchMeasurementStatus_cfunc(
            vi, selector_string, timeout, measurement_status
        )

    def RFmxLTE_SEMFetchSubblockMeasurement(
        self, vi, selector_string, timeout, subblock_power, integration_bandwidth, frequency
    ):
        """RFmxLTE_SEMFetchSubblockMeasurement."""
        with self._func_lock:
            if self.RFmxLTE_SEMFetchSubblockMeasurement_cfunc is None:
                self.RFmxLTE_SEMFetchSubblockMeasurement_cfunc = self._get_library_function(
                    "RFmxLTE_SEMFetchSubblockMeasurement"
                )
                self.RFmxLTE_SEMFetchSubblockMeasurement_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxLTE_SEMFetchSubblockMeasurement_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_SEMFetchSubblockMeasurement_cfunc(
            vi, selector_string, timeout, subblock_power, integration_bandwidth, frequency
        )

    def RFmxLTE_SEMFetchTotalAggregatedPower(
        self, vi, selector_string, timeout, total_aggregated_power
    ):
        """RFmxLTE_SEMFetchTotalAggregatedPower."""
        with self._func_lock:
            if self.RFmxLTE_SEMFetchTotalAggregatedPower_cfunc is None:
                self.RFmxLTE_SEMFetchTotalAggregatedPower_cfunc = self._get_library_function(
                    "RFmxLTE_SEMFetchTotalAggregatedPower"
                )
                self.RFmxLTE_SEMFetchTotalAggregatedPower_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxLTE_SEMFetchTotalAggregatedPower_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_SEMFetchTotalAggregatedPower_cfunc(
            vi, selector_string, timeout, total_aggregated_power
        )

    def RFmxLTE_SEMFetchUpperOffsetMargin(
        self,
        vi,
        selector_string,
        timeout,
        measurement_status,
        margin,
        margin_frequency,
        margin_absolute_power,
        margin_relative_power,
    ):
        """RFmxLTE_SEMFetchUpperOffsetMargin."""
        with self._func_lock:
            if self.RFmxLTE_SEMFetchUpperOffsetMargin_cfunc is None:
                self.RFmxLTE_SEMFetchUpperOffsetMargin_cfunc = self._get_library_function(
                    "RFmxLTE_SEMFetchUpperOffsetMargin"
                )
                self.RFmxLTE_SEMFetchUpperOffsetMargin_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_int32),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxLTE_SEMFetchUpperOffsetMargin_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_SEMFetchUpperOffsetMargin_cfunc(
            vi,
            selector_string,
            timeout,
            measurement_status,
            margin,
            margin_frequency,
            margin_absolute_power,
            margin_relative_power,
        )

    def RFmxLTE_SEMFetchUpperOffsetPower(
        self,
        vi,
        selector_string,
        timeout,
        absolute_integrated_power,
        relative_integrated_power,
        absolute_peak_power,
        peak_frequency,
        relative_peak_power,
    ):
        """RFmxLTE_SEMFetchUpperOffsetPower."""
        with self._func_lock:
            if self.RFmxLTE_SEMFetchUpperOffsetPower_cfunc is None:
                self.RFmxLTE_SEMFetchUpperOffsetPower_cfunc = self._get_library_function(
                    "RFmxLTE_SEMFetchUpperOffsetPower"
                )
                self.RFmxLTE_SEMFetchUpperOffsetPower_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxLTE_SEMFetchUpperOffsetPower_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_SEMFetchUpperOffsetPower_cfunc(
            vi,
            selector_string,
            timeout,
            absolute_integrated_power,
            relative_integrated_power,
            absolute_peak_power,
            peak_frequency,
            relative_peak_power,
        )

    def RFmxLTE_PVTFetchMeasurement(
        self,
        vi,
        selector_string,
        timeout,
        measurement_status,
        mean_absolute_off_power_before,
        mean_absolute_off_power_after,
        mean_absolute_on_power,
        burst_width,
    ):
        """RFmxLTE_PVTFetchMeasurement."""
        with self._func_lock:
            if self.RFmxLTE_PVTFetchMeasurement_cfunc is None:
                self.RFmxLTE_PVTFetchMeasurement_cfunc = self._get_library_function(
                    "RFmxLTE_PVTFetchMeasurement"
                )
                self.RFmxLTE_PVTFetchMeasurement_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_int32),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxLTE_PVTFetchMeasurement_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_PVTFetchMeasurement_cfunc(
            vi,
            selector_string,
            timeout,
            measurement_status,
            mean_absolute_off_power_before,
            mean_absolute_off_power_after,
            mean_absolute_on_power,
            burst_width,
        )

    def RFmxLTE_SlotPhaseFetchMaximumPhaseDiscontinuity(
        self, vi, selector_string, timeout, maximum_phase_discontinuity
    ):
        """RFmxLTE_SlotPhaseFetchMaximumPhaseDiscontinuity."""
        with self._func_lock:
            if self.RFmxLTE_SlotPhaseFetchMaximumPhaseDiscontinuity_cfunc is None:
                self.RFmxLTE_SlotPhaseFetchMaximumPhaseDiscontinuity_cfunc = (
                    self._get_library_function("RFmxLTE_SlotPhaseFetchMaximumPhaseDiscontinuity")
                )
                self.RFmxLTE_SlotPhaseFetchMaximumPhaseDiscontinuity_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxLTE_SlotPhaseFetchMaximumPhaseDiscontinuity_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_SlotPhaseFetchMaximumPhaseDiscontinuity_cfunc(
            vi, selector_string, timeout, maximum_phase_discontinuity
        )

    def RFmxLTE_TXPFetchMeasurement(
        self, vi, selector_string, timeout, average_power_mean, peak_power_maximum
    ):
        """RFmxLTE_TXPFetchMeasurement."""
        with self._func_lock:
            if self.RFmxLTE_TXPFetchMeasurement_cfunc is None:
                self.RFmxLTE_TXPFetchMeasurement_cfunc = self._get_library_function(
                    "RFmxLTE_TXPFetchMeasurement"
                )
                self.RFmxLTE_TXPFetchMeasurement_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxLTE_TXPFetchMeasurement_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_TXPFetchMeasurement_cfunc(
            vi, selector_string, timeout, average_power_mean, peak_power_maximum
        )

    def RFmxLTE_ACPFetchAbsolutePowersTrace(
        self,
        vi,
        selector_string,
        timeout,
        trace_index,
        x0,
        dx,
        absolute_powers_trace,
        array_size,
        actual_array_size,
    ):
        """RFmxLTE_ACPFetchAbsolutePowersTrace."""
        with self._func_lock:
            if self.RFmxLTE_ACPFetchAbsolutePowersTrace_cfunc is None:
                self.RFmxLTE_ACPFetchAbsolutePowersTrace_cfunc = self._get_library_function(
                    "RFmxLTE_ACPFetchAbsolutePowersTrace"
                )
                self.RFmxLTE_ACPFetchAbsolutePowersTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxLTE_ACPFetchAbsolutePowersTrace_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ACPFetchAbsolutePowersTrace_cfunc(
            vi,
            selector_string,
            timeout,
            trace_index,
            x0,
            dx,
            absolute_powers_trace,
            array_size,
            actual_array_size,
        )

    def RFmxLTE_ACPFetchComponentCarrierMeasurementArray(
        self,
        vi,
        selector_string,
        timeout,
        absolute_power,
        relative_power,
        array_size,
        actual_array_size,
    ):
        """RFmxLTE_ACPFetchComponentCarrierMeasurementArray."""
        with self._func_lock:
            if self.RFmxLTE_ACPFetchComponentCarrierMeasurementArray_cfunc is None:
                self.RFmxLTE_ACPFetchComponentCarrierMeasurementArray_cfunc = (
                    self._get_library_function("RFmxLTE_ACPFetchComponentCarrierMeasurementArray")
                )
                self.RFmxLTE_ACPFetchComponentCarrierMeasurementArray_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxLTE_ACPFetchComponentCarrierMeasurementArray_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ACPFetchComponentCarrierMeasurementArray_cfunc(
            vi,
            selector_string,
            timeout,
            absolute_power,
            relative_power,
            array_size,
            actual_array_size,
        )

    def RFmxLTE_ACPFetchOffsetMeasurementArray(
        self,
        vi,
        selector_string,
        timeout,
        lower_relative_power,
        upper_relative_power,
        lower_absolute_power,
        upper_absolute_power,
        array_size,
        actual_array_size,
    ):
        """RFmxLTE_ACPFetchOffsetMeasurementArray."""
        with self._func_lock:
            if self.RFmxLTE_ACPFetchOffsetMeasurementArray_cfunc is None:
                self.RFmxLTE_ACPFetchOffsetMeasurementArray_cfunc = self._get_library_function(
                    "RFmxLTE_ACPFetchOffsetMeasurementArray"
                )
                self.RFmxLTE_ACPFetchOffsetMeasurementArray_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxLTE_ACPFetchOffsetMeasurementArray_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ACPFetchOffsetMeasurementArray_cfunc(
            vi,
            selector_string,
            timeout,
            lower_relative_power,
            upper_relative_power,
            lower_absolute_power,
            upper_absolute_power,
            array_size,
            actual_array_size,
        )

    def RFmxLTE_ACPFetchRelativePowersTrace(
        self,
        vi,
        selector_string,
        timeout,
        trace_index,
        x0,
        dx,
        relative_powers_trace,
        array_size,
        actual_array_size,
    ):
        """RFmxLTE_ACPFetchRelativePowersTrace."""
        with self._func_lock:
            if self.RFmxLTE_ACPFetchRelativePowersTrace_cfunc is None:
                self.RFmxLTE_ACPFetchRelativePowersTrace_cfunc = self._get_library_function(
                    "RFmxLTE_ACPFetchRelativePowersTrace"
                )
                self.RFmxLTE_ACPFetchRelativePowersTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxLTE_ACPFetchRelativePowersTrace_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ACPFetchRelativePowersTrace_cfunc(
            vi,
            selector_string,
            timeout,
            trace_index,
            x0,
            dx,
            relative_powers_trace,
            array_size,
            actual_array_size,
        )

    def RFmxLTE_ACPFetchSpectrum(
        self, vi, selector_string, timeout, x0, dx, spectrum, array_size, actual_array_size
    ):
        """RFmxLTE_ACPFetchSpectrum."""
        with self._func_lock:
            if self.RFmxLTE_ACPFetchSpectrum_cfunc is None:
                self.RFmxLTE_ACPFetchSpectrum_cfunc = self._get_library_function(
                    "RFmxLTE_ACPFetchSpectrum"
                )
                self.RFmxLTE_ACPFetchSpectrum_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxLTE_ACPFetchSpectrum_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ACPFetchSpectrum_cfunc(
            vi, selector_string, timeout, x0, dx, spectrum, array_size, actual_array_size
        )

    def RFmxLTE_CHPFetchComponentCarrierMeasurementArray(
        self,
        vi,
        selector_string,
        timeout,
        absolute_power,
        relative_power,
        array_size,
        actual_array_size,
    ):
        """RFmxLTE_CHPFetchComponentCarrierMeasurementArray."""
        with self._func_lock:
            if self.RFmxLTE_CHPFetchComponentCarrierMeasurementArray_cfunc is None:
                self.RFmxLTE_CHPFetchComponentCarrierMeasurementArray_cfunc = (
                    self._get_library_function("RFmxLTE_CHPFetchComponentCarrierMeasurementArray")
                )
                self.RFmxLTE_CHPFetchComponentCarrierMeasurementArray_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxLTE_CHPFetchComponentCarrierMeasurementArray_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_CHPFetchComponentCarrierMeasurementArray_cfunc(
            vi,
            selector_string,
            timeout,
            absolute_power,
            relative_power,
            array_size,
            actual_array_size,
        )

    def RFmxLTE_CHPFetchSpectrum(
        self, vi, selector_string, timeout, x0, dx, spectrum, array_size, actual_array_size
    ):
        """RFmxLTE_CHPFetchSpectrum."""
        with self._func_lock:
            if self.RFmxLTE_CHPFetchSpectrum_cfunc is None:
                self.RFmxLTE_CHPFetchSpectrum_cfunc = self._get_library_function(
                    "RFmxLTE_CHPFetchSpectrum"
                )
                self.RFmxLTE_CHPFetchSpectrum_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxLTE_CHPFetchSpectrum_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_CHPFetchSpectrum_cfunc(
            vi, selector_string, timeout, x0, dx, spectrum, array_size, actual_array_size
        )

    def RFmxLTE_ModAccFetchCompositeEVMArray(
        self,
        vi,
        selector_string,
        timeout,
        mean_rms_composite_evm,
        maximum_peak_composite_evm,
        mean_frequency_error,
        peak_composite_evm_symbol_index,
        peak_composite_evm_subcarrier_index,
        peak_composite_evm_slot_index,
        array_size,
        actual_array_size,
    ):
        """RFmxLTE_ModAccFetchCompositeEVMArray."""
        with self._func_lock:
            if self.RFmxLTE_ModAccFetchCompositeEVMArray_cfunc is None:
                self.RFmxLTE_ModAccFetchCompositeEVMArray_cfunc = self._get_library_function(
                    "RFmxLTE_ModAccFetchCompositeEVMArray"
                )
                self.RFmxLTE_ModAccFetchCompositeEVMArray_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_int32),
                    ctypes.POINTER(ctypes.c_int32),
                    ctypes.POINTER(ctypes.c_int32),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxLTE_ModAccFetchCompositeEVMArray_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ModAccFetchCompositeEVMArray_cfunc(
            vi,
            selector_string,
            timeout,
            mean_rms_composite_evm,
            maximum_peak_composite_evm,
            mean_frequency_error,
            peak_composite_evm_symbol_index,
            peak_composite_evm_subcarrier_index,
            peak_composite_evm_slot_index,
            array_size,
            actual_array_size,
        )

    def RFmxLTE_ModAccFetchCompositeMagnitudeAndPhaseErrorArray(
        self,
        vi,
        selector_string,
        timeout,
        mean_rms_composite_magnitude_error,
        maximum_peak_composite_magnitude_error,
        mean_rms_composite_phase_error,
        maximum_peak_composite_phase_error,
        array_size,
        actual_array_size,
    ):
        """RFmxLTE_ModAccFetchCompositeMagnitudeAndPhaseErrorArray."""
        with self._func_lock:
            if self.RFmxLTE_ModAccFetchCompositeMagnitudeAndPhaseErrorArray_cfunc is None:
                self.RFmxLTE_ModAccFetchCompositeMagnitudeAndPhaseErrorArray_cfunc = (
                    self._get_library_function(
                        "RFmxLTE_ModAccFetchCompositeMagnitudeAndPhaseErrorArray"
                    )
                )
                self.RFmxLTE_ModAccFetchCompositeMagnitudeAndPhaseErrorArray_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxLTE_ModAccFetchCompositeMagnitudeAndPhaseErrorArray_cfunc.restype = (
                    ctypes.c_int32
                )
        return self.RFmxLTE_ModAccFetchCompositeMagnitudeAndPhaseErrorArray_cfunc(
            vi,
            selector_string,
            timeout,
            mean_rms_composite_magnitude_error,
            maximum_peak_composite_magnitude_error,
            mean_rms_composite_phase_error,
            maximum_peak_composite_phase_error,
            array_size,
            actual_array_size,
        )

    def RFmxLTE_ModAccFetchCSRSConstellation(
        self, vi, selector_string, timeout, csrs_constellation, array_size, actual_array_size
    ):
        """RFmxLTE_ModAccFetchCSRSConstellation."""
        with self._func_lock:
            if self.RFmxLTE_ModAccFetchCSRSConstellation_cfunc is None:
                self.RFmxLTE_ModAccFetchCSRSConstellation_cfunc = self._get_library_function(
                    "RFmxLTE_ModAccFetchCSRSConstellation"
                )
                self.RFmxLTE_ModAccFetchCSRSConstellation_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(_custom_types.ComplexSingle),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxLTE_ModAccFetchCSRSConstellation_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ModAccFetchCSRSConstellation_cfunc(
            vi, selector_string, timeout, csrs_constellation, array_size, actual_array_size
        )

    def RFmxLTE_ModAccFetchCSRSEVMArray(
        self, vi, selector_string, timeout, mean_rms_csrs_evm, array_size, actual_array_size
    ):
        """RFmxLTE_ModAccFetchCSRSEVMArray."""
        with self._func_lock:
            if self.RFmxLTE_ModAccFetchCSRSEVMArray_cfunc is None:
                self.RFmxLTE_ModAccFetchCSRSEVMArray_cfunc = self._get_library_function(
                    "RFmxLTE_ModAccFetchCSRSEVMArray"
                )
                self.RFmxLTE_ModAccFetchCSRSEVMArray_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxLTE_ModAccFetchCSRSEVMArray_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ModAccFetchCSRSEVMArray_cfunc(
            vi, selector_string, timeout, mean_rms_csrs_evm, array_size, actual_array_size
        )

    def RFmxLTE_ModAccFetchDownlinkDetectedCellIDArray(
        self, vi, selector_string, timeout, detected_cell_id, array_size, actual_array_size
    ):
        """RFmxLTE_ModAccFetchDownlinkDetectedCellIDArray."""
        with self._func_lock:
            if self.RFmxLTE_ModAccFetchDownlinkDetectedCellIDArray_cfunc is None:
                self.RFmxLTE_ModAccFetchDownlinkDetectedCellIDArray_cfunc = (
                    self._get_library_function("RFmxLTE_ModAccFetchDownlinkDetectedCellIDArray")
                )
                self.RFmxLTE_ModAccFetchDownlinkDetectedCellIDArray_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_int32),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxLTE_ModAccFetchDownlinkDetectedCellIDArray_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ModAccFetchDownlinkDetectedCellIDArray_cfunc(
            vi, selector_string, timeout, detected_cell_id, array_size, actual_array_size
        )

    def RFmxLTE_ModAccFetchDownlinkPBCHConstellation(
        self, vi, selector_string, timeout, pbch_constellation, array_size, actual_array_size
    ):
        """RFmxLTE_ModAccFetchDownlinkPBCHConstellation."""
        with self._func_lock:
            if self.RFmxLTE_ModAccFetchDownlinkPBCHConstellation_cfunc is None:
                self.RFmxLTE_ModAccFetchDownlinkPBCHConstellation_cfunc = (
                    self._get_library_function("RFmxLTE_ModAccFetchDownlinkPBCHConstellation")
                )
                self.RFmxLTE_ModAccFetchDownlinkPBCHConstellation_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(_custom_types.ComplexSingle),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxLTE_ModAccFetchDownlinkPBCHConstellation_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ModAccFetchDownlinkPBCHConstellation_cfunc(
            vi, selector_string, timeout, pbch_constellation, array_size, actual_array_size
        )

    def RFmxLTE_ModAccFetchDownlinkPCFICHConstellation(
        self, vi, selector_string, timeout, pcfich_constellation, array_size, actual_array_size
    ):
        """RFmxLTE_ModAccFetchDownlinkPCFICHConstellation."""
        with self._func_lock:
            if self.RFmxLTE_ModAccFetchDownlinkPCFICHConstellation_cfunc is None:
                self.RFmxLTE_ModAccFetchDownlinkPCFICHConstellation_cfunc = (
                    self._get_library_function("RFmxLTE_ModAccFetchDownlinkPCFICHConstellation")
                )
                self.RFmxLTE_ModAccFetchDownlinkPCFICHConstellation_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(_custom_types.ComplexSingle),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxLTE_ModAccFetchDownlinkPCFICHConstellation_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ModAccFetchDownlinkPCFICHConstellation_cfunc(
            vi, selector_string, timeout, pcfich_constellation, array_size, actual_array_size
        )

    def RFmxLTE_ModAccFetchDownlinkPDCCHConstellation(
        self, vi, selector_string, timeout, pdcch_constellation, array_size, actual_array_size
    ):
        """RFmxLTE_ModAccFetchDownlinkPDCCHConstellation."""
        with self._func_lock:
            if self.RFmxLTE_ModAccFetchDownlinkPDCCHConstellation_cfunc is None:
                self.RFmxLTE_ModAccFetchDownlinkPDCCHConstellation_cfunc = (
                    self._get_library_function("RFmxLTE_ModAccFetchDownlinkPDCCHConstellation")
                )
                self.RFmxLTE_ModAccFetchDownlinkPDCCHConstellation_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(_custom_types.ComplexSingle),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxLTE_ModAccFetchDownlinkPDCCHConstellation_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ModAccFetchDownlinkPDCCHConstellation_cfunc(
            vi, selector_string, timeout, pdcch_constellation, array_size, actual_array_size
        )

    def RFmxLTE_ModAccFetchDownlinkPHICHConstellation(
        self, vi, selector_string, timeout, phich_constellation, array_size, actual_array_size
    ):
        """RFmxLTE_ModAccFetchDownlinkPHICHConstellation."""
        with self._func_lock:
            if self.RFmxLTE_ModAccFetchDownlinkPHICHConstellation_cfunc is None:
                self.RFmxLTE_ModAccFetchDownlinkPHICHConstellation_cfunc = (
                    self._get_library_function("RFmxLTE_ModAccFetchDownlinkPHICHConstellation")
                )
                self.RFmxLTE_ModAccFetchDownlinkPHICHConstellation_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(_custom_types.ComplexSingle),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxLTE_ModAccFetchDownlinkPHICHConstellation_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ModAccFetchDownlinkPHICHConstellation_cfunc(
            vi, selector_string, timeout, phich_constellation, array_size, actual_array_size
        )

    def RFmxLTE_ModAccFetchDownlinkTransmitPowerArray(
        self,
        vi,
        selector_string,
        timeout,
        rs_transmit_power,
        ofdm_symbol_transmit_power,
        reserved_1,
        reserved_2,
        array_size,
        actual_array_size,
    ):
        """RFmxLTE_ModAccFetchDownlinkTransmitPowerArray."""
        with self._func_lock:
            if self.RFmxLTE_ModAccFetchDownlinkTransmitPowerArray_cfunc is None:
                self.RFmxLTE_ModAccFetchDownlinkTransmitPowerArray_cfunc = (
                    self._get_library_function("RFmxLTE_ModAccFetchDownlinkTransmitPowerArray")
                )
                self.RFmxLTE_ModAccFetchDownlinkTransmitPowerArray_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxLTE_ModAccFetchDownlinkTransmitPowerArray_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ModAccFetchDownlinkTransmitPowerArray_cfunc(
            vi,
            selector_string,
            timeout,
            rs_transmit_power,
            ofdm_symbol_transmit_power,
            reserved_1,
            reserved_2,
            array_size,
            actual_array_size,
        )

    def RFmxLTE_ModAccFetchEVMPerSlotTrace(
        self, vi, selector_string, timeout, x0, dx, rms_evm_per_slot, array_size, actual_array_size
    ):
        """RFmxLTE_ModAccFetchEVMPerSlotTrace."""
        with self._func_lock:
            if self.RFmxLTE_ModAccFetchEVMPerSlotTrace_cfunc is None:
                self.RFmxLTE_ModAccFetchEVMPerSlotTrace_cfunc = self._get_library_function(
                    "RFmxLTE_ModAccFetchEVMPerSlotTrace"
                )
                self.RFmxLTE_ModAccFetchEVMPerSlotTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxLTE_ModAccFetchEVMPerSlotTrace_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ModAccFetchEVMPerSlotTrace_cfunc(
            vi, selector_string, timeout, x0, dx, rms_evm_per_slot, array_size, actual_array_size
        )

    def RFmxLTE_ModAccFetchEVMPerSubcarrierTrace(
        self,
        vi,
        selector_string,
        timeout,
        x0,
        dx,
        mean_rms_evm_per_subcarrier,
        array_size,
        actual_array_size,
    ):
        """RFmxLTE_ModAccFetchEVMPerSubcarrierTrace."""
        with self._func_lock:
            if self.RFmxLTE_ModAccFetchEVMPerSubcarrierTrace_cfunc is None:
                self.RFmxLTE_ModAccFetchEVMPerSubcarrierTrace_cfunc = self._get_library_function(
                    "RFmxLTE_ModAccFetchEVMPerSubcarrierTrace"
                )
                self.RFmxLTE_ModAccFetchEVMPerSubcarrierTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxLTE_ModAccFetchEVMPerSubcarrierTrace_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ModAccFetchEVMPerSubcarrierTrace_cfunc(
            vi,
            selector_string,
            timeout,
            x0,
            dx,
            mean_rms_evm_per_subcarrier,
            array_size,
            actual_array_size,
        )

    def RFmxLTE_ModAccFetchEVMPerSymbolTrace(
        self,
        vi,
        selector_string,
        timeout,
        x0,
        dx,
        rms_evm_per_symbol,
        array_size,
        actual_array_size,
    ):
        """RFmxLTE_ModAccFetchEVMPerSymbolTrace."""
        with self._func_lock:
            if self.RFmxLTE_ModAccFetchEVMPerSymbolTrace_cfunc is None:
                self.RFmxLTE_ModAccFetchEVMPerSymbolTrace_cfunc = self._get_library_function(
                    "RFmxLTE_ModAccFetchEVMPerSymbolTrace"
                )
                self.RFmxLTE_ModAccFetchEVMPerSymbolTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxLTE_ModAccFetchEVMPerSymbolTrace_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ModAccFetchEVMPerSymbolTrace_cfunc(
            vi, selector_string, timeout, x0, dx, rms_evm_per_symbol, array_size, actual_array_size
        )

    def RFmxLTE_ModAccFetchEVMHighPerSymbolTrace(
        self,
        vi,
        selector_string,
        timeout,
        x0,
        dx,
        evm_high_per_symbol,
        array_size,
        actual_array_size,
    ):
        """RFmxLTE_ModAccFetchEVMHighPerSymbolTrace."""
        with self._func_lock:
            if self.RFmxLTE_ModAccFetchEVMHighPerSymbolTrace_cfunc is None:
                self.RFmxLTE_ModAccFetchEVMHighPerSymbolTrace_cfunc = self._get_library_function(
                    "RFmxLTE_ModAccFetchEVMHighPerSymbolTrace"
                )
                self.RFmxLTE_ModAccFetchEVMHighPerSymbolTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxLTE_ModAccFetchEVMHighPerSymbolTrace_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ModAccFetchEVMHighPerSymbolTrace_cfunc(
            vi, selector_string, timeout, x0, dx, evm_high_per_symbol, array_size, actual_array_size
        )

    def RFmxLTE_ModAccFetchMaximumEVMHighPerSymbolTrace(
        self,
        vi,
        selector_string,
        timeout,
        x0,
        dx,
        maximum_evm_high_per_symbol,
        array_size,
        actual_array_size,
    ):
        """RFmxLTE_ModAccFetchMaximumEVMHighPerSymbolTrace."""
        with self._func_lock:
            if self.RFmxLTE_ModAccFetchMaximumEVMHighPerSymbolTrace_cfunc is None:
                self.RFmxLTE_ModAccFetchMaximumEVMHighPerSymbolTrace_cfunc = (
                    self._get_library_function("RFmxLTE_ModAccFetchMaximumEVMHighPerSymbolTrace")
                )
                self.RFmxLTE_ModAccFetchMaximumEVMHighPerSymbolTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxLTE_ModAccFetchMaximumEVMHighPerSymbolTrace_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ModAccFetchMaximumEVMHighPerSymbolTrace_cfunc(
            vi,
            selector_string,
            timeout,
            x0,
            dx,
            maximum_evm_high_per_symbol,
            array_size,
            actual_array_size,
        )

    def RFmxLTE_ModAccFetchEVMLowPerSymbolTrace(
        self,
        vi,
        selector_string,
        timeout,
        x0,
        dx,
        evm_low_per_symbol,
        array_size,
        actual_array_size,
    ):
        """RFmxLTE_ModAccFetchEVMLowPerSymbolTrace."""
        with self._func_lock:
            if self.RFmxLTE_ModAccFetchEVMLowPerSymbolTrace_cfunc is None:
                self.RFmxLTE_ModAccFetchEVMLowPerSymbolTrace_cfunc = self._get_library_function(
                    "RFmxLTE_ModAccFetchEVMLowPerSymbolTrace"
                )
                self.RFmxLTE_ModAccFetchEVMLowPerSymbolTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxLTE_ModAccFetchEVMLowPerSymbolTrace_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ModAccFetchEVMLowPerSymbolTrace_cfunc(
            vi, selector_string, timeout, x0, dx, evm_low_per_symbol, array_size, actual_array_size
        )

    def RFmxLTE_ModAccFetchMaximumEVMLowPerSymbolTrace(
        self,
        vi,
        selector_string,
        timeout,
        x0,
        dx,
        maximum_evm_low_per_symbol,
        array_size,
        actual_array_size,
    ):
        """RFmxLTE_ModAccFetchMaximumEVMLowPerSymbolTrace."""
        with self._func_lock:
            if self.RFmxLTE_ModAccFetchMaximumEVMLowPerSymbolTrace_cfunc is None:
                self.RFmxLTE_ModAccFetchMaximumEVMLowPerSymbolTrace_cfunc = (
                    self._get_library_function("RFmxLTE_ModAccFetchMaximumEVMLowPerSymbolTrace")
                )
                self.RFmxLTE_ModAccFetchMaximumEVMLowPerSymbolTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxLTE_ModAccFetchMaximumEVMLowPerSymbolTrace_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ModAccFetchMaximumEVMLowPerSymbolTrace_cfunc(
            vi,
            selector_string,
            timeout,
            x0,
            dx,
            maximum_evm_low_per_symbol,
            array_size,
            actual_array_size,
        )

    def RFmxLTE_ModAccFetchInBandEmissionMarginArray(
        self, vi, selector_string, timeout, in_band_emission_margin, array_size, actual_array_size
    ):
        """RFmxLTE_ModAccFetchInBandEmissionMarginArray."""
        with self._func_lock:
            if self.RFmxLTE_ModAccFetchInBandEmissionMarginArray_cfunc is None:
                self.RFmxLTE_ModAccFetchInBandEmissionMarginArray_cfunc = (
                    self._get_library_function("RFmxLTE_ModAccFetchInBandEmissionMarginArray")
                )
                self.RFmxLTE_ModAccFetchInBandEmissionMarginArray_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxLTE_ModAccFetchInBandEmissionMarginArray_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ModAccFetchInBandEmissionMarginArray_cfunc(
            vi, selector_string, timeout, in_band_emission_margin, array_size, actual_array_size
        )

    def RFmxLTE_ModAccFetchInBandEmissionTrace(
        self,
        vi,
        selector_string,
        timeout,
        x0,
        dx,
        in_band_emission,
        in_band_emission_mask,
        array_size,
        actual_array_size,
    ):
        """RFmxLTE_ModAccFetchInBandEmissionTrace."""
        with self._func_lock:
            if self.RFmxLTE_ModAccFetchInBandEmissionTrace_cfunc is None:
                self.RFmxLTE_ModAccFetchInBandEmissionTrace_cfunc = self._get_library_function(
                    "RFmxLTE_ModAccFetchInBandEmissionTrace"
                )
                self.RFmxLTE_ModAccFetchInBandEmissionTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxLTE_ModAccFetchInBandEmissionTrace_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ModAccFetchInBandEmissionTrace_cfunc(
            vi,
            selector_string,
            timeout,
            x0,
            dx,
            in_band_emission,
            in_band_emission_mask,
            array_size,
            actual_array_size,
        )

    def RFmxLTE_ModAccFetchIQImpairmentsArray(
        self,
        vi,
        selector_string,
        timeout,
        mean_iq_origin_offset,
        mean_iq_gain_imbalance,
        mean_iq_quadrature_error,
        array_size,
        actual_array_size,
    ):
        """RFmxLTE_ModAccFetchIQImpairmentsArray."""
        with self._func_lock:
            if self.RFmxLTE_ModAccFetchIQImpairmentsArray_cfunc is None:
                self.RFmxLTE_ModAccFetchIQImpairmentsArray_cfunc = self._get_library_function(
                    "RFmxLTE_ModAccFetchIQImpairmentsArray"
                )
                self.RFmxLTE_ModAccFetchIQImpairmentsArray_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxLTE_ModAccFetchIQImpairmentsArray_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ModAccFetchIQImpairmentsArray_cfunc(
            vi,
            selector_string,
            timeout,
            mean_iq_origin_offset,
            mean_iq_gain_imbalance,
            mean_iq_quadrature_error,
            array_size,
            actual_array_size,
        )

    def RFmxLTE_ModAccFetchMaximumEVMPerSlotTrace(
        self,
        vi,
        selector_string,
        timeout,
        x0,
        dx,
        maximum_evm_per_slot,
        array_size,
        actual_array_size,
    ):
        """RFmxLTE_ModAccFetchMaximumEVMPerSlotTrace."""
        with self._func_lock:
            if self.RFmxLTE_ModAccFetchMaximumEVMPerSlotTrace_cfunc is None:
                self.RFmxLTE_ModAccFetchMaximumEVMPerSlotTrace_cfunc = self._get_library_function(
                    "RFmxLTE_ModAccFetchMaximumEVMPerSlotTrace"
                )
                self.RFmxLTE_ModAccFetchMaximumEVMPerSlotTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxLTE_ModAccFetchMaximumEVMPerSlotTrace_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ModAccFetchMaximumEVMPerSlotTrace_cfunc(
            vi,
            selector_string,
            timeout,
            x0,
            dx,
            maximum_evm_per_slot,
            array_size,
            actual_array_size,
        )

    def RFmxLTE_ModAccFetchMaximumEVMPerSubcarrierTrace(
        self,
        vi,
        selector_string,
        timeout,
        x0,
        dx,
        maximum_evm_per_subcarrier,
        array_size,
        actual_array_size,
    ):
        """RFmxLTE_ModAccFetchMaximumEVMPerSubcarrierTrace."""
        with self._func_lock:
            if self.RFmxLTE_ModAccFetchMaximumEVMPerSubcarrierTrace_cfunc is None:
                self.RFmxLTE_ModAccFetchMaximumEVMPerSubcarrierTrace_cfunc = (
                    self._get_library_function("RFmxLTE_ModAccFetchMaximumEVMPerSubcarrierTrace")
                )
                self.RFmxLTE_ModAccFetchMaximumEVMPerSubcarrierTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxLTE_ModAccFetchMaximumEVMPerSubcarrierTrace_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ModAccFetchMaximumEVMPerSubcarrierTrace_cfunc(
            vi,
            selector_string,
            timeout,
            x0,
            dx,
            maximum_evm_per_subcarrier,
            array_size,
            actual_array_size,
        )

    def RFmxLTE_ModAccFetchMaximumEVMPerSymbolTrace(
        self,
        vi,
        selector_string,
        timeout,
        x0,
        dx,
        maximum_evm_per_symbol,
        array_size,
        actual_array_size,
    ):
        """RFmxLTE_ModAccFetchMaximumEVMPerSymbolTrace."""
        with self._func_lock:
            if self.RFmxLTE_ModAccFetchMaximumEVMPerSymbolTrace_cfunc is None:
                self.RFmxLTE_ModAccFetchMaximumEVMPerSymbolTrace_cfunc = self._get_library_function(
                    "RFmxLTE_ModAccFetchMaximumEVMPerSymbolTrace"
                )
                self.RFmxLTE_ModAccFetchMaximumEVMPerSymbolTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxLTE_ModAccFetchMaximumEVMPerSymbolTrace_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ModAccFetchMaximumEVMPerSymbolTrace_cfunc(
            vi,
            selector_string,
            timeout,
            x0,
            dx,
            maximum_evm_per_symbol,
            array_size,
            actual_array_size,
        )

    def RFmxLTE_ModAccFetchMaximumMagnitudeErrorPerSymbolTrace(
        self,
        vi,
        selector_string,
        timeout,
        x0,
        dx,
        maximum_magnitude_error_per_symbol,
        array_size,
        actual_array_size,
    ):
        """RFmxLTE_ModAccFetchMaximumMagnitudeErrorPerSymbolTrace."""
        with self._func_lock:
            if self.RFmxLTE_ModAccFetchMaximumMagnitudeErrorPerSymbolTrace_cfunc is None:
                self.RFmxLTE_ModAccFetchMaximumMagnitudeErrorPerSymbolTrace_cfunc = (
                    self._get_library_function(
                        "RFmxLTE_ModAccFetchMaximumMagnitudeErrorPerSymbolTrace"
                    )
                )
                self.RFmxLTE_ModAccFetchMaximumMagnitudeErrorPerSymbolTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxLTE_ModAccFetchMaximumMagnitudeErrorPerSymbolTrace_cfunc.restype = (
                    ctypes.c_int32
                )
        return self.RFmxLTE_ModAccFetchMaximumMagnitudeErrorPerSymbolTrace_cfunc(
            vi,
            selector_string,
            timeout,
            x0,
            dx,
            maximum_magnitude_error_per_symbol,
            array_size,
            actual_array_size,
        )

    def RFmxLTE_ModAccFetchMaximumPhaseErrorPerSymbolTrace(
        self,
        vi,
        selector_string,
        timeout,
        x0,
        dx,
        maximum_phase_error_per_symbol,
        array_size,
        actual_array_size,
    ):
        """RFmxLTE_ModAccFetchMaximumPhaseErrorPerSymbolTrace."""
        with self._func_lock:
            if self.RFmxLTE_ModAccFetchMaximumPhaseErrorPerSymbolTrace_cfunc is None:
                self.RFmxLTE_ModAccFetchMaximumPhaseErrorPerSymbolTrace_cfunc = (
                    self._get_library_function("RFmxLTE_ModAccFetchMaximumPhaseErrorPerSymbolTrace")
                )
                self.RFmxLTE_ModAccFetchMaximumPhaseErrorPerSymbolTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxLTE_ModAccFetchMaximumPhaseErrorPerSymbolTrace_cfunc.restype = (
                    ctypes.c_int32
                )
        return self.RFmxLTE_ModAccFetchMaximumPhaseErrorPerSymbolTrace_cfunc(
            vi,
            selector_string,
            timeout,
            x0,
            dx,
            maximum_phase_error_per_symbol,
            array_size,
            actual_array_size,
        )

    def RFmxLTE_ModAccFetchPDSCH1024QAMConstellation(
        self, vi, selector_string, timeout, qam1024_constellation, array_size, actual_array_size
    ):
        """RFmxLTE_ModAccFetchPDSCH1024QAMConstellation."""
        with self._func_lock:
            if self.RFmxLTE_ModAccFetchPDSCH1024QAMConstellation_cfunc is None:
                self.RFmxLTE_ModAccFetchPDSCH1024QAMConstellation_cfunc = (
                    self._get_library_function("RFmxLTE_ModAccFetchPDSCH1024QAMConstellation")
                )
                self.RFmxLTE_ModAccFetchPDSCH1024QAMConstellation_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(_custom_types.ComplexSingle),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxLTE_ModAccFetchPDSCH1024QAMConstellation_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ModAccFetchPDSCH1024QAMConstellation_cfunc(
            vi, selector_string, timeout, qam1024_constellation, array_size, actual_array_size
        )

    def RFmxLTE_ModAccFetchPDSCH1024QAMEVMArray(
        self, vi, selector_string, timeout, mean_rms_1024qam_evm, array_size, actual_array_size
    ):
        """RFmxLTE_ModAccFetchPDSCH1024QAMEVMArray."""
        with self._func_lock:
            if self.RFmxLTE_ModAccFetchPDSCH1024QAMEVMArray_cfunc is None:
                self.RFmxLTE_ModAccFetchPDSCH1024QAMEVMArray_cfunc = self._get_library_function(
                    "RFmxLTE_ModAccFetchPDSCH1024QAMEVMArray"
                )
                self.RFmxLTE_ModAccFetchPDSCH1024QAMEVMArray_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxLTE_ModAccFetchPDSCH1024QAMEVMArray_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ModAccFetchPDSCH1024QAMEVMArray_cfunc(
            vi, selector_string, timeout, mean_rms_1024qam_evm, array_size, actual_array_size
        )

    def RFmxLTE_ModAccFetchPDSCH16QAMConstellation(
        self, vi, selector_string, timeout, qam16_constellation, array_size, actual_array_size
    ):
        """RFmxLTE_ModAccFetchPDSCH16QAMConstellation."""
        with self._func_lock:
            if self.RFmxLTE_ModAccFetchPDSCH16QAMConstellation_cfunc is None:
                self.RFmxLTE_ModAccFetchPDSCH16QAMConstellation_cfunc = self._get_library_function(
                    "RFmxLTE_ModAccFetchPDSCH16QAMConstellation"
                )
                self.RFmxLTE_ModAccFetchPDSCH16QAMConstellation_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(_custom_types.ComplexSingle),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxLTE_ModAccFetchPDSCH16QAMConstellation_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ModAccFetchPDSCH16QAMConstellation_cfunc(
            vi, selector_string, timeout, qam16_constellation, array_size, actual_array_size
        )

    def RFmxLTE_ModAccFetchPDSCH256QAMConstellation(
        self, vi, selector_string, timeout, qam256_constellation, array_size, actual_array_size
    ):
        """RFmxLTE_ModAccFetchPDSCH256QAMConstellation."""
        with self._func_lock:
            if self.RFmxLTE_ModAccFetchPDSCH256QAMConstellation_cfunc is None:
                self.RFmxLTE_ModAccFetchPDSCH256QAMConstellation_cfunc = self._get_library_function(
                    "RFmxLTE_ModAccFetchPDSCH256QAMConstellation"
                )
                self.RFmxLTE_ModAccFetchPDSCH256QAMConstellation_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(_custom_types.ComplexSingle),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxLTE_ModAccFetchPDSCH256QAMConstellation_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ModAccFetchPDSCH256QAMConstellation_cfunc(
            vi, selector_string, timeout, qam256_constellation, array_size, actual_array_size
        )

    def RFmxLTE_ModAccFetchPDSCH64QAMConstellation(
        self, vi, selector_string, timeout, qam64_constellation, array_size, actual_array_size
    ):
        """RFmxLTE_ModAccFetchPDSCH64QAMConstellation."""
        with self._func_lock:
            if self.RFmxLTE_ModAccFetchPDSCH64QAMConstellation_cfunc is None:
                self.RFmxLTE_ModAccFetchPDSCH64QAMConstellation_cfunc = self._get_library_function(
                    "RFmxLTE_ModAccFetchPDSCH64QAMConstellation"
                )
                self.RFmxLTE_ModAccFetchPDSCH64QAMConstellation_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(_custom_types.ComplexSingle),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxLTE_ModAccFetchPDSCH64QAMConstellation_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ModAccFetchPDSCH64QAMConstellation_cfunc(
            vi, selector_string, timeout, qam64_constellation, array_size, actual_array_size
        )

    def RFmxLTE_ModAccFetchPDSCHEVMArray(
        self,
        vi,
        selector_string,
        timeout,
        mean_rms_evm,
        mean_rms_qpsk_evm,
        mean_rms_16qam_evm,
        mean_rms_64qam_evm,
        mean_rms_256qam_evm,
        array_size,
        actual_array_size,
    ):
        """RFmxLTE_ModAccFetchPDSCHEVMArray."""
        with self._func_lock:
            if self.RFmxLTE_ModAccFetchPDSCHEVMArray_cfunc is None:
                self.RFmxLTE_ModAccFetchPDSCHEVMArray_cfunc = self._get_library_function(
                    "RFmxLTE_ModAccFetchPDSCHEVMArray"
                )
                self.RFmxLTE_ModAccFetchPDSCHEVMArray_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxLTE_ModAccFetchPDSCHEVMArray_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ModAccFetchPDSCHEVMArray_cfunc(
            vi,
            selector_string,
            timeout,
            mean_rms_evm,
            mean_rms_qpsk_evm,
            mean_rms_16qam_evm,
            mean_rms_64qam_evm,
            mean_rms_256qam_evm,
            array_size,
            actual_array_size,
        )

    def RFmxLTE_ModAccFetchPDSCHQPSKConstellation(
        self, vi, selector_string, timeout, qpsk_constellation, array_size, actual_array_size
    ):
        """RFmxLTE_ModAccFetchPDSCHQPSKConstellation."""
        with self._func_lock:
            if self.RFmxLTE_ModAccFetchPDSCHQPSKConstellation_cfunc is None:
                self.RFmxLTE_ModAccFetchPDSCHQPSKConstellation_cfunc = self._get_library_function(
                    "RFmxLTE_ModAccFetchPDSCHQPSKConstellation"
                )
                self.RFmxLTE_ModAccFetchPDSCHQPSKConstellation_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(_custom_types.ComplexSingle),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxLTE_ModAccFetchPDSCHQPSKConstellation_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ModAccFetchPDSCHQPSKConstellation_cfunc(
            vi, selector_string, timeout, qpsk_constellation, array_size, actual_array_size
        )

    def RFmxLTE_ModAccFetchPSSCHDataEVMArray(
        self,
        vi,
        selector_string,
        timeout,
        pssch_mean_rms_data_evm,
        pssch_maximum_peak_data_evm,
        array_size,
        actual_array_size,
    ):
        """RFmxLTE_ModAccFetchPSSCHDataEVMArray."""
        with self._func_lock:
            if self.RFmxLTE_ModAccFetchPSSCHDataEVMArray_cfunc is None:
                self.RFmxLTE_ModAccFetchPSSCHDataEVMArray_cfunc = self._get_library_function(
                    "RFmxLTE_ModAccFetchPSSCHDataEVMArray"
                )
                self.RFmxLTE_ModAccFetchPSSCHDataEVMArray_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxLTE_ModAccFetchPSSCHDataEVMArray_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ModAccFetchPSSCHDataEVMArray_cfunc(
            vi,
            selector_string,
            timeout,
            pssch_mean_rms_data_evm,
            pssch_maximum_peak_data_evm,
            array_size,
            actual_array_size,
        )

    def RFmxLTE_ModAccFetchPSSCHDMRSEVMArray(
        self,
        vi,
        selector_string,
        timeout,
        pssch_mean_rms_dmrs_evm,
        pssch_maximum_peak_dmrs_evm,
        array_size,
        actual_array_size,
    ):
        """RFmxLTE_ModAccFetchPSSCHDMRSEVMArray."""
        with self._func_lock:
            if self.RFmxLTE_ModAccFetchPSSCHDMRSEVMArray_cfunc is None:
                self.RFmxLTE_ModAccFetchPSSCHDMRSEVMArray_cfunc = self._get_library_function(
                    "RFmxLTE_ModAccFetchPSSCHDMRSEVMArray"
                )
                self.RFmxLTE_ModAccFetchPSSCHDMRSEVMArray_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxLTE_ModAccFetchPSSCHDMRSEVMArray_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ModAccFetchPSSCHDMRSEVMArray_cfunc(
            vi,
            selector_string,
            timeout,
            pssch_mean_rms_dmrs_evm,
            pssch_maximum_peak_dmrs_evm,
            array_size,
            actual_array_size,
        )

    def RFmxLTE_ModAccFetchPSSCHSymbolPowerArray(
        self,
        vi,
        selector_string,
        timeout,
        pssch_mean_data_power,
        pssch_mean_dmrs_power,
        array_size,
        actual_array_size,
    ):
        """RFmxLTE_ModAccFetchPSSCHSymbolPowerArray."""
        with self._func_lock:
            if self.RFmxLTE_ModAccFetchPSSCHSymbolPowerArray_cfunc is None:
                self.RFmxLTE_ModAccFetchPSSCHSymbolPowerArray_cfunc = self._get_library_function(
                    "RFmxLTE_ModAccFetchPSSCHSymbolPowerArray"
                )
                self.RFmxLTE_ModAccFetchPSSCHSymbolPowerArray_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxLTE_ModAccFetchPSSCHSymbolPowerArray_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ModAccFetchPSSCHSymbolPowerArray_cfunc(
            vi,
            selector_string,
            timeout,
            pssch_mean_data_power,
            pssch_mean_dmrs_power,
            array_size,
            actual_array_size,
        )

    def RFmxLTE_ModAccFetchPUSCHDataEVMArray(
        self,
        vi,
        selector_string,
        timeout,
        mean_rms_data_evm,
        maximum_peak_data_evm,
        array_size,
        actual_array_size,
    ):
        """RFmxLTE_ModAccFetchPUSCHDataEVMArray."""
        with self._func_lock:
            if self.RFmxLTE_ModAccFetchPUSCHDataEVMArray_cfunc is None:
                self.RFmxLTE_ModAccFetchPUSCHDataEVMArray_cfunc = self._get_library_function(
                    "RFmxLTE_ModAccFetchPUSCHDataEVMArray"
                )
                self.RFmxLTE_ModAccFetchPUSCHDataEVMArray_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxLTE_ModAccFetchPUSCHDataEVMArray_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ModAccFetchPUSCHDataEVMArray_cfunc(
            vi,
            selector_string,
            timeout,
            mean_rms_data_evm,
            maximum_peak_data_evm,
            array_size,
            actual_array_size,
        )

    def RFmxLTE_ModAccFetchPUSCHDemodulatedBits(
        self, vi, selector_string, timeout, bits, array_size, actual_array_size
    ):
        """RFmxLTE_ModAccFetchPUSCHDemodulatedBits."""
        with self._func_lock:
            if self.RFmxLTE_ModAccFetchPUSCHDemodulatedBits_cfunc is None:
                self.RFmxLTE_ModAccFetchPUSCHDemodulatedBits_cfunc = self._get_library_function(
                    "RFmxLTE_ModAccFetchPUSCHDemodulatedBits"
                )
                self.RFmxLTE_ModAccFetchPUSCHDemodulatedBits_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_int8),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxLTE_ModAccFetchPUSCHDemodulatedBits_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ModAccFetchPUSCHDemodulatedBits_cfunc(
            vi, selector_string, timeout, bits, array_size, actual_array_size
        )

    def RFmxLTE_ModAccFetchPUSCHDMRSEVMArray(
        self,
        vi,
        selector_string,
        timeout,
        mean_rms_dmrs_evm,
        maximum_peak_dmrs_evm,
        array_size,
        actual_array_size,
    ):
        """RFmxLTE_ModAccFetchPUSCHDMRSEVMArray."""
        with self._func_lock:
            if self.RFmxLTE_ModAccFetchPUSCHDMRSEVMArray_cfunc is None:
                self.RFmxLTE_ModAccFetchPUSCHDMRSEVMArray_cfunc = self._get_library_function(
                    "RFmxLTE_ModAccFetchPUSCHDMRSEVMArray"
                )
                self.RFmxLTE_ModAccFetchPUSCHDMRSEVMArray_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxLTE_ModAccFetchPUSCHDMRSEVMArray_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ModAccFetchPUSCHDMRSEVMArray_cfunc(
            vi,
            selector_string,
            timeout,
            mean_rms_dmrs_evm,
            maximum_peak_dmrs_evm,
            array_size,
            actual_array_size,
        )

    def RFmxLTE_ModAccFetchPUSCHSymbolPowerArray(
        self,
        vi,
        selector_string,
        timeout,
        pusch_mean_data_power,
        pusch_mean_dmrs_power,
        array_size,
        actual_array_size,
    ):
        """RFmxLTE_ModAccFetchPUSCHSymbolPowerArray."""
        with self._func_lock:
            if self.RFmxLTE_ModAccFetchPUSCHSymbolPowerArray_cfunc is None:
                self.RFmxLTE_ModAccFetchPUSCHSymbolPowerArray_cfunc = self._get_library_function(
                    "RFmxLTE_ModAccFetchPUSCHSymbolPowerArray"
                )
                self.RFmxLTE_ModAccFetchPUSCHSymbolPowerArray_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxLTE_ModAccFetchPUSCHSymbolPowerArray_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ModAccFetchPUSCHSymbolPowerArray_cfunc(
            vi,
            selector_string,
            timeout,
            pusch_mean_data_power,
            pusch_mean_dmrs_power,
            array_size,
            actual_array_size,
        )

    def RFmxLTE_ModAccFetchRMSMagnitudeErrorPerSymbolTrace(
        self,
        vi,
        selector_string,
        timeout,
        x0,
        dx,
        rms_magnitude_error_per_symbol,
        array_size,
        actual_array_size,
    ):
        """RFmxLTE_ModAccFetchRMSMagnitudeErrorPerSymbolTrace."""
        with self._func_lock:
            if self.RFmxLTE_ModAccFetchRMSMagnitudeErrorPerSymbolTrace_cfunc is None:
                self.RFmxLTE_ModAccFetchRMSMagnitudeErrorPerSymbolTrace_cfunc = (
                    self._get_library_function("RFmxLTE_ModAccFetchRMSMagnitudeErrorPerSymbolTrace")
                )
                self.RFmxLTE_ModAccFetchRMSMagnitudeErrorPerSymbolTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxLTE_ModAccFetchRMSMagnitudeErrorPerSymbolTrace_cfunc.restype = (
                    ctypes.c_int32
                )
        return self.RFmxLTE_ModAccFetchRMSMagnitudeErrorPerSymbolTrace_cfunc(
            vi,
            selector_string,
            timeout,
            x0,
            dx,
            rms_magnitude_error_per_symbol,
            array_size,
            actual_array_size,
        )

    def RFmxLTE_ModAccFetchRMSPhaseErrorPerSymbolTrace(
        self,
        vi,
        selector_string,
        timeout,
        x0,
        dx,
        rms_phase_error_per_symbol,
        array_size,
        actual_array_size,
    ):
        """RFmxLTE_ModAccFetchRMSPhaseErrorPerSymbolTrace."""
        with self._func_lock:
            if self.RFmxLTE_ModAccFetchRMSPhaseErrorPerSymbolTrace_cfunc is None:
                self.RFmxLTE_ModAccFetchRMSPhaseErrorPerSymbolTrace_cfunc = (
                    self._get_library_function("RFmxLTE_ModAccFetchRMSPhaseErrorPerSymbolTrace")
                )
                self.RFmxLTE_ModAccFetchRMSPhaseErrorPerSymbolTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxLTE_ModAccFetchRMSPhaseErrorPerSymbolTrace_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ModAccFetchRMSPhaseErrorPerSymbolTrace_cfunc(
            vi,
            selector_string,
            timeout,
            x0,
            dx,
            rms_phase_error_per_symbol,
            array_size,
            actual_array_size,
        )

    def RFmxLTE_ModAccFetchSpectralFlatnessArray(
        self,
        vi,
        selector_string,
        timeout,
        range1_maximum_to_range1_minimum,
        range2_maximum_to_range2_minimum,
        range1_maximum_to_range2_minimum,
        range2_maximum_to_range1_minimum,
        array_size,
        actual_array_size,
    ):
        """RFmxLTE_ModAccFetchSpectralFlatnessArray."""
        with self._func_lock:
            if self.RFmxLTE_ModAccFetchSpectralFlatnessArray_cfunc is None:
                self.RFmxLTE_ModAccFetchSpectralFlatnessArray_cfunc = self._get_library_function(
                    "RFmxLTE_ModAccFetchSpectralFlatnessArray"
                )
                self.RFmxLTE_ModAccFetchSpectralFlatnessArray_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxLTE_ModAccFetchSpectralFlatnessArray_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ModAccFetchSpectralFlatnessArray_cfunc(
            vi,
            selector_string,
            timeout,
            range1_maximum_to_range1_minimum,
            range2_maximum_to_range2_minimum,
            range1_maximum_to_range2_minimum,
            range2_maximum_to_range1_minimum,
            array_size,
            actual_array_size,
        )

    def RFmxLTE_ModAccFetchSRSConstellation(
        self, vi, selector_string, timeout, srs_constellation, array_size, actual_array_size
    ):
        """RFmxLTE_ModAccFetchSRSConstellation."""
        with self._func_lock:
            if self.RFmxLTE_ModAccFetchSRSConstellation_cfunc is None:
                self.RFmxLTE_ModAccFetchSRSConstellation_cfunc = self._get_library_function(
                    "RFmxLTE_ModAccFetchSRSConstellation"
                )
                self.RFmxLTE_ModAccFetchSRSConstellation_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(_custom_types.ComplexSingle),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxLTE_ModAccFetchSRSConstellation_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ModAccFetchSRSConstellation_cfunc(
            vi, selector_string, timeout, srs_constellation, array_size, actual_array_size
        )

    def RFmxLTE_ModAccFetchSRSEVMArray(
        self,
        vi,
        selector_string,
        timeout,
        mean_rms_srs_evm,
        mean_srs_power,
        array_size,
        actual_array_size,
    ):
        """RFmxLTE_ModAccFetchSRSEVMArray."""
        with self._func_lock:
            if self.RFmxLTE_ModAccFetchSRSEVMArray_cfunc is None:
                self.RFmxLTE_ModAccFetchSRSEVMArray_cfunc = self._get_library_function(
                    "RFmxLTE_ModAccFetchSRSEVMArray"
                )
                self.RFmxLTE_ModAccFetchSRSEVMArray_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxLTE_ModAccFetchSRSEVMArray_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ModAccFetchSRSEVMArray_cfunc(
            vi,
            selector_string,
            timeout,
            mean_rms_srs_evm,
            mean_srs_power,
            array_size,
            actual_array_size,
        )

    def RFmxLTE_ModAccFetchSubblockInBandEmissionTrace(
        self,
        vi,
        selector_string,
        timeout,
        subblock_in_band_emission,
        subblock_in_band_emission_mask,
        subblock_in_band_emission_rb_indices,
        array_size,
        actual_array_size,
    ):
        """RFmxLTE_ModAccFetchSubblockInBandEmissionTrace."""
        with self._func_lock:
            if self.RFmxLTE_ModAccFetchSubblockInBandEmissionTrace_cfunc is None:
                self.RFmxLTE_ModAccFetchSubblockInBandEmissionTrace_cfunc = (
                    self._get_library_function("RFmxLTE_ModAccFetchSubblockInBandEmissionTrace")
                )
                self.RFmxLTE_ModAccFetchSubblockInBandEmissionTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxLTE_ModAccFetchSubblockInBandEmissionTrace_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ModAccFetchSubblockInBandEmissionTrace_cfunc(
            vi,
            selector_string,
            timeout,
            subblock_in_band_emission,
            subblock_in_band_emission_mask,
            subblock_in_band_emission_rb_indices,
            array_size,
            actual_array_size,
        )

    def RFmxLTE_ModAccFetchSynchronizationSignalConstellation(
        self,
        vi,
        selector_string,
        timeout,
        sss_constellation,
        pss_constellation,
        array_size,
        actual_array_size,
    ):
        """RFmxLTE_ModAccFetchSynchronizationSignalConstellation."""
        with self._func_lock:
            if self.RFmxLTE_ModAccFetchSynchronizationSignalConstellation_cfunc is None:
                self.RFmxLTE_ModAccFetchSynchronizationSignalConstellation_cfunc = (
                    self._get_library_function(
                        "RFmxLTE_ModAccFetchSynchronizationSignalConstellation"
                    )
                )
                self.RFmxLTE_ModAccFetchSynchronizationSignalConstellation_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(_custom_types.ComplexSingle),
                    ctypes.POINTER(_custom_types.ComplexSingle),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxLTE_ModAccFetchSynchronizationSignalConstellation_cfunc.restype = (
                    ctypes.c_int32
                )
        return self.RFmxLTE_ModAccFetchSynchronizationSignalConstellation_cfunc(
            vi,
            selector_string,
            timeout,
            sss_constellation,
            pss_constellation,
            array_size,
            actual_array_size,
        )

    def RFmxLTE_ModAccFetchSynchronizationSignalEVMArray(
        self,
        vi,
        selector_string,
        timeout,
        mean_rms_pss_evm,
        mean_rms_sss_evm,
        array_size,
        actual_array_size,
    ):
        """RFmxLTE_ModAccFetchSynchronizationSignalEVMArray."""
        with self._func_lock:
            if self.RFmxLTE_ModAccFetchSynchronizationSignalEVMArray_cfunc is None:
                self.RFmxLTE_ModAccFetchSynchronizationSignalEVMArray_cfunc = (
                    self._get_library_function("RFmxLTE_ModAccFetchSynchronizationSignalEVMArray")
                )
                self.RFmxLTE_ModAccFetchSynchronizationSignalEVMArray_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxLTE_ModAccFetchSynchronizationSignalEVMArray_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ModAccFetchSynchronizationSignalEVMArray_cfunc(
            vi,
            selector_string,
            timeout,
            mean_rms_pss_evm,
            mean_rms_sss_evm,
            array_size,
            actual_array_size,
        )

    def RFmxLTE_ModAccFetchMaximumFrequencyErrorPerSlotTrace(
        self,
        vi,
        selector_string,
        timeout,
        x0,
        dx,
        maximum_frequency_error_per_slot,
        array_size,
        actual_array_size,
    ):
        """RFmxLTE_ModAccFetchMaximumFrequencyErrorPerSlotTrace."""
        with self._func_lock:
            if self.RFmxLTE_ModAccFetchMaximumFrequencyErrorPerSlotTrace_cfunc is None:
                self.RFmxLTE_ModAccFetchMaximumFrequencyErrorPerSlotTrace_cfunc = (
                    self._get_library_function(
                        "RFmxLTE_ModAccFetchMaximumFrequencyErrorPerSlotTrace"
                    )
                )
                self.RFmxLTE_ModAccFetchMaximumFrequencyErrorPerSlotTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxLTE_ModAccFetchMaximumFrequencyErrorPerSlotTrace_cfunc.restype = (
                    ctypes.c_int32
                )
        return self.RFmxLTE_ModAccFetchMaximumFrequencyErrorPerSlotTrace_cfunc(
            vi,
            selector_string,
            timeout,
            x0,
            dx,
            maximum_frequency_error_per_slot,
            array_size,
            actual_array_size,
        )

    def RFmxLTE_ModAccFetchNPDSCHQPSKConstellation(
        self, vi, selector_string, timeout, qpsk_constellation, array_size, actual_array_size
    ):
        """RFmxLTE_ModAccFetchNPDSCHQPSKConstellation."""
        with self._func_lock:
            if self.RFmxLTE_ModAccFetchNPDSCHQPSKConstellation_cfunc is None:
                self.RFmxLTE_ModAccFetchNPDSCHQPSKConstellation_cfunc = self._get_library_function(
                    "RFmxLTE_ModAccFetchNPDSCHQPSKConstellation"
                )
                self.RFmxLTE_ModAccFetchNPDSCHQPSKConstellation_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(_custom_types.ComplexSingle),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxLTE_ModAccFetchNPDSCHQPSKConstellation_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ModAccFetchNPDSCHQPSKConstellation_cfunc(
            vi, selector_string, timeout, qpsk_constellation, array_size, actual_array_size
        )

    def RFmxLTE_ModAccFetchNRSConstellation(
        self, vi, selector_string, timeout, nrs_constellation, array_size, actual_array_size
    ):
        """RFmxLTE_ModAccFetchNRSConstellation."""
        with self._func_lock:
            if self.RFmxLTE_ModAccFetchNRSConstellation_cfunc is None:
                self.RFmxLTE_ModAccFetchNRSConstellation_cfunc = self._get_library_function(
                    "RFmxLTE_ModAccFetchNRSConstellation"
                )
                self.RFmxLTE_ModAccFetchNRSConstellation_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(_custom_types.ComplexSingle),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxLTE_ModAccFetchNRSConstellation_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ModAccFetchNRSConstellation_cfunc(
            vi, selector_string, timeout, nrs_constellation, array_size, actual_array_size
        )

    def RFmxLTE_OBWFetchSpectrum(
        self, vi, selector_string, timeout, x0, dx, spectrum, array_size, actual_array_size
    ):
        """RFmxLTE_OBWFetchSpectrum."""
        with self._func_lock:
            if self.RFmxLTE_OBWFetchSpectrum_cfunc is None:
                self.RFmxLTE_OBWFetchSpectrum_cfunc = self._get_library_function(
                    "RFmxLTE_OBWFetchSpectrum"
                )
                self.RFmxLTE_OBWFetchSpectrum_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxLTE_OBWFetchSpectrum_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_OBWFetchSpectrum_cfunc(
            vi, selector_string, timeout, x0, dx, spectrum, array_size, actual_array_size
        )

    def RFmxLTE_SEMFetchComponentCarrierMeasurementArray(
        self,
        vi,
        selector_string,
        timeout,
        absolute_integrated_power,
        relative_integrated_power,
        array_size,
        actual_array_size,
    ):
        """RFmxLTE_SEMFetchComponentCarrierMeasurementArray."""
        with self._func_lock:
            if self.RFmxLTE_SEMFetchComponentCarrierMeasurementArray_cfunc is None:
                self.RFmxLTE_SEMFetchComponentCarrierMeasurementArray_cfunc = (
                    self._get_library_function("RFmxLTE_SEMFetchComponentCarrierMeasurementArray")
                )
                self.RFmxLTE_SEMFetchComponentCarrierMeasurementArray_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxLTE_SEMFetchComponentCarrierMeasurementArray_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_SEMFetchComponentCarrierMeasurementArray_cfunc(
            vi,
            selector_string,
            timeout,
            absolute_integrated_power,
            relative_integrated_power,
            array_size,
            actual_array_size,
        )

    def RFmxLTE_SEMFetchLowerOffsetMarginArray(
        self,
        vi,
        selector_string,
        timeout,
        measurement_status,
        margin,
        margin_frequency,
        margin_absolute_power,
        margin_relative_power,
        array_size,
        actual_array_size,
    ):
        """RFmxLTE_SEMFetchLowerOffsetMarginArray."""
        with self._func_lock:
            if self.RFmxLTE_SEMFetchLowerOffsetMarginArray_cfunc is None:
                self.RFmxLTE_SEMFetchLowerOffsetMarginArray_cfunc = self._get_library_function(
                    "RFmxLTE_SEMFetchLowerOffsetMarginArray"
                )
                self.RFmxLTE_SEMFetchLowerOffsetMarginArray_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_int32),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxLTE_SEMFetchLowerOffsetMarginArray_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_SEMFetchLowerOffsetMarginArray_cfunc(
            vi,
            selector_string,
            timeout,
            measurement_status,
            margin,
            margin_frequency,
            margin_absolute_power,
            margin_relative_power,
            array_size,
            actual_array_size,
        )

    def RFmxLTE_SEMFetchLowerOffsetPowerArray(
        self,
        vi,
        selector_string,
        timeout,
        absolute_integrated_power,
        relative_integrated_power,
        absolute_peak_power,
        peak_frequency,
        relative_peak_power,
        array_size,
        actual_array_size,
    ):
        """RFmxLTE_SEMFetchLowerOffsetPowerArray."""
        with self._func_lock:
            if self.RFmxLTE_SEMFetchLowerOffsetPowerArray_cfunc is None:
                self.RFmxLTE_SEMFetchLowerOffsetPowerArray_cfunc = self._get_library_function(
                    "RFmxLTE_SEMFetchLowerOffsetPowerArray"
                )
                self.RFmxLTE_SEMFetchLowerOffsetPowerArray_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxLTE_SEMFetchLowerOffsetPowerArray_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_SEMFetchLowerOffsetPowerArray_cfunc(
            vi,
            selector_string,
            timeout,
            absolute_integrated_power,
            relative_integrated_power,
            absolute_peak_power,
            peak_frequency,
            relative_peak_power,
            array_size,
            actual_array_size,
        )

    def RFmxLTE_SEMFetchSpectrum(
        self,
        vi,
        selector_string,
        timeout,
        x0,
        dx,
        spectrum,
        composite_mask,
        array_size,
        actual_array_size,
    ):
        """RFmxLTE_SEMFetchSpectrum."""
        with self._func_lock:
            if self.RFmxLTE_SEMFetchSpectrum_cfunc is None:
                self.RFmxLTE_SEMFetchSpectrum_cfunc = self._get_library_function(
                    "RFmxLTE_SEMFetchSpectrum"
                )
                self.RFmxLTE_SEMFetchSpectrum_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxLTE_SEMFetchSpectrum_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_SEMFetchSpectrum_cfunc(
            vi,
            selector_string,
            timeout,
            x0,
            dx,
            spectrum,
            composite_mask,
            array_size,
            actual_array_size,
        )

    def RFmxLTE_SEMFetchUpperOffsetMarginArray(
        self,
        vi,
        selector_string,
        timeout,
        measurement_status,
        margin,
        margin_frequency,
        margin_absolute_power,
        margin_relative_power,
        array_size,
        actual_array_size,
    ):
        """RFmxLTE_SEMFetchUpperOffsetMarginArray."""
        with self._func_lock:
            if self.RFmxLTE_SEMFetchUpperOffsetMarginArray_cfunc is None:
                self.RFmxLTE_SEMFetchUpperOffsetMarginArray_cfunc = self._get_library_function(
                    "RFmxLTE_SEMFetchUpperOffsetMarginArray"
                )
                self.RFmxLTE_SEMFetchUpperOffsetMarginArray_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_int32),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxLTE_SEMFetchUpperOffsetMarginArray_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_SEMFetchUpperOffsetMarginArray_cfunc(
            vi,
            selector_string,
            timeout,
            measurement_status,
            margin,
            margin_frequency,
            margin_absolute_power,
            margin_relative_power,
            array_size,
            actual_array_size,
        )

    def RFmxLTE_SEMFetchUpperOffsetPowerArray(
        self,
        vi,
        selector_string,
        timeout,
        absolute_integrated_power,
        relative_integrated_power,
        absolute_peak_power,
        peak_frequency,
        relative_peak_power,
        array_size,
        actual_array_size,
    ):
        """RFmxLTE_SEMFetchUpperOffsetPowerArray."""
        with self._func_lock:
            if self.RFmxLTE_SEMFetchUpperOffsetPowerArray_cfunc is None:
                self.RFmxLTE_SEMFetchUpperOffsetPowerArray_cfunc = self._get_library_function(
                    "RFmxLTE_SEMFetchUpperOffsetPowerArray"
                )
                self.RFmxLTE_SEMFetchUpperOffsetPowerArray_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxLTE_SEMFetchUpperOffsetPowerArray_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_SEMFetchUpperOffsetPowerArray_cfunc(
            vi,
            selector_string,
            timeout,
            absolute_integrated_power,
            relative_integrated_power,
            absolute_peak_power,
            peak_frequency,
            relative_peak_power,
            array_size,
            actual_array_size,
        )

    def RFmxLTE_PVTFetchMeasurementArray(
        self,
        vi,
        selector_string,
        timeout,
        measurement_status,
        mean_absolute_off_power_before,
        mean_absolute_off_power_after,
        mean_absolute_on_power,
        burst_width,
        array_size,
        actual_array_size,
    ):
        """RFmxLTE_PVTFetchMeasurementArray."""
        with self._func_lock:
            if self.RFmxLTE_PVTFetchMeasurementArray_cfunc is None:
                self.RFmxLTE_PVTFetchMeasurementArray_cfunc = self._get_library_function(
                    "RFmxLTE_PVTFetchMeasurementArray"
                )
                self.RFmxLTE_PVTFetchMeasurementArray_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_int32),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxLTE_PVTFetchMeasurementArray_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_PVTFetchMeasurementArray_cfunc(
            vi,
            selector_string,
            timeout,
            measurement_status,
            mean_absolute_off_power_before,
            mean_absolute_off_power_after,
            mean_absolute_on_power,
            burst_width,
            array_size,
            actual_array_size,
        )

    def RFmxLTE_PVTFetchSignalPowerTrace(
        self,
        vi,
        selector_string,
        timeout,
        x0,
        dx,
        signal_power,
        absolute_limit,
        array_size,
        actual_array_size,
    ):
        """RFmxLTE_PVTFetchSignalPowerTrace."""
        with self._func_lock:
            if self.RFmxLTE_PVTFetchSignalPowerTrace_cfunc is None:
                self.RFmxLTE_PVTFetchSignalPowerTrace_cfunc = self._get_library_function(
                    "RFmxLTE_PVTFetchSignalPowerTrace"
                )
                self.RFmxLTE_PVTFetchSignalPowerTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxLTE_PVTFetchSignalPowerTrace_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_PVTFetchSignalPowerTrace_cfunc(
            vi,
            selector_string,
            timeout,
            x0,
            dx,
            signal_power,
            absolute_limit,
            array_size,
            actual_array_size,
        )

    def RFmxLTE_SlotPhaseFetchMaximumPhaseDiscontinuityArray(
        self,
        vi,
        selector_string,
        timeout,
        maximum_phase_discontinuity,
        array_size,
        actual_array_size,
    ):
        """RFmxLTE_SlotPhaseFetchMaximumPhaseDiscontinuityArray."""
        with self._func_lock:
            if self.RFmxLTE_SlotPhaseFetchMaximumPhaseDiscontinuityArray_cfunc is None:
                self.RFmxLTE_SlotPhaseFetchMaximumPhaseDiscontinuityArray_cfunc = (
                    self._get_library_function(
                        "RFmxLTE_SlotPhaseFetchMaximumPhaseDiscontinuityArray"
                    )
                )
                self.RFmxLTE_SlotPhaseFetchMaximumPhaseDiscontinuityArray_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxLTE_SlotPhaseFetchMaximumPhaseDiscontinuityArray_cfunc.restype = (
                    ctypes.c_int32
                )
        return self.RFmxLTE_SlotPhaseFetchMaximumPhaseDiscontinuityArray_cfunc(
            vi, selector_string, timeout, maximum_phase_discontinuity, array_size, actual_array_size
        )

    def RFmxLTE_SlotPhaseFetchPhaseDiscontinuities(
        self, vi, selector_string, timeout, slot_phase_discontinuity, array_size, actual_array_size
    ):
        """RFmxLTE_SlotPhaseFetchPhaseDiscontinuities."""
        with self._func_lock:
            if self.RFmxLTE_SlotPhaseFetchPhaseDiscontinuities_cfunc is None:
                self.RFmxLTE_SlotPhaseFetchPhaseDiscontinuities_cfunc = self._get_library_function(
                    "RFmxLTE_SlotPhaseFetchPhaseDiscontinuities"
                )
                self.RFmxLTE_SlotPhaseFetchPhaseDiscontinuities_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxLTE_SlotPhaseFetchPhaseDiscontinuities_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_SlotPhaseFetchPhaseDiscontinuities_cfunc(
            vi, selector_string, timeout, slot_phase_discontinuity, array_size, actual_array_size
        )

    def RFmxLTE_SlotPhaseFetchSamplePhaseErrorLinearFitTrace(
        self,
        vi,
        selector_string,
        timeout,
        x0,
        dx,
        sample_phase_error_linear_fit,
        array_size,
        actual_array_size,
    ):
        """RFmxLTE_SlotPhaseFetchSamplePhaseErrorLinearFitTrace."""
        with self._func_lock:
            if self.RFmxLTE_SlotPhaseFetchSamplePhaseErrorLinearFitTrace_cfunc is None:
                self.RFmxLTE_SlotPhaseFetchSamplePhaseErrorLinearFitTrace_cfunc = (
                    self._get_library_function(
                        "RFmxLTE_SlotPhaseFetchSamplePhaseErrorLinearFitTrace"
                    )
                )
                self.RFmxLTE_SlotPhaseFetchSamplePhaseErrorLinearFitTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxLTE_SlotPhaseFetchSamplePhaseErrorLinearFitTrace_cfunc.restype = (
                    ctypes.c_int32
                )
        return self.RFmxLTE_SlotPhaseFetchSamplePhaseErrorLinearFitTrace_cfunc(
            vi,
            selector_string,
            timeout,
            x0,
            dx,
            sample_phase_error_linear_fit,
            array_size,
            actual_array_size,
        )

    def RFmxLTE_SlotPhaseFetchSamplePhaseError(
        self,
        vi,
        selector_string,
        timeout,
        x0,
        dx,
        sample_phase_error,
        array_size,
        actual_array_size,
    ):
        """RFmxLTE_SlotPhaseFetchSamplePhaseError."""
        with self._func_lock:
            if self.RFmxLTE_SlotPhaseFetchSamplePhaseError_cfunc is None:
                self.RFmxLTE_SlotPhaseFetchSamplePhaseError_cfunc = self._get_library_function(
                    "RFmxLTE_SlotPhaseFetchSamplePhaseError"
                )
                self.RFmxLTE_SlotPhaseFetchSamplePhaseError_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxLTE_SlotPhaseFetchSamplePhaseError_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_SlotPhaseFetchSamplePhaseError_cfunc(
            vi, selector_string, timeout, x0, dx, sample_phase_error, array_size, actual_array_size
        )

    def RFmxLTE_SlotPowerFetchPowers(
        self,
        vi,
        selector_string,
        timeout,
        subframe_power,
        subframe_power_delta,
        array_size,
        actual_array_size,
    ):
        """RFmxLTE_SlotPowerFetchPowers."""
        with self._func_lock:
            if self.RFmxLTE_SlotPowerFetchPowers_cfunc is None:
                self.RFmxLTE_SlotPowerFetchPowers_cfunc = self._get_library_function(
                    "RFmxLTE_SlotPowerFetchPowers"
                )
                self.RFmxLTE_SlotPowerFetchPowers_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxLTE_SlotPowerFetchPowers_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_SlotPowerFetchPowers_cfunc(
            vi,
            selector_string,
            timeout,
            subframe_power,
            subframe_power_delta,
            array_size,
            actual_array_size,
        )

    def RFmxLTE_TXPFetchPowerTrace(
        self, vi, selector_string, timeout, x0, dx, power, array_size, actual_array_size
    ):
        """RFmxLTE_TXPFetchPowerTrace."""
        with self._func_lock:
            if self.RFmxLTE_TXPFetchPowerTrace_cfunc is None:
                self.RFmxLTE_TXPFetchPowerTrace_cfunc = self._get_library_function(
                    "RFmxLTE_TXPFetchPowerTrace"
                )
                self.RFmxLTE_TXPFetchPowerTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxLTE_TXPFetchPowerTrace_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_TXPFetchPowerTrace_cfunc(
            vi, selector_string, timeout, x0, dx, power, array_size, actual_array_size
        )

    def RFmxLTE_CloneSignalConfiguration(self, vi, old_signal_name, new_signal_name):
        """RFmxLTE_CloneSignalConfiguration."""
        with self._func_lock:
            if self.RFmxLTE_CloneSignalConfiguration_cfunc is None:
                self.RFmxLTE_CloneSignalConfiguration_cfunc = self._get_library_function(
                    "RFmxLTE_CloneSignalConfiguration"
                )
                self.RFmxLTE_CloneSignalConfiguration_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.POINTER(ctypes.c_char),
                ]
                self.RFmxLTE_CloneSignalConfiguration_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_CloneSignalConfiguration_cfunc(vi, old_signal_name, new_signal_name)

    def RFmxLTE_DeleteSignalConfiguration(self, vi, signal_name):
        """RFmxLTE_DeleteSignalConfiguration."""
        with self._func_lock:
            if self.RFmxLTE_DeleteSignalConfiguration_cfunc is None:
                self.RFmxLTE_DeleteSignalConfiguration_cfunc = self._get_library_function(
                    "RFmxLTE_DeleteSignalConfiguration"
                )
                self.RFmxLTE_DeleteSignalConfiguration_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                ]
                self.RFmxLTE_DeleteSignalConfiguration_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_DeleteSignalConfiguration_cfunc(vi, signal_name)

    def RFmxLTE_SendSoftwareEdgeTrigger(self, vi):
        """RFmxLTE_SendSoftwareEdgeTrigger."""
        with self._func_lock:
            if self.RFmxLTE_SendSoftwareEdgeTrigger_cfunc is None:
                self.RFmxLTE_SendSoftwareEdgeTrigger_cfunc = self._get_library_function(
                    "RFmxLTE_SendSoftwareEdgeTrigger"
                )
                self.RFmxLTE_SendSoftwareEdgeTrigger_cfunc.argtypes = [ctypes.c_uint32]
                self.RFmxLTE_SendSoftwareEdgeTrigger_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_SendSoftwareEdgeTrigger_cfunc(vi)

    def RFmxLTE_GetAllNamedResultNames(
        self,
        vi,
        selector_string,
        result_names,
        result_names_buffer_size,
        actual_result_names_size,
        default_result_exists,
    ):
        """RFmxLTE_GetAllNamedResultNames."""
        with self._func_lock:
            if self.RFmxLTE_GetAllNamedResultNames_cfunc is None:
                self.RFmxLTE_GetAllNamedResultNames_cfunc = self._get_library_function(
                    "RFmxLTE_GetAllNamedResultNames"
                )
                self.RFmxLTE_GetAllNamedResultNames_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxLTE_GetAllNamedResultNames_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_GetAllNamedResultNames_cfunc(
            vi,
            selector_string,
            result_names,
            result_names_buffer_size,
            actual_result_names_size,
            default_result_exists,
        )

    def RFmxLTE_ClearNoiseCalibrationDatabase(self, vi, selector_string):
        """RFmxLTE_ClearNoiseCalibrationDatabase."""
        with self._func_lock:
            if self.RFmxLTE_ClearNoiseCalibrationDatabase_cfunc is None:
                self.RFmxLTE_ClearNoiseCalibrationDatabase_cfunc = self._get_library_function(
                    "RFmxLTE_ClearNoiseCalibrationDatabase"
                )
                self.RFmxLTE_ClearNoiseCalibrationDatabase_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                ]
                self.RFmxLTE_ClearNoiseCalibrationDatabase_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ClearNoiseCalibrationDatabase_cfunc(vi, selector_string)

    def RFmxLTE_AnalyzeIQ1Waveform(
        self, vi, selector_string, result_name, x0, dx, iq, array_size, reset, reserved
    ):
        """RFmxLTE_AnalyzeIQ1Waveform."""
        with self._func_lock:
            if self.RFmxLTE_AnalyzeIQ1Waveform_cfunc is None:
                self.RFmxLTE_AnalyzeIQ1Waveform_cfunc = self._get_library_function(
                    "RFmxLTE_AnalyzeIQ1Waveform"
                )
                self.RFmxLTE_AnalyzeIQ1Waveform_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.c_double,
                    ctypes.POINTER(_custom_types.ComplexSingle),
                    ctypes.c_int32,
                    ctypes.c_int32,
                    ctypes.c_int64,
                ]
                self.RFmxLTE_AnalyzeIQ1Waveform_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_AnalyzeIQ1Waveform_cfunc(
            vi, selector_string, result_name, x0, dx, iq, array_size, reset, reserved
        )

    def RFmxLTE_AnalyzeSpectrum1Waveform(
        self, vi, selector_string, result_name, x0, dx, spectrum, array_size, reset, reserved
    ):
        """RFmxLTE_AnalyzeSpectrum1Waveform."""
        with self._func_lock:
            if self.RFmxLTE_AnalyzeSpectrum1Waveform_cfunc is None:
                self.RFmxLTE_AnalyzeSpectrum1Waveform_cfunc = self._get_library_function(
                    "RFmxLTE_AnalyzeSpectrum1Waveform"
                )
                self.RFmxLTE_AnalyzeSpectrum1Waveform_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.c_int32,
                    ctypes.c_int64,
                ]
                self.RFmxLTE_AnalyzeSpectrum1Waveform_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_AnalyzeSpectrum1Waveform_cfunc(
            vi, selector_string, result_name, x0, dx, spectrum, array_size, reset, reserved
        )

    def RFmxLTE_CfgDownlinkAutoChannelDetection(
        self,
        vi,
        selector_string,
        auto_pdsch_channel_detection_enabled,
        auto_control_channel_power_detection_enabled,
        auto_pcfich_cfi_detection_enabled,
        reserved,
    ):
        """RFmxLTE_CfgDownlinkAutoChannelDetection."""
        with self._func_lock:
            if self.RFmxLTE_CfgDownlinkAutoChannelDetection_cfunc is None:
                self.RFmxLTE_CfgDownlinkAutoChannelDetection_cfunc = self._get_library_function(
                    "RFmxLTE_CfgDownlinkAutoChannelDetection"
                )
                self.RFmxLTE_CfgDownlinkAutoChannelDetection_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                    ctypes.c_int32,
                    ctypes.c_int32,
                    ctypes.c_int32,
                ]
                self.RFmxLTE_CfgDownlinkAutoChannelDetection_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_CfgDownlinkAutoChannelDetection_cfunc(
            vi,
            selector_string,
            auto_pdsch_channel_detection_enabled,
            auto_control_channel_power_detection_enabled,
            auto_pcfich_cfi_detection_enabled,
            reserved,
        )

    def RFmxLTE_ModAccFetchPUSCHConstellationTrace(
        self,
        vi,
        selector_string,
        timeout,
        data_constellation,
        data_array_size,
        data_actual_array_size,
        dmrs_constellation,
        dmrs_array_size,
        dmrs_actual_array_size,
    ):
        """RFmxLTE_ModAccFetchPUSCHConstellationTrace."""
        with self._func_lock:
            if self.RFmxLTE_ModAccFetchPUSCHConstellationTrace_cfunc is None:
                self.RFmxLTE_ModAccFetchPUSCHConstellationTrace_cfunc = self._get_library_function(
                    "RFmxLTE_ModAccFetchPUSCHConstellationTrace"
                )
                self.RFmxLTE_ModAccFetchPUSCHConstellationTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(_custom_types.ComplexSingle),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                    ctypes.POINTER(_custom_types.ComplexSingle),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxLTE_ModAccFetchPUSCHConstellationTrace_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ModAccFetchPUSCHConstellationTrace_cfunc(
            vi,
            selector_string,
            timeout,
            data_constellation,
            data_array_size,
            data_actual_array_size,
            dmrs_constellation,
            dmrs_array_size,
            dmrs_actual_array_size,
        )

    def RFmxLTE_ModAccFetchNPUSCHConstellationTrace(
        self,
        vi,
        selector_string,
        timeout,
        data_constellation,
        data_array_size,
        data_actual_array_size,
        dmrs_constellation,
        dmrs_array_size,
        dmrs_actual_array_size,
    ):
        """RFmxLTE_ModAccFetchNPUSCHConstellationTrace."""
        with self._func_lock:
            if self.RFmxLTE_ModAccFetchNPUSCHConstellationTrace_cfunc is None:
                self.RFmxLTE_ModAccFetchNPUSCHConstellationTrace_cfunc = self._get_library_function(
                    "RFmxLTE_ModAccFetchNPUSCHConstellationTrace"
                )
                self.RFmxLTE_ModAccFetchNPUSCHConstellationTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(_custom_types.ComplexSingle),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                    ctypes.POINTER(_custom_types.ComplexSingle),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxLTE_ModAccFetchNPUSCHConstellationTrace_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ModAccFetchNPUSCHConstellationTrace_cfunc(
            vi,
            selector_string,
            timeout,
            data_constellation,
            data_array_size,
            data_actual_array_size,
            dmrs_constellation,
            dmrs_array_size,
            dmrs_actual_array_size,
        )

    def RFmxLTE_ModAccFetchNBSynchronizationSignalConstellation(
        self,
        vi,
        selector_string,
        timeout,
        nsss_constellation,
        npss_constellation,
        array_size,
        actual_array_size,
    ):
        """RFmxLTE_ModAccFetchNBSynchronizationSignalConstellation."""
        with self._func_lock:
            if self.RFmxLTE_ModAccFetchNBSynchronizationSignalConstellation_cfunc is None:
                self.RFmxLTE_ModAccFetchNBSynchronizationSignalConstellation_cfunc = (
                    self._get_library_function(
                        "RFmxLTE_ModAccFetchNBSynchronizationSignalConstellation"
                    )
                )
                self.RFmxLTE_ModAccFetchNBSynchronizationSignalConstellation_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(_custom_types.ComplexSingle),
                    ctypes.POINTER(_custom_types.ComplexSingle),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxLTE_ModAccFetchNBSynchronizationSignalConstellation_cfunc.restype = (
                    ctypes.c_int32
                )
        return self.RFmxLTE_ModAccFetchNBSynchronizationSignalConstellation_cfunc(
            vi,
            selector_string,
            timeout,
            nsss_constellation,
            npss_constellation,
            array_size,
            actual_array_size,
        )

    def RFmxLTE_ModAccFetchSpectralFlatnessTrace(
        self,
        vi,
        selector_string,
        timeout,
        x0,
        dx,
        spectral_flatness,
        spectral_flatness_lower_mask,
        spectral_flatness_upper_mask,
        array_size,
        actual_array_size,
    ):
        """RFmxLTE_ModAccFetchSpectralFlatnessTrace."""
        with self._func_lock:
            if self.RFmxLTE_ModAccFetchSpectralFlatnessTrace_cfunc is None:
                self.RFmxLTE_ModAccFetchSpectralFlatnessTrace_cfunc = self._get_library_function(
                    "RFmxLTE_ModAccFetchSpectralFlatnessTrace"
                )
                self.RFmxLTE_ModAccFetchSpectralFlatnessTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxLTE_ModAccFetchSpectralFlatnessTrace_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ModAccFetchSpectralFlatnessTrace_cfunc(
            vi,
            selector_string,
            timeout,
            x0,
            dx,
            spectral_flatness,
            spectral_flatness_lower_mask,
            spectral_flatness_upper_mask,
            array_size,
            actual_array_size,
        )

    def RFmxLTE_ModAccFetchPSSCHConstellationTrace(
        self,
        vi,
        selector_string,
        timeout,
        data_constellation,
        dmrs_constellation,
        array_size,
        actual_array_size,
    ):
        """RFmxLTE_ModAccFetchPSSCHConstellationTrace."""
        with self._func_lock:
            if self.RFmxLTE_ModAccFetchPSSCHConstellationTrace_cfunc is None:
                self.RFmxLTE_ModAccFetchPSSCHConstellationTrace_cfunc = self._get_library_function(
                    "RFmxLTE_ModAccFetchPSSCHConstellationTrace"
                )
                self.RFmxLTE_ModAccFetchPSSCHConstellationTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(_custom_types.ComplexSingle),
                    ctypes.POINTER(_custom_types.ComplexSingle),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxLTE_ModAccFetchPSSCHConstellationTrace_cfunc.restype = ctypes.c_int32
        return self.RFmxLTE_ModAccFetchPSSCHConstellationTrace_cfunc(
            vi,
            selector_string,
            timeout,
            data_constellation,
            dmrs_constellation,
            array_size,
            actual_array_size,
        )
