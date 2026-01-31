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
class SuperpixelTransformer(ComplexParamsMixin, JavaMLReadable, JavaMLWritable, JavaTransformer):
    """
    Args:
        cellSize (float): Number that controls the size of the superpixels
        inputCol (str): The name of the input column
        modifier (float): Controls the trade-off spatial and color distance
        outputCol (str): The name of the output column
    """

    cellSize = Param(Params._dummy(), "cellSize", "Number that controls the size of the superpixels", typeConverter=TypeConverters.toFloat)
    
    inputCol = Param(Params._dummy(), "inputCol", "The name of the input column", typeConverter=TypeConverters.toString)
    
    modifier = Param(Params._dummy(), "modifier", "Controls the trade-off spatial and color distance", typeConverter=TypeConverters.toFloat)
    
    outputCol = Param(Params._dummy(), "outputCol", "The name of the output column", typeConverter=TypeConverters.toString)

    
    @keyword_only
    def __init__(
        self,
        java_obj=None,
        cellSize=16.0,
        inputCol=None,
        modifier=130.0,
        outputCol="SuperpixelTransformer_f9343db65aeb_output"
        ):
        super(SuperpixelTransformer, self).__init__()
        if java_obj is None:
            self._java_obj = self._new_java_obj("com.microsoft.azure.synapse.ml.image.SuperpixelTransformer", self.uid)
        else:
            self._java_obj = java_obj
        self._setDefault(cellSize=16.0)
        self._setDefault(modifier=130.0)
        self._setDefault(outputCol="SuperpixelTransformer_f9343db65aeb_output")
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
        cellSize=16.0,
        inputCol=None,
        modifier=130.0,
        outputCol="SuperpixelTransformer_f9343db65aeb_output"
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
        return "com.microsoft.azure.synapse.ml.image.SuperpixelTransformer"

    @staticmethod
    def _from_java(java_stage):
        module_name=SuperpixelTransformer.__module__
        module_name=module_name.rsplit(".", 1)[0] + ".SuperpixelTransformer"
        return from_java(java_stage, module_name)

    def setCellSize(self, value):
        """
        Args:
            cellSize: Number that controls the size of the superpixels
        """
        self._set(cellSize=value)
        return self
    
    def setInputCol(self, value):
        """
        Args:
            inputCol: The name of the input column
        """
        self._set(inputCol=value)
        return self
    
    def setModifier(self, value):
        """
        Args:
            modifier: Controls the trade-off spatial and color distance
        """
        self._set(modifier=value)
        return self
    
    def setOutputCol(self, value):
        """
        Args:
            outputCol: The name of the output column
        """
        self._set(outputCol=value)
        return self

    
    def getCellSize(self):
        """
        Returns:
            cellSize: Number that controls the size of the superpixels
        """
        return self.getOrDefault(self.cellSize)
    
    
    def getInputCol(self):
        """
        Returns:
            inputCol: The name of the input column
        """
        return self.getOrDefault(self.inputCol)
    
    
    def getModifier(self):
        """
        Returns:
            modifier: Controls the trade-off spatial and color distance
        """
        return self.getOrDefault(self.modifier)
    
    
    def getOutputCol(self):
        """
        Returns:
            outputCol: The name of the output column
        """
        return self.getOrDefault(self.outputCol)

    

    
        