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
class UnrollBinaryImage(ComplexParamsMixin, JavaMLReadable, JavaMLWritable, JavaTransformer):
    """
    Args:
        height (int): the width of the image
        inputCol (str): The name of the input column
        nChannels (int): the number of channels of the target image
        outputCol (str): The name of the output column
        width (int): the width of the image
    """

    height = Param(Params._dummy(), "height", "the width of the image", typeConverter=TypeConverters.toInt)
    
    inputCol = Param(Params._dummy(), "inputCol", "The name of the input column", typeConverter=TypeConverters.toString)
    
    nChannels = Param(Params._dummy(), "nChannels", "the number of channels of the target image", typeConverter=TypeConverters.toInt)
    
    outputCol = Param(Params._dummy(), "outputCol", "The name of the output column", typeConverter=TypeConverters.toString)
    
    width = Param(Params._dummy(), "width", "the width of the image", typeConverter=TypeConverters.toInt)

    
    @keyword_only
    def __init__(
        self,
        java_obj=None,
        height=None,
        inputCol="image",
        nChannels=None,
        outputCol="UnrollImage_8a99d031d34f_output",
        width=None
        ):
        super(UnrollBinaryImage, self).__init__()
        if java_obj is None:
            self._java_obj = self._new_java_obj("com.microsoft.azure.synapse.ml.image.UnrollBinaryImage", self.uid)
        else:
            self._java_obj = java_obj
        self._setDefault(inputCol="image")
        self._setDefault(outputCol="UnrollImage_8a99d031d34f_output")
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
        height=None,
        inputCol="image",
        nChannels=None,
        outputCol="UnrollImage_8a99d031d34f_output",
        width=None
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
        return "com.microsoft.azure.synapse.ml.image.UnrollBinaryImage"

    @staticmethod
    def _from_java(java_stage):
        module_name=UnrollBinaryImage.__module__
        module_name=module_name.rsplit(".", 1)[0] + ".UnrollBinaryImage"
        return from_java(java_stage, module_name)

    def setHeight(self, value):
        """
        Args:
            height: the width of the image
        """
        self._set(height=value)
        return self
    
    def setInputCol(self, value):
        """
        Args:
            inputCol: The name of the input column
        """
        self._set(inputCol=value)
        return self
    
    def setNChannels(self, value):
        """
        Args:
            nChannels: the number of channels of the target image
        """
        self._set(nChannels=value)
        return self
    
    def setOutputCol(self, value):
        """
        Args:
            outputCol: The name of the output column
        """
        self._set(outputCol=value)
        return self
    
    def setWidth(self, value):
        """
        Args:
            width: the width of the image
        """
        self._set(width=value)
        return self

    
    def getHeight(self):
        """
        Returns:
            height: the width of the image
        """
        return self.getOrDefault(self.height)
    
    
    def getInputCol(self):
        """
        Returns:
            inputCol: The name of the input column
        """
        return self.getOrDefault(self.inputCol)
    
    
    def getNChannels(self):
        """
        Returns:
            nChannels: the number of channels of the target image
        """
        return self.getOrDefault(self.nChannels)
    
    
    def getOutputCol(self):
        """
        Returns:
            outputCol: The name of the output column
        """
        return self.getOrDefault(self.outputCol)
    
    
    def getWidth(self):
        """
        Returns:
            width: the width of the image
        """
        return self.getOrDefault(self.width)

    

    
        