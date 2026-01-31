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
class DistributionBalanceMeasure(ComplexParamsMixin, JavaMLReadable, JavaMLWritable, JavaTransformer):
    """
    Args:
        featureNameCol (str): Output column name for feature names.
        outputCol (str): output column name
        referenceDistribution (object): An ordered list of reference distributions that correspond to each of the sensitive columns.
        sensitiveCols (list): Sensitive columns to use.
        verbose (bool): Whether to show intermediate measures and calculations, such as Positive Rate.
    """

    featureNameCol = Param(Params._dummy(), "featureNameCol", "Output column name for feature names.", typeConverter=TypeConverters.toString)
    
    outputCol = Param(Params._dummy(), "outputCol", "output column name", typeConverter=TypeConverters.toString)
    
    referenceDistribution = Param(Params._dummy(), "referenceDistribution", "An ordered list of reference distributions that correspond to each of the sensitive columns.")
    
    sensitiveCols = Param(Params._dummy(), "sensitiveCols", "Sensitive columns to use.", typeConverter=TypeConverters.toListString)
    
    verbose = Param(Params._dummy(), "verbose", "Whether to show intermediate measures and calculations, such as Positive Rate.", typeConverter=TypeConverters.toBoolean)

    
    @keyword_only
    def __init__(
        self,
        java_obj=None,
        featureNameCol="FeatureName",
        outputCol="DistributionBalanceMeasure",
        referenceDistribution=None,
        sensitiveCols=None,
        verbose=False
        ):
        super(DistributionBalanceMeasure, self).__init__()
        if java_obj is None:
            self._java_obj = self._new_java_obj("com.microsoft.azure.synapse.ml.exploratory.DistributionBalanceMeasure", self.uid)
        else:
            self._java_obj = java_obj
        self._setDefault(featureNameCol="FeatureName")
        self._setDefault(outputCol="DistributionBalanceMeasure")
        self._setDefault(verbose=False)
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
        featureNameCol="FeatureName",
        outputCol="DistributionBalanceMeasure",
        referenceDistribution=None,
        sensitiveCols=None,
        verbose=False
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
        return "com.microsoft.azure.synapse.ml.exploratory.DistributionBalanceMeasure"

    @staticmethod
    def _from_java(java_stage):
        module_name=DistributionBalanceMeasure.__module__
        module_name=module_name.rsplit(".", 1)[0] + ".DistributionBalanceMeasure"
        return from_java(java_stage, module_name)

    def setFeatureNameCol(self, value):
        """
        Args:
            featureNameCol: Output column name for feature names.
        """
        self._set(featureNameCol=value)
        return self
    
    def setOutputCol(self, value):
        """
        Args:
            outputCol: output column name
        """
        self._set(outputCol=value)
        return self
    
    def setReferenceDistribution(self, value):
        """
        Args:
            referenceDistribution: An ordered list of reference distributions that correspond to each of the sensitive columns.
        """
        self._set(referenceDistribution=value)
        return self
    
    def setSensitiveCols(self, value):
        """
        Args:
            sensitiveCols: Sensitive columns to use.
        """
        self._set(sensitiveCols=value)
        return self
    
    def setVerbose(self, value):
        """
        Args:
            verbose: Whether to show intermediate measures and calculations, such as Positive Rate.
        """
        self._set(verbose=value)
        return self

    
    def getFeatureNameCol(self):
        """
        Returns:
            featureNameCol: Output column name for feature names.
        """
        return self.getOrDefault(self.featureNameCol)
    
    
    def getOutputCol(self):
        """
        Returns:
            outputCol: output column name
        """
        return self.getOrDefault(self.outputCol)
    
    
    def getReferenceDistribution(self):
        """
        Returns:
            referenceDistribution: An ordered list of reference distributions that correspond to each of the sensitive columns.
        """
        return self.getOrDefault(self.referenceDistribution)
    
    
    def getSensitiveCols(self):
        """
        Returns:
            sensitiveCols: Sensitive columns to use.
        """
        return self.getOrDefault(self.sensitiveCols)
    
    
    def getVerbose(self):
        """
        Returns:
            verbose: Whether to show intermediate measures and calculations, such as Positive Rate.
        """
        return self.getOrDefault(self.verbose)

    

    
        