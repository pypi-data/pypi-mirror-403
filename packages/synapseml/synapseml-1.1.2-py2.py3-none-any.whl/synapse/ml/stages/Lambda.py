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
class Lambda(ComplexParamsMixin, JavaMLReadable, JavaMLWritable, JavaTransformer):
    """
    Args:
        transformFunc (object): holder for dataframe function
        transformSchemaFunc (object): the output schema after the transformation
    """

    transformFunc = Param(Params._dummy(), "transformFunc", "holder for dataframe function")
    
    transformSchemaFunc = Param(Params._dummy(), "transformSchemaFunc", "the output schema after the transformation")

    
    @keyword_only
    def __init__(
        self,
        java_obj=None,
        transformFunc=None,
        transformSchemaFunc=None
        ):
        super(Lambda, self).__init__()
        if java_obj is None:
            self._java_obj = self._new_java_obj("com.microsoft.azure.synapse.ml.stages.Lambda", self.uid)
        else:
            self._java_obj = java_obj
        
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
        transformFunc=None,
        transformSchemaFunc=None
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
        return "com.microsoft.azure.synapse.ml.stages.Lambda"

    @staticmethod
    def _from_java(java_stage):
        module_name=Lambda.__module__
        module_name=module_name.rsplit(".", 1)[0] + ".Lambda"
        return from_java(java_stage, module_name)

    def setTransformFunc(self, value):
        """
        Args:
            transformFunc: holder for dataframe function
        """
        self._set(transformFunc=value)
        return self
    
    def setTransformSchemaFunc(self, value):
        """
        Args:
            transformSchemaFunc: the output schema after the transformation
        """
        self._set(transformSchemaFunc=value)
        return self

    
    def getTransformFunc(self):
        """
        Returns:
            transformFunc: holder for dataframe function
        """
        return self.getOrDefault(self.transformFunc)
    
    
    def getTransformSchemaFunc(self):
        """
        Returns:
            transformSchemaFunc: the output schema after the transformation
        """
        return self.getOrDefault(self.transformSchemaFunc)

    

    
        