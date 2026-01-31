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
class DataConversion(ComplexParamsMixin, JavaMLReadable, JavaMLWritable, JavaTransformer):
    """
    Args:
        cols (list): Comma separated list of columns whose type will be converted
        convertTo (str): The result type
        dateTimeFormat (str): Format for DateTime when making DateTime:String conversions
    """

    cols = Param(Params._dummy(), "cols", "Comma separated list of columns whose type will be converted", typeConverter=TypeConverters.toListString)
    
    convertTo = Param(Params._dummy(), "convertTo", "The result type", typeConverter=TypeConverters.toString)
    
    dateTimeFormat = Param(Params._dummy(), "dateTimeFormat", "Format for DateTime when making DateTime:String conversions", typeConverter=TypeConverters.toString)

    
    @keyword_only
    def __init__(
        self,
        java_obj=None,
        cols=None,
        convertTo="",
        dateTimeFormat="yyyy-MM-dd HH:mm:ss"
        ):
        super(DataConversion, self).__init__()
        if java_obj is None:
            self._java_obj = self._new_java_obj("com.microsoft.azure.synapse.ml.featurize.DataConversion", self.uid)
        else:
            self._java_obj = java_obj
        self._setDefault(convertTo="")
        self._setDefault(dateTimeFormat="yyyy-MM-dd HH:mm:ss")
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
        cols=None,
        convertTo="",
        dateTimeFormat="yyyy-MM-dd HH:mm:ss"
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
        return "com.microsoft.azure.synapse.ml.featurize.DataConversion"

    @staticmethod
    def _from_java(java_stage):
        module_name=DataConversion.__module__
        module_name=module_name.rsplit(".", 1)[0] + ".DataConversion"
        return from_java(java_stage, module_name)

    def setCols(self, value):
        """
        Args:
            cols: Comma separated list of columns whose type will be converted
        """
        self._set(cols=value)
        return self
    
    def setConvertTo(self, value):
        """
        Args:
            convertTo: The result type
        """
        self._set(convertTo=value)
        return self
    
    def setDateTimeFormat(self, value):
        """
        Args:
            dateTimeFormat: Format for DateTime when making DateTime:String conversions
        """
        self._set(dateTimeFormat=value)
        return self

    
    def getCols(self):
        """
        Returns:
            cols: Comma separated list of columns whose type will be converted
        """
        return self.getOrDefault(self.cols)
    
    
    def getConvertTo(self):
        """
        Returns:
            convertTo: The result type
        """
        return self.getOrDefault(self.convertTo)
    
    
    def getDateTimeFormat(self):
        """
        Returns:
            dateTimeFormat: Format for DateTime when making DateTime:String conversions
        """
        return self.getOrDefault(self.dateTimeFormat)

    

    
        