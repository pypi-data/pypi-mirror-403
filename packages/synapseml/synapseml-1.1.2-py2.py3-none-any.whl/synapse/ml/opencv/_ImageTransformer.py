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
class _ImageTransformer(ComplexParamsMixin, JavaMLReadable, JavaMLWritable, JavaTransformer):
    """
    Args:
        autoConvertToColor (bool): Whether to automatically convert black and white images to color
        colorScaleFactor (float): The scale factor for color values. Used for normalization. The color values will be multiplied with the scale factor.
        ignoreDecodingErrors (bool): Whether to throw on decoding errors or just return null
        inputCol (str): The name of the input column
        normalizeMean (list): The mean value to use for normalization for each channel. The length of the array must match the number of channels of the input image.
        normalizeStd (list): The standard deviation to use for normalization for each channel. The length of the array must match the number of channels of the input image.
        outputCol (str): The name of the output column
        stages (object): Image transformation stages
        tensorChannelOrder (str): The color channel order of the output channels. Valid values are RGB and GBR. Default: RGB.
        tensorElementType (object): The element data type for the output tensor. Only used when toTensor is set to true. Valid values are DoubleType or FloatType. Default value: FloatType.
        toTensor (bool): Convert output image to tensor in the shape of (C * H * W)
    """

    autoConvertToColor = Param(Params._dummy(), "autoConvertToColor", "Whether to automatically convert black and white images to color", typeConverter=TypeConverters.toBoolean)
    
    colorScaleFactor = Param(Params._dummy(), "colorScaleFactor", "The scale factor for color values. Used for normalization. The color values will be multiplied with the scale factor.", typeConverter=TypeConverters.toFloat)
    
    ignoreDecodingErrors = Param(Params._dummy(), "ignoreDecodingErrors", "Whether to throw on decoding errors or just return null", typeConverter=TypeConverters.toBoolean)
    
    inputCol = Param(Params._dummy(), "inputCol", "The name of the input column", typeConverter=TypeConverters.toString)
    
    normalizeMean = Param(Params._dummy(), "normalizeMean", "The mean value to use for normalization for each channel. The length of the array must match the number of channels of the input image.", typeConverter=TypeConverters.toListFloat)
    
    normalizeStd = Param(Params._dummy(), "normalizeStd", "The standard deviation to use for normalization for each channel. The length of the array must match the number of channels of the input image.", typeConverter=TypeConverters.toListFloat)
    
    outputCol = Param(Params._dummy(), "outputCol", "The name of the output column", typeConverter=TypeConverters.toString)
    
    stages = Param(Params._dummy(), "stages", "Image transformation stages")
    
    tensorChannelOrder = Param(Params._dummy(), "tensorChannelOrder", "The color channel order of the output channels. Valid values are RGB and GBR. Default: RGB.", typeConverter=TypeConverters.toString)
    
    tensorElementType = Param(Params._dummy(), "tensorElementType", "The element data type for the output tensor. Only used when toTensor is set to true. Valid values are DoubleType or FloatType. Default value: FloatType.")
    
    toTensor = Param(Params._dummy(), "toTensor", "Convert output image to tensor in the shape of (C * H * W)", typeConverter=TypeConverters.toBoolean)

    
    @keyword_only
    def __init__(
        self,
        java_obj=None,
        autoConvertToColor=False,
        colorScaleFactor=None,
        ignoreDecodingErrors=False,
        inputCol="image",
        normalizeMean=None,
        normalizeStd=None,
        outputCol="ImageTransformer_3487d00ec3ae_output",
        stages=None,
        tensorChannelOrder="RGB",
        tensorElementType=None,
        toTensor=False
        ):
        super(_ImageTransformer, self).__init__()
        if java_obj is None:
            self._java_obj = self._new_java_obj("com.microsoft.azure.synapse.ml.opencv.ImageTransformer", self.uid)
        else:
            self._java_obj = java_obj
        self._setDefault(autoConvertToColor=False)
        self._setDefault(ignoreDecodingErrors=False)
        self._setDefault(inputCol="image")
        self._setDefault(outputCol="ImageTransformer_3487d00ec3ae_output")
        self._setDefault(tensorChannelOrder="RGB")
        self._setDefault(toTensor=False)
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
        autoConvertToColor=False,
        colorScaleFactor=None,
        ignoreDecodingErrors=False,
        inputCol="image",
        normalizeMean=None,
        normalizeStd=None,
        outputCol="ImageTransformer_3487d00ec3ae_output",
        stages=None,
        tensorChannelOrder="RGB",
        tensorElementType=None,
        toTensor=False
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
        return "com.microsoft.azure.synapse.ml.opencv.ImageTransformer"

    @staticmethod
    def _from_java(java_stage):
        module_name=_ImageTransformer.__module__
        module_name=module_name.rsplit(".", 1)[0] + ".ImageTransformer"
        return from_java(java_stage, module_name)

    def setAutoConvertToColor(self, value):
        """
        Args:
            autoConvertToColor: Whether to automatically convert black and white images to color
        """
        self._set(autoConvertToColor=value)
        return self
    
    def setColorScaleFactor(self, value):
        """
        Args:
            colorScaleFactor: The scale factor for color values. Used for normalization. The color values will be multiplied with the scale factor.
        """
        self._set(colorScaleFactor=value)
        return self
    
    def setIgnoreDecodingErrors(self, value):
        """
        Args:
            ignoreDecodingErrors: Whether to throw on decoding errors or just return null
        """
        self._set(ignoreDecodingErrors=value)
        return self
    
    def setInputCol(self, value):
        """
        Args:
            inputCol: The name of the input column
        """
        self._set(inputCol=value)
        return self
    
    def setNormalizeMean(self, value):
        """
        Args:
            normalizeMean: The mean value to use for normalization for each channel. The length of the array must match the number of channels of the input image.
        """
        self._set(normalizeMean=value)
        return self
    
    def setNormalizeStd(self, value):
        """
        Args:
            normalizeStd: The standard deviation to use for normalization for each channel. The length of the array must match the number of channels of the input image.
        """
        self._set(normalizeStd=value)
        return self
    
    def setOutputCol(self, value):
        """
        Args:
            outputCol: The name of the output column
        """
        self._set(outputCol=value)
        return self
    
    def setStages(self, value):
        """
        Args:
            stages: Image transformation stages
        """
        self._set(stages=value)
        return self
    
    def setTensorChannelOrder(self, value):
        """
        Args:
            tensorChannelOrder: The color channel order of the output channels. Valid values are RGB and GBR. Default: RGB.
        """
        self._set(tensorChannelOrder=value)
        return self
    
    def setTensorElementType(self, value):
        """
        Args:
            tensorElementType: The element data type for the output tensor. Only used when toTensor is set to true. Valid values are DoubleType or FloatType. Default value: FloatType.
        """
        self._set(tensorElementType=value)
        return self
    
    def setToTensor(self, value):
        """
        Args:
            toTensor: Convert output image to tensor in the shape of (C * H * W)
        """
        self._set(toTensor=value)
        return self

    
    def getAutoConvertToColor(self):
        """
        Returns:
            autoConvertToColor: Whether to automatically convert black and white images to color
        """
        return self.getOrDefault(self.autoConvertToColor)
    
    
    def getColorScaleFactor(self):
        """
        Returns:
            colorScaleFactor: The scale factor for color values. Used for normalization. The color values will be multiplied with the scale factor.
        """
        return self.getOrDefault(self.colorScaleFactor)
    
    
    def getIgnoreDecodingErrors(self):
        """
        Returns:
            ignoreDecodingErrors: Whether to throw on decoding errors or just return null
        """
        return self.getOrDefault(self.ignoreDecodingErrors)
    
    
    def getInputCol(self):
        """
        Returns:
            inputCol: The name of the input column
        """
        return self.getOrDefault(self.inputCol)
    
    
    def getNormalizeMean(self):
        """
        Returns:
            normalizeMean: The mean value to use for normalization for each channel. The length of the array must match the number of channels of the input image.
        """
        return self.getOrDefault(self.normalizeMean)
    
    
    def getNormalizeStd(self):
        """
        Returns:
            normalizeStd: The standard deviation to use for normalization for each channel. The length of the array must match the number of channels of the input image.
        """
        return self.getOrDefault(self.normalizeStd)
    
    
    def getOutputCol(self):
        """
        Returns:
            outputCol: The name of the output column
        """
        return self.getOrDefault(self.outputCol)
    
    
    def getStages(self):
        """
        Returns:
            stages: Image transformation stages
        """
        return self.getOrDefault(self.stages)
    
    
    def getTensorChannelOrder(self):
        """
        Returns:
            tensorChannelOrder: The color channel order of the output channels. Valid values are RGB and GBR. Default: RGB.
        """
        return self.getOrDefault(self.tensorChannelOrder)
    
    
    def getTensorElementType(self):
        """
        Returns:
            tensorElementType: The element data type for the output tensor. Only used when toTensor is set to true. Valid values are DoubleType or FloatType. Default value: FloatType.
        """
        return self.getOrDefault(self.tensorElementType)
    
    
    def getToTensor(self):
        """
        Returns:
            toTensor: Convert output image to tensor in the shape of (C * H * W)
        """
        return self.getOrDefault(self.toTensor)

    

    
        