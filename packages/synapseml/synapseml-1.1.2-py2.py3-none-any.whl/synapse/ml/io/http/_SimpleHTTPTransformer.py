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
class _SimpleHTTPTransformer(ComplexParamsMixin, JavaMLReadable, JavaMLWritable, JavaTransformer):
    """
    Args:
        concurrency (int): max number of concurrent calls
        concurrentTimeout (float): max number seconds to wait on futures if concurrency >= 1
        errorCol (str): column to hold http errors
        flattenOutputBatches (bool): whether to flatten the output batches
        handler (object): Which strategy to use when handling requests
        inputCol (str): The name of the input column
        inputParser (object): format to parse the column to
        miniBatcher (object): Minibatcher to use
        outputCol (str): The name of the output column
        outputParser (object): format to parse the column to
        timeout (float): number of seconds to wait before closing the connection
    """

    concurrency = Param(Params._dummy(), "concurrency", "max number of concurrent calls", typeConverter=TypeConverters.toInt)
    
    concurrentTimeout = Param(Params._dummy(), "concurrentTimeout", "max number seconds to wait on futures if concurrency >= 1", typeConverter=TypeConverters.toFloat)
    
    errorCol = Param(Params._dummy(), "errorCol", "column to hold http errors", typeConverter=TypeConverters.toString)
    
    flattenOutputBatches = Param(Params._dummy(), "flattenOutputBatches", "whether to flatten the output batches", typeConverter=TypeConverters.toBoolean)
    
    handler = Param(Params._dummy(), "handler", "Which strategy to use when handling requests")
    
    inputCol = Param(Params._dummy(), "inputCol", "The name of the input column", typeConverter=TypeConverters.toString)
    
    inputParser = Param(Params._dummy(), "inputParser", "format to parse the column to")
    
    miniBatcher = Param(Params._dummy(), "miniBatcher", "Minibatcher to use")
    
    outputCol = Param(Params._dummy(), "outputCol", "The name of the output column", typeConverter=TypeConverters.toString)
    
    outputParser = Param(Params._dummy(), "outputParser", "format to parse the column to")
    
    timeout = Param(Params._dummy(), "timeout", "number of seconds to wait before closing the connection", typeConverter=TypeConverters.toFloat)

    
    @keyword_only
    def __init__(
        self,
        java_obj=None,
        concurrency=1,
        concurrentTimeout=None,
        errorCol="SimpleHTTPTransformer_12a903b714de_errors",
        flattenOutputBatches=None,
        handler=None,
        inputCol=None,
        inputParser=None,
        miniBatcher=None,
        outputCol=None,
        outputParser=None,
        timeout=60.0
        ):
        super(_SimpleHTTPTransformer, self).__init__()
        if java_obj is None:
            self._java_obj = self._new_java_obj("com.microsoft.azure.synapse.ml.io.http.SimpleHTTPTransformer", self.uid)
        else:
            self._java_obj = java_obj
        self._setDefault(concurrency=1)
        self._setDefault(errorCol="SimpleHTTPTransformer_12a903b714de_errors")
        self._setDefault(timeout=60.0)
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
        concurrency=1,
        concurrentTimeout=None,
        errorCol="SimpleHTTPTransformer_12a903b714de_errors",
        flattenOutputBatches=None,
        handler=None,
        inputCol=None,
        inputParser=None,
        miniBatcher=None,
        outputCol=None,
        outputParser=None,
        timeout=60.0
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
        return "com.microsoft.azure.synapse.ml.io.http.SimpleHTTPTransformer"

    @staticmethod
    def _from_java(java_stage):
        module_name=_SimpleHTTPTransformer.__module__
        module_name=module_name.rsplit(".", 1)[0] + ".SimpleHTTPTransformer"
        return from_java(java_stage, module_name)

    def setConcurrency(self, value):
        """
        Args:
            concurrency: max number of concurrent calls
        """
        self._set(concurrency=value)
        return self
    
    def setConcurrentTimeout(self, value):
        """
        Args:
            concurrentTimeout: max number seconds to wait on futures if concurrency >= 1
        """
        self._set(concurrentTimeout=value)
        return self
    
    def setErrorCol(self, value):
        """
        Args:
            errorCol: column to hold http errors
        """
        self._set(errorCol=value)
        return self
    
    def setFlattenOutputBatches(self, value):
        """
        Args:
            flattenOutputBatches: whether to flatten the output batches
        """
        self._set(flattenOutputBatches=value)
        return self
    
    def setHandler(self, value):
        """
        Args:
            handler: Which strategy to use when handling requests
        """
        self._set(handler=value)
        return self
    
    def setInputCol(self, value):
        """
        Args:
            inputCol: The name of the input column
        """
        self._set(inputCol=value)
        return self
    
    def setInputParser(self, value):
        """
        Args:
            inputParser: format to parse the column to
        """
        self._set(inputParser=value)
        return self
    
    def setMiniBatcher(self, value):
        """
        Args:
            miniBatcher: Minibatcher to use
        """
        self._set(miniBatcher=value)
        return self
    
    def setOutputCol(self, value):
        """
        Args:
            outputCol: The name of the output column
        """
        self._set(outputCol=value)
        return self
    
    def setOutputParser(self, value):
        """
        Args:
            outputParser: format to parse the column to
        """
        self._set(outputParser=value)
        return self
    
    def setTimeout(self, value):
        """
        Args:
            timeout: number of seconds to wait before closing the connection
        """
        self._set(timeout=value)
        return self

    
    def getConcurrency(self):
        """
        Returns:
            concurrency: max number of concurrent calls
        """
        return self.getOrDefault(self.concurrency)
    
    
    def getConcurrentTimeout(self):
        """
        Returns:
            concurrentTimeout: max number seconds to wait on futures if concurrency >= 1
        """
        return self.getOrDefault(self.concurrentTimeout)
    
    
    def getErrorCol(self):
        """
        Returns:
            errorCol: column to hold http errors
        """
        return self.getOrDefault(self.errorCol)
    
    
    def getFlattenOutputBatches(self):
        """
        Returns:
            flattenOutputBatches: whether to flatten the output batches
        """
        return self.getOrDefault(self.flattenOutputBatches)
    
    
    def getHandler(self):
        """
        Returns:
            handler: Which strategy to use when handling requests
        """
        return self.getOrDefault(self.handler)
    
    
    def getInputCol(self):
        """
        Returns:
            inputCol: The name of the input column
        """
        return self.getOrDefault(self.inputCol)
    
    
    def getInputParser(self):
        """
        Returns:
            inputParser: format to parse the column to
        """
        return JavaParams._from_java(self._java_obj.getInputParser())
    
    
    def getMiniBatcher(self):
        """
        Returns:
            miniBatcher: Minibatcher to use
        """
        return JavaParams._from_java(self._java_obj.getMiniBatcher())
    
    
    def getOutputCol(self):
        """
        Returns:
            outputCol: The name of the output column
        """
        return self.getOrDefault(self.outputCol)
    
    
    def getOutputParser(self):
        """
        Returns:
            outputParser: format to parse the column to
        """
        return JavaParams._from_java(self._java_obj.getOutputParser())
    
    
    def getTimeout(self):
        """
        Returns:
            timeout: number of seconds to wait before closing the connection
        """
        return self.getOrDefault(self.timeout)

    

    
        