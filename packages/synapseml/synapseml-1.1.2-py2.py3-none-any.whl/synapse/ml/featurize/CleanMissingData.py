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
from synapse.ml.featurize.CleanMissingDataModel import CleanMissingDataModel

@inherit_doc
class CleanMissingData(ComplexParamsMixin, JavaMLReadable, JavaMLWritable, JavaEstimator):
    """
    Args:
        cleaningMode (str): Cleaning mode
        customValue (str): Custom value for replacement
        inputCols (list): The names of the input columns
        outputCols (list): The names of the output columns
    """

    cleaningMode = Param(Params._dummy(), "cleaningMode", "Cleaning mode", typeConverter=TypeConverters.toString)
    
    customValue = Param(Params._dummy(), "customValue", "Custom value for replacement", typeConverter=TypeConverters.toString)
    
    inputCols = Param(Params._dummy(), "inputCols", "The names of the input columns", typeConverter=TypeConverters.toListString)
    
    outputCols = Param(Params._dummy(), "outputCols", "The names of the output columns", typeConverter=TypeConverters.toListString)

    
    @keyword_only
    def __init__(
        self,
        java_obj=None,
        cleaningMode="Mean",
        customValue=None,
        inputCols=None,
        outputCols=None
        ):
        super(CleanMissingData, self).__init__()
        if java_obj is None:
            self._java_obj = self._new_java_obj("com.microsoft.azure.synapse.ml.featurize.CleanMissingData", self.uid)
        else:
            self._java_obj = java_obj
        self._setDefault(cleaningMode="Mean")
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
        cleaningMode="Mean",
        customValue=None,
        inputCols=None,
        outputCols=None
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
        return "com.microsoft.azure.synapse.ml.featurize.CleanMissingData"

    @staticmethod
    def _from_java(java_stage):
        module_name=CleanMissingData.__module__
        module_name=module_name.rsplit(".", 1)[0] + ".CleanMissingData"
        return from_java(java_stage, module_name)

    def setCleaningMode(self, value):
        """
        Args:
            cleaningMode: Cleaning mode
        """
        self._set(cleaningMode=value)
        return self
    
    def setCustomValue(self, value):
        """
        Args:
            customValue: Custom value for replacement
        """
        self._set(customValue=value)
        return self
    
    def setInputCols(self, value):
        """
        Args:
            inputCols: The names of the input columns
        """
        self._set(inputCols=value)
        return self
    
    def setOutputCols(self, value):
        """
        Args:
            outputCols: The names of the output columns
        """
        self._set(outputCols=value)
        return self

    
    def getCleaningMode(self):
        """
        Returns:
            cleaningMode: Cleaning mode
        """
        return self.getOrDefault(self.cleaningMode)
    
    
    def getCustomValue(self):
        """
        Returns:
            customValue: Custom value for replacement
        """
        return self.getOrDefault(self.customValue)
    
    
    def getInputCols(self):
        """
        Returns:
            inputCols: The names of the input columns
        """
        return self.getOrDefault(self.inputCols)
    
    
    def getOutputCols(self):
        """
        Returns:
            outputCols: The names of the output columns
        """
        return self.getOrDefault(self.outputCols)

    def _create_model(self, java_model):
        try:
            model = CleanMissingDataModel(java_obj=java_model)
            model._transfer_params_from_java()
        except TypeError:
            model = CleanMissingDataModel._from_java(java_model)
        return model
    
    def _fit(self, dataset):
        java_model = self._fit_java(dataset)
        return self._create_model(java_model)

    
        