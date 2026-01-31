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
class ValueIndexerModel(ComplexParamsMixin, JavaMLReadable, JavaMLWritable, JavaModel):
    """
    Args:
        dataType (str): The datatype of the levels as a Json string
        inputCol (str): The name of the input column
        levels (object): Levels in categorical array
        outputCol (str): The name of the output column
    """

    dataType = Param(Params._dummy(), "dataType", "The datatype of the levels as a Json string", typeConverter=TypeConverters.toString)
    
    inputCol = Param(Params._dummy(), "inputCol", "The name of the input column", typeConverter=TypeConverters.toString)
    
    levels = Param(Params._dummy(), "levels", "Levels in categorical array")
    
    outputCol = Param(Params._dummy(), "outputCol", "The name of the output column", typeConverter=TypeConverters.toString)

    
    @keyword_only
    def __init__(
        self,
        java_obj=None,
        dataType="string",
        inputCol="input",
        levels=None,
        outputCol="ValueIndexerModel_56af63e49349_output"
        ):
        super(ValueIndexerModel, self).__init__()
        if java_obj is None:
            self._java_obj = self._new_java_obj("com.microsoft.azure.synapse.ml.featurize.ValueIndexerModel", self.uid)
        else:
            self._java_obj = java_obj
        self._setDefault(dataType="string")
        self._setDefault(inputCol="input")
        self._setDefault(outputCol="ValueIndexerModel_56af63e49349_output")
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
        dataType="string",
        inputCol="input",
        levels=None,
        outputCol="ValueIndexerModel_56af63e49349_output"
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
        return "com.microsoft.azure.synapse.ml.featurize.ValueIndexerModel"

    @staticmethod
    def _from_java(java_stage):
        module_name=ValueIndexerModel.__module__
        module_name=module_name.rsplit(".", 1)[0] + ".ValueIndexerModel"
        return from_java(java_stage, module_name)

    def setDataType(self, value):
        """
        Args:
            dataType: The datatype of the levels as a Json string
        """
        self._set(dataType=value)
        return self
    
    def setInputCol(self, value):
        """
        Args:
            inputCol: The name of the input column
        """
        self._set(inputCol=value)
        return self
    
    def setLevels(self, value):
        """
        Args:
            levels: Levels in categorical array
        """
        self._set(levels=value)
        return self
    
    def setOutputCol(self, value):
        """
        Args:
            outputCol: The name of the output column
        """
        self._set(outputCol=value)
        return self

    
    def getDataType(self):
        """
        Returns:
            dataType: The datatype of the levels as a Json string
        """
        return self.getOrDefault(self.dataType)
    
    
    def getInputCol(self):
        """
        Returns:
            inputCol: The name of the input column
        """
        return self.getOrDefault(self.inputCol)
    
    
    def getLevels(self):
        """
        Returns:
            levels: Levels in categorical array
        """
        return self.getOrDefault(self.levels)
    
    
    def getOutputCol(self):
        """
        Returns:
            outputCol: The name of the output column
        """
        return self.getOrDefault(self.outputCol)

    

    
        