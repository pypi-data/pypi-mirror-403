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
class _ImageFeaturizer(ComplexParamsMixin, JavaMLReadable, JavaMLWritable, JavaTransformer):
    """
    Args:
        autoConvertToColor (bool): Whether to automatically convert black and white images to color. default = true
        channelNormalizationMeans (list): Normalization means for color channels
        channelNormalizationStds (list): Normalization std's for color channels
        colorScaleFactor (float): Color scale factor
        dropNa (bool): Whether to drop na values before mapping
        featureTensorName (str): the name of the tensor to include in the fetch dict
        headless (bool): whether to use the feature tensor or the output tensor
        ignoreDecodingErrors (bool): Whether to throw on decoding errors or just return None
        imageHeight (int): Size required by model
        imageTensorName (str): the name of the tensor to include in the fetch dict
        imageWidth (int): Size required by model
        inputCol (str): The name of the input column
        onnxModel (object): The internal ONNX model used in the featurizer
        outputCol (str): The name of the output column
        outputTensorName (str): the name of the tensor to include in the fetch dict
    """

    autoConvertToColor = Param(Params._dummy(), "autoConvertToColor", "Whether to automatically convert black and white images to color. default = true", typeConverter=TypeConverters.toBoolean)
    
    channelNormalizationMeans = Param(Params._dummy(), "channelNormalizationMeans", "Normalization means for color channels", typeConverter=TypeConverters.toListFloat)
    
    channelNormalizationStds = Param(Params._dummy(), "channelNormalizationStds", "Normalization std's for color channels", typeConverter=TypeConverters.toListFloat)
    
    colorScaleFactor = Param(Params._dummy(), "colorScaleFactor", "Color scale factor", typeConverter=TypeConverters.toFloat)
    
    dropNa = Param(Params._dummy(), "dropNa", "Whether to drop na values before mapping", typeConverter=TypeConverters.toBoolean)
    
    featureTensorName = Param(Params._dummy(), "featureTensorName", "the name of the tensor to include in the fetch dict", typeConverter=TypeConverters.toString)
    
    headless = Param(Params._dummy(), "headless", "whether to use the feature tensor or the output tensor", typeConverter=TypeConverters.toBoolean)
    
    ignoreDecodingErrors = Param(Params._dummy(), "ignoreDecodingErrors", "Whether to throw on decoding errors or just return None", typeConverter=TypeConverters.toBoolean)
    
    imageHeight = Param(Params._dummy(), "imageHeight", "Size required by model", typeConverter=TypeConverters.toInt)
    
    imageTensorName = Param(Params._dummy(), "imageTensorName", "the name of the tensor to include in the fetch dict", typeConverter=TypeConverters.toString)
    
    imageWidth = Param(Params._dummy(), "imageWidth", "Size required by model", typeConverter=TypeConverters.toInt)
    
    inputCol = Param(Params._dummy(), "inputCol", "The name of the input column", typeConverter=TypeConverters.toString)
    
    onnxModel = Param(Params._dummy(), "onnxModel", "The internal ONNX model used in the featurizer")
    
    outputCol = Param(Params._dummy(), "outputCol", "The name of the output column", typeConverter=TypeConverters.toString)
    
    outputTensorName = Param(Params._dummy(), "outputTensorName", "the name of the tensor to include in the fetch dict", typeConverter=TypeConverters.toString)

    
    @keyword_only
    def __init__(
        self,
        java_obj=None,
        autoConvertToColor=True,
        channelNormalizationMeans=[0.485,0.456,0.406],
        channelNormalizationStds=[0.229,0.224,0.225],
        colorScaleFactor=0.00392156862745098,
        dropNa=True,
        featureTensorName=None,
        headless=True,
        ignoreDecodingErrors=False,
        imageHeight=None,
        imageTensorName=None,
        imageWidth=None,
        inputCol=None,
        onnxModel=None,
        outputCol="ImageFeaturizer_ebff79e123b4_output",
        outputTensorName=""
        ):
        super(_ImageFeaturizer, self).__init__()
        if java_obj is None:
            self._java_obj = self._new_java_obj("com.microsoft.azure.synapse.ml.onnx.ImageFeaturizer", self.uid)
        else:
            self._java_obj = java_obj
        self._setDefault(autoConvertToColor=True)
        self._setDefault(channelNormalizationMeans=[0.485,0.456,0.406])
        self._setDefault(channelNormalizationStds=[0.229,0.224,0.225])
        self._setDefault(colorScaleFactor=0.00392156862745098)
        self._setDefault(dropNa=True)
        self._setDefault(headless=True)
        self._setDefault(ignoreDecodingErrors=False)
        self._setDefault(outputCol="ImageFeaturizer_ebff79e123b4_output")
        self._setDefault(outputTensorName="")
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
        autoConvertToColor=True,
        channelNormalizationMeans=[0.485,0.456,0.406],
        channelNormalizationStds=[0.229,0.224,0.225],
        colorScaleFactor=0.00392156862745098,
        dropNa=True,
        featureTensorName=None,
        headless=True,
        ignoreDecodingErrors=False,
        imageHeight=None,
        imageTensorName=None,
        imageWidth=None,
        inputCol=None,
        onnxModel=None,
        outputCol="ImageFeaturizer_ebff79e123b4_output",
        outputTensorName=""
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
        return "com.microsoft.azure.synapse.ml.onnx.ImageFeaturizer"

    @staticmethod
    def _from_java(java_stage):
        module_name=_ImageFeaturizer.__module__
        module_name=module_name.rsplit(".", 1)[0] + ".ImageFeaturizer"
        return from_java(java_stage, module_name)

    def setAutoConvertToColor(self, value):
        """
        Args:
            autoConvertToColor: Whether to automatically convert black and white images to color. default = true
        """
        self._set(autoConvertToColor=value)
        return self
    
    def setChannelNormalizationMeans(self, value):
        """
        Args:
            channelNormalizationMeans: Normalization means for color channels
        """
        self._set(channelNormalizationMeans=value)
        return self
    
    def setChannelNormalizationStds(self, value):
        """
        Args:
            channelNormalizationStds: Normalization std's for color channels
        """
        self._set(channelNormalizationStds=value)
        return self
    
    def setColorScaleFactor(self, value):
        """
        Args:
            colorScaleFactor: Color scale factor
        """
        self._set(colorScaleFactor=value)
        return self
    
    def setDropNa(self, value):
        """
        Args:
            dropNa: Whether to drop na values before mapping
        """
        self._set(dropNa=value)
        return self
    
    def setFeatureTensorName(self, value):
        """
        Args:
            featureTensorName: the name of the tensor to include in the fetch dict
        """
        self._set(featureTensorName=value)
        return self
    
    def setHeadless(self, value):
        """
        Args:
            headless: whether to use the feature tensor or the output tensor
        """
        self._set(headless=value)
        return self
    
    def setIgnoreDecodingErrors(self, value):
        """
        Args:
            ignoreDecodingErrors: Whether to throw on decoding errors or just return None
        """
        self._set(ignoreDecodingErrors=value)
        return self
    
    def setImageHeight(self, value):
        """
        Args:
            imageHeight: Size required by model
        """
        self._set(imageHeight=value)
        return self
    
    def setImageTensorName(self, value):
        """
        Args:
            imageTensorName: the name of the tensor to include in the fetch dict
        """
        self._set(imageTensorName=value)
        return self
    
    def setImageWidth(self, value):
        """
        Args:
            imageWidth: Size required by model
        """
        self._set(imageWidth=value)
        return self
    
    def setInputCol(self, value):
        """
        Args:
            inputCol: The name of the input column
        """
        self._set(inputCol=value)
        return self
    
    def setOnnxModel(self, value):
        """
        Args:
            onnxModel: The internal ONNX model used in the featurizer
        """
        self._set(onnxModel=value)
        return self
    
    def setOutputCol(self, value):
        """
        Args:
            outputCol: The name of the output column
        """
        self._set(outputCol=value)
        return self
    
    def setOutputTensorName(self, value):
        """
        Args:
            outputTensorName: the name of the tensor to include in the fetch dict
        """
        self._set(outputTensorName=value)
        return self

    
    def getAutoConvertToColor(self):
        """
        Returns:
            autoConvertToColor: Whether to automatically convert black and white images to color. default = true
        """
        return self.getOrDefault(self.autoConvertToColor)
    
    
    def getChannelNormalizationMeans(self):
        """
        Returns:
            channelNormalizationMeans: Normalization means for color channels
        """
        return self.getOrDefault(self.channelNormalizationMeans)
    
    
    def getChannelNormalizationStds(self):
        """
        Returns:
            channelNormalizationStds: Normalization std's for color channels
        """
        return self.getOrDefault(self.channelNormalizationStds)
    
    
    def getColorScaleFactor(self):
        """
        Returns:
            colorScaleFactor: Color scale factor
        """
        return self.getOrDefault(self.colorScaleFactor)
    
    
    def getDropNa(self):
        """
        Returns:
            dropNa: Whether to drop na values before mapping
        """
        return self.getOrDefault(self.dropNa)
    
    
    def getFeatureTensorName(self):
        """
        Returns:
            featureTensorName: the name of the tensor to include in the fetch dict
        """
        return self.getOrDefault(self.featureTensorName)
    
    
    def getHeadless(self):
        """
        Returns:
            headless: whether to use the feature tensor or the output tensor
        """
        return self.getOrDefault(self.headless)
    
    
    def getIgnoreDecodingErrors(self):
        """
        Returns:
            ignoreDecodingErrors: Whether to throw on decoding errors or just return None
        """
        return self.getOrDefault(self.ignoreDecodingErrors)
    
    
    def getImageHeight(self):
        """
        Returns:
            imageHeight: Size required by model
        """
        return self.getOrDefault(self.imageHeight)
    
    
    def getImageTensorName(self):
        """
        Returns:
            imageTensorName: the name of the tensor to include in the fetch dict
        """
        return self.getOrDefault(self.imageTensorName)
    
    
    def getImageWidth(self):
        """
        Returns:
            imageWidth: Size required by model
        """
        return self.getOrDefault(self.imageWidth)
    
    
    def getInputCol(self):
        """
        Returns:
            inputCol: The name of the input column
        """
        return self.getOrDefault(self.inputCol)
    
    
    def getOnnxModel(self):
        """
        Returns:
            onnxModel: The internal ONNX model used in the featurizer
        """
        return JavaParams._from_java(self._java_obj.getOnnxModel())
    
    
    def getOutputCol(self):
        """
        Returns:
            outputCol: The name of the output column
        """
        return self.getOrDefault(self.outputCol)
    
    
    def getOutputTensorName(self):
        """
        Returns:
            outputTensorName: the name of the tensor to include in the fetch dict
        """
        return self.getOrDefault(self.outputTensorName)

    

    
        