# Copyright (C) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See LICENSE in project root for information.


import sys
if sys.version >= '3':
    basestring = str

from pyspark import SparkContext, SQLContext
from pyspark.sql import DataFrame
from pyspark.ml.param.shared import *
from pyspark import keyword_only
from pyspark.ml.util import JavaMLReadable, JavaMLWritable
from synapse.ml.core.platform import running_on_synapse_internal
from synapse.ml.core.serialize.java_params_patch import *
from pyspark.ml.wrapper import JavaTransformer, JavaEstimator, JavaModel
from pyspark.ml.evaluation import JavaEvaluator
from pyspark.ml.common import inherit_doc
from synapse.ml.core.schema.Utils import *
from pyspark.ml.param import TypeConverters
from synapse.ml.core.schema.TypeConversionUtils import generateTypeConverter, complexTypeConverter


@inherit_doc
class _ONNXModel(ComplexParamsMixin, JavaMLReadable, JavaMLWritable, JavaTransformer):
    """
    Args:
        argMaxDict (dict): A map between output dataframe columns, where the value column will be computed from taking the argmax of the key column. This can be used to convert probability output to predicted label.
        deviceType (str): Specify a device type the model inference runs on. Supported types are: CPU or CUDA.If not specified, auto detection will be used.
        feedDict (dict):  Provide a map from CNTK/ONNX model input variable names (keys) to column names of the input dataframe (values)
        fetchDict (dict): Provide a map from column names of the output dataframe (keys) to CNTK/ONNX model output variable names (values)
        miniBatcher (object): Minibatcher to use
        modelPayload (list): Array of bytes containing the serialized ONNX model.
        optimizationLevel (str): Specify the optimization level for the ONNX graph optimizations. Details at https://onnxruntime.ai/docs/resources/graph-optimizations.html#graph-optimization-levels. Supported values are: NO_OPT; BASIC_OPT; EXTENDED_OPT; ALL_OPT. Default: ALL_OPT.
        softMaxDict (dict): A map between output dataframe columns, where the value column will be computed from taking the softmax of the key column. If the 'rawPrediction' column contains logits outputs, then one can set softMaxDict to `Map("rawPrediction" -> "probability")` to obtain the probability outputs.
    """

    argMaxDict = Param(Params._dummy(), "argMaxDict", "A map between output dataframe columns, where the value column will be computed from taking the argmax of the key column. This can be used to convert probability output to predicted label.")
    
    deviceType = Param(Params._dummy(), "deviceType", "Specify a device type the model inference runs on. Supported types are: CPU or CUDA.If not specified, auto detection will be used.", typeConverter=TypeConverters.toString)
    
    feedDict = Param(Params._dummy(), "feedDict", " Provide a map from CNTK/ONNX model input variable names (keys) to column names of the input dataframe (values)")
    
    fetchDict = Param(Params._dummy(), "fetchDict", "Provide a map from column names of the output dataframe (keys) to CNTK/ONNX model output variable names (values)")
    
    miniBatcher = Param(Params._dummy(), "miniBatcher", "Minibatcher to use")
    
    modelPayload = Param(Params._dummy(), "modelPayload", "Array of bytes containing the serialized ONNX model.")
    
    optimizationLevel = Param(Params._dummy(), "optimizationLevel", "Specify the optimization level for the ONNX graph optimizations. Details at https://onnxruntime.ai/docs/resources/graph-optimizations.html#graph-optimization-levels. Supported values are: NO_OPT; BASIC_OPT; EXTENDED_OPT; ALL_OPT. Default: ALL_OPT.", typeConverter=TypeConverters.toString)
    
    softMaxDict = Param(Params._dummy(), "softMaxDict", "A map between output dataframe columns, where the value column will be computed from taking the softmax of the key column. If the 'rawPrediction' column contains logits outputs, then one can set softMaxDict to `Map(\"rawPrediction\" -> \"probability\")` to obtain the probability outputs.")

    
    @keyword_only
    def __init__(
        self,
        java_obj=None,
        argMaxDict=None,
        deviceType=None,
        feedDict=None,
        fetchDict=None,
        miniBatcher=None,
        modelPayload=None,
        optimizationLevel="ALL_OPT",
        softMaxDict=None
        ):
        super(_ONNXModel, self).__init__()
        if java_obj is None:
            self._java_obj = self._new_java_obj("com.microsoft.azure.synapse.ml.onnx.ONNXModel", self.uid)
        else:
            self._java_obj = java_obj
        self._setDefault(optimizationLevel="ALL_OPT")
        if hasattr(self, "_input_kwargs"):
            kwargs = self._input_kwargs
        else:
            kwargs = self.__init__._input_kwargs
    
        if java_obj is None:
            for k,v in kwargs.items():
                if v is not None:
                    getattr(self, "set" + k[0].upper() + k[1:])(v)

    @keyword_only
    def setParams(
        self,
        argMaxDict=None,
        deviceType=None,
        feedDict=None,
        fetchDict=None,
        miniBatcher=None,
        modelPayload=None,
        optimizationLevel="ALL_OPT",
        softMaxDict=None
        ):
        """
        Set the (keyword only) parameters
        """
        if hasattr(self, "_input_kwargs"):
            kwargs = self._input_kwargs
        else:
            kwargs = self.__init__._input_kwargs
        return self._set(**kwargs)

    @classmethod
    def read(cls):
        """ Returns an MLReader instance for this class. """
        return JavaMMLReader(cls)

    @staticmethod
    def getJavaPackage():
        """ Returns package name String. """
        return "com.microsoft.azure.synapse.ml.onnx.ONNXModel"

    @staticmethod
    def _from_java(java_stage):
        module_name=_ONNXModel.__module__
        module_name=module_name.rsplit(".", 1)[0] + ".ONNXModel"
        return from_java(java_stage, module_name)

    def setArgMaxDict(self, value):
        """
        Args:
            argMaxDict: A map between output dataframe columns, where the value column will be computed from taking the argmax of the key column. This can be used to convert probability output to predicted label.
        """
        self._set(argMaxDict=value)
        return self
    
    def setDeviceType(self, value):
        """
        Args:
            deviceType: Specify a device type the model inference runs on. Supported types are: CPU or CUDA.If not specified, auto detection will be used.
        """
        self._set(deviceType=value)
        return self
    
    def setFeedDict(self, value):
        """
        Args:
            feedDict:  Provide a map from CNTK/ONNX model input variable names (keys) to column names of the input dataframe (values)
        """
        self._set(feedDict=value)
        return self
    
    def setFetchDict(self, value):
        """
        Args:
            fetchDict: Provide a map from column names of the output dataframe (keys) to CNTK/ONNX model output variable names (values)
        """
        self._set(fetchDict=value)
        return self
    
    def setMiniBatcher(self, value):
        """
        Args:
            miniBatcher: Minibatcher to use
        """
        self._set(miniBatcher=value)
        return self
    
    def setModelPayload(self, value):
        """
        Args:
            modelPayload: Array of bytes containing the serialized ONNX model.
        """
        self._set(modelPayload=value)
        return self
    
    def setOptimizationLevel(self, value):
        """
        Args:
            optimizationLevel: Specify the optimization level for the ONNX graph optimizations. Details at https://onnxruntime.ai/docs/resources/graph-optimizations.html#graph-optimization-levels. Supported values are: NO_OPT; BASIC_OPT; EXTENDED_OPT; ALL_OPT. Default: ALL_OPT.
        """
        self._set(optimizationLevel=value)
        return self
    
    def setSoftMaxDict(self, value):
        """
        Args:
            softMaxDict: A map between output dataframe columns, where the value column will be computed from taking the softmax of the key column. If the 'rawPrediction' column contains logits outputs, then one can set softMaxDict to `Map("rawPrediction" -> "probability")` to obtain the probability outputs.
        """
        self._set(softMaxDict=value)
        return self

    
    def getArgMaxDict(self):
        """
        Returns:
            argMaxDict: A map between output dataframe columns, where the value column will be computed from taking the argmax of the key column. This can be used to convert probability output to predicted label.
        """
        return self.getOrDefault(self.argMaxDict)
    
    
    def getDeviceType(self):
        """
        Returns:
            deviceType: Specify a device type the model inference runs on. Supported types are: CPU or CUDA.If not specified, auto detection will be used.
        """
        return self.getOrDefault(self.deviceType)
    
    
    def getFeedDict(self):
        """
        Returns:
            feedDict:  Provide a map from CNTK/ONNX model input variable names (keys) to column names of the input dataframe (values)
        """
        return self.getOrDefault(self.feedDict)
    
    
    def getFetchDict(self):
        """
        Returns:
            fetchDict: Provide a map from column names of the output dataframe (keys) to CNTK/ONNX model output variable names (values)
        """
        return self.getOrDefault(self.fetchDict)
    
    
    def getMiniBatcher(self):
        """
        Returns:
            miniBatcher: Minibatcher to use
        """
        return JavaParams._from_java(self._java_obj.getMiniBatcher())
    
    
    def getModelPayload(self):
        """
        Returns:
            modelPayload: Array of bytes containing the serialized ONNX model.
        """
        return self.getOrDefault(self.modelPayload)
    
    
    def getOptimizationLevel(self):
        """
        Returns:
            optimizationLevel: Specify the optimization level for the ONNX graph optimizations. Details at https://onnxruntime.ai/docs/resources/graph-optimizations.html#graph-optimization-levels. Supported values are: NO_OPT; BASIC_OPT; EXTENDED_OPT; ALL_OPT. Default: ALL_OPT.
        """
        return self.getOrDefault(self.optimizationLevel)
    
    
    def getSoftMaxDict(self):
        """
        Returns:
            softMaxDict: A map between output dataframe columns, where the value column will be computed from taking the softmax of the key column. If the 'rawPrediction' column contains logits outputs, then one can set softMaxDict to `Map("rawPrediction" -> "probability")` to obtain the probability outputs.
        """
        return self.getOrDefault(self.softMaxDict)

    

    
        