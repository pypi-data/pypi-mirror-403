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
class PageSplitter(ComplexParamsMixin, JavaMLReadable, JavaMLWritable, JavaTransformer):
    """
    Args:
        boundaryRegex (str): how to split into words
        inputCol (str): The name of the input column
        maximumPageLength (int): the maximum number of characters to be in a page
        minimumPageLength (int): the the minimum number of characters to have on a page in order to preserve work boundaries
        outputCol (str): The name of the output column
    """

    boundaryRegex = Param(Params._dummy(), "boundaryRegex", "how to split into words", typeConverter=TypeConverters.toString)
    
    inputCol = Param(Params._dummy(), "inputCol", "The name of the input column", typeConverter=TypeConverters.toString)
    
    maximumPageLength = Param(Params._dummy(), "maximumPageLength", "the maximum number of characters to be in a page", typeConverter=TypeConverters.toInt)
    
    minimumPageLength = Param(Params._dummy(), "minimumPageLength", "the the minimum number of characters to have on a page in order to preserve work boundaries", typeConverter=TypeConverters.toInt)
    
    outputCol = Param(Params._dummy(), "outputCol", "The name of the output column", typeConverter=TypeConverters.toString)

    
    @keyword_only
    def __init__(
        self,
        java_obj=None,
        boundaryRegex="\\s",
        inputCol=None,
        maximumPageLength=5000,
        minimumPageLength=4500,
        outputCol="PageSplitter_b067bee6dcd2_output"
        ):
        super(PageSplitter, self).__init__()
        if java_obj is None:
            self._java_obj = self._new_java_obj("com.microsoft.azure.synapse.ml.featurize.text.PageSplitter", self.uid)
        else:
            self._java_obj = java_obj
        self._setDefault(boundaryRegex="\\s")
        self._setDefault(maximumPageLength=5000)
        self._setDefault(minimumPageLength=4500)
        self._setDefault(outputCol="PageSplitter_b067bee6dcd2_output")
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
        boundaryRegex="\\s",
        inputCol=None,
        maximumPageLength=5000,
        minimumPageLength=4500,
        outputCol="PageSplitter_b067bee6dcd2_output"
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
        return "com.microsoft.azure.synapse.ml.featurize.text.PageSplitter"

    @staticmethod
    def _from_java(java_stage):
        module_name=PageSplitter.__module__
        module_name=module_name.rsplit(".", 1)[0] + ".PageSplitter"
        return from_java(java_stage, module_name)

    def setBoundaryRegex(self, value):
        """
        Args:
            boundaryRegex: how to split into words
        """
        self._set(boundaryRegex=value)
        return self
    
    def setInputCol(self, value):
        """
        Args:
            inputCol: The name of the input column
        """
        self._set(inputCol=value)
        return self
    
    def setMaximumPageLength(self, value):
        """
        Args:
            maximumPageLength: the maximum number of characters to be in a page
        """
        self._set(maximumPageLength=value)
        return self
    
    def setMinimumPageLength(self, value):
        """
        Args:
            minimumPageLength: the the minimum number of characters to have on a page in order to preserve work boundaries
        """
        self._set(minimumPageLength=value)
        return self
    
    def setOutputCol(self, value):
        """
        Args:
            outputCol: The name of the output column
        """
        self._set(outputCol=value)
        return self

    
    def getBoundaryRegex(self):
        """
        Returns:
            boundaryRegex: how to split into words
        """
        return self.getOrDefault(self.boundaryRegex)
    
    
    def getInputCol(self):
        """
        Returns:
            inputCol: The name of the input column
        """
        return self.getOrDefault(self.inputCol)
    
    
    def getMaximumPageLength(self):
        """
        Returns:
            maximumPageLength: the maximum number of characters to be in a page
        """
        return self.getOrDefault(self.maximumPageLength)
    
    
    def getMinimumPageLength(self):
        """
        Returns:
            minimumPageLength: the the minimum number of characters to have on a page in order to preserve work boundaries
        """
        return self.getOrDefault(self.minimumPageLength)
    
    
    def getOutputCol(self):
        """
        Returns:
            outputCol: The name of the output column
        """
        return self.getOrDefault(self.outputCol)

    

    
        