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
from synapse.ml.causal.DoubleMLModel import DoubleMLModel

@inherit_doc
class DoubleMLEstimator(ComplexParamsMixin, JavaMLReadable, JavaMLWritable, JavaEstimator):
    """
    Args:
        confidenceLevel (float): confidence level, default value is 0.975
        featuresCol (str): The name of the features column
        maxIter (int): maximum number of iterations (>= 0)
        outcomeCol (str): outcome column
        outcomeModel (object): outcome model to run
        parallelism (int): the number of threads to use when running parallel algorithms
        sampleSplitRatio (list): Sample split ratio for cross-fitting. Default: [0.5, 0.5].
        treatmentCol (str): treatment column
        treatmentModel (object): treatment model to run
        weightCol (str): The name of the weight column
    """

    confidenceLevel = Param(Params._dummy(), "confidenceLevel", "confidence level, default value is 0.975", typeConverter=TypeConverters.toFloat)
    
    featuresCol = Param(Params._dummy(), "featuresCol", "The name of the features column", typeConverter=TypeConverters.toString)
    
    maxIter = Param(Params._dummy(), "maxIter", "maximum number of iterations (>= 0)", typeConverter=TypeConverters.toInt)
    
    outcomeCol = Param(Params._dummy(), "outcomeCol", "outcome column", typeConverter=TypeConverters.toString)
    
    outcomeModel = Param(Params._dummy(), "outcomeModel", "outcome model to run")
    
    parallelism = Param(Params._dummy(), "parallelism", "the number of threads to use when running parallel algorithms", typeConverter=TypeConverters.toInt)
    
    sampleSplitRatio = Param(Params._dummy(), "sampleSplitRatio", "Sample split ratio for cross-fitting. Default: [0.5, 0.5].", typeConverter=TypeConverters.toListFloat)
    
    treatmentCol = Param(Params._dummy(), "treatmentCol", "treatment column", typeConverter=TypeConverters.toString)
    
    treatmentModel = Param(Params._dummy(), "treatmentModel", "treatment model to run")
    
    weightCol = Param(Params._dummy(), "weightCol", "The name of the weight column", typeConverter=TypeConverters.toString)

    
    @keyword_only
    def __init__(
        self,
        java_obj=None,
        confidenceLevel=0.975,
        featuresCol=None,
        maxIter=1,
        outcomeCol=None,
        outcomeModel=None,
        parallelism=10,
        sampleSplitRatio=[0.5,0.5],
        treatmentCol=None,
        treatmentModel=None,
        weightCol=None
        ):
        super(DoubleMLEstimator, self).__init__()
        if java_obj is None:
            self._java_obj = self._new_java_obj("com.microsoft.azure.synapse.ml.causal.DoubleMLEstimator", self.uid)
        else:
            self._java_obj = java_obj
        self._setDefault(confidenceLevel=0.975)
        self._setDefault(maxIter=1)
        self._setDefault(parallelism=10)
        self._setDefault(sampleSplitRatio=[0.5,0.5])
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
        confidenceLevel=0.975,
        featuresCol=None,
        maxIter=1,
        outcomeCol=None,
        outcomeModel=None,
        parallelism=10,
        sampleSplitRatio=[0.5,0.5],
        treatmentCol=None,
        treatmentModel=None,
        weightCol=None
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
        return "com.microsoft.azure.synapse.ml.causal.DoubleMLEstimator"

    @staticmethod
    def _from_java(java_stage):
        module_name=DoubleMLEstimator.__module__
        module_name=module_name.rsplit(".", 1)[0] + ".DoubleMLEstimator"
        return from_java(java_stage, module_name)

    def setConfidenceLevel(self, value):
        """
        Args:
            confidenceLevel: confidence level, default value is 0.975
        """
        self._set(confidenceLevel=value)
        return self
    
    def setFeaturesCol(self, value):
        """
        Args:
            featuresCol: The name of the features column
        """
        self._set(featuresCol=value)
        return self
    
    def setMaxIter(self, value):
        """
        Args:
            maxIter: maximum number of iterations (>= 0)
        """
        self._set(maxIter=value)
        return self
    
    def setOutcomeCol(self, value):
        """
        Args:
            outcomeCol: outcome column
        """
        self._set(outcomeCol=value)
        return self
    
    def setOutcomeModel(self, value):
        """
        Args:
            outcomeModel: outcome model to run
        """
        self._set(outcomeModel=value)
        return self
    
    def setParallelism(self, value):
        """
        Args:
            parallelism: the number of threads to use when running parallel algorithms
        """
        self._set(parallelism=value)
        return self
    
    def setSampleSplitRatio(self, value):
        """
        Args:
            sampleSplitRatio: Sample split ratio for cross-fitting. Default: [0.5, 0.5].
        """
        self._set(sampleSplitRatio=value)
        return self
    
    def setTreatmentCol(self, value):
        """
        Args:
            treatmentCol: treatment column
        """
        self._set(treatmentCol=value)
        return self
    
    def setTreatmentModel(self, value):
        """
        Args:
            treatmentModel: treatment model to run
        """
        self._set(treatmentModel=value)
        return self
    
    def setWeightCol(self, value):
        """
        Args:
            weightCol: The name of the weight column
        """
        self._set(weightCol=value)
        return self

    
    def getConfidenceLevel(self):
        """
        Returns:
            confidenceLevel: confidence level, default value is 0.975
        """
        return self.getOrDefault(self.confidenceLevel)
    
    
    def getFeaturesCol(self):
        """
        Returns:
            featuresCol: The name of the features column
        """
        return self.getOrDefault(self.featuresCol)
    
    
    def getMaxIter(self):
        """
        Returns:
            maxIter: maximum number of iterations (>= 0)
        """
        return self.getOrDefault(self.maxIter)
    
    
    def getOutcomeCol(self):
        """
        Returns:
            outcomeCol: outcome column
        """
        return self.getOrDefault(self.outcomeCol)
    
    
    def getOutcomeModel(self):
        """
        Returns:
            outcomeModel: outcome model to run
        """
        return JavaParams._from_java(self._java_obj.getOutcomeModel())
    
    
    def getParallelism(self):
        """
        Returns:
            parallelism: the number of threads to use when running parallel algorithms
        """
        return self.getOrDefault(self.parallelism)
    
    
    def getSampleSplitRatio(self):
        """
        Returns:
            sampleSplitRatio: Sample split ratio for cross-fitting. Default: [0.5, 0.5].
        """
        return self.getOrDefault(self.sampleSplitRatio)
    
    
    def getTreatmentCol(self):
        """
        Returns:
            treatmentCol: treatment column
        """
        return self.getOrDefault(self.treatmentCol)
    
    
    def getTreatmentModel(self):
        """
        Returns:
            treatmentModel: treatment model to run
        """
        return JavaParams._from_java(self._java_obj.getTreatmentModel())
    
    
    def getWeightCol(self):
        """
        Returns:
            weightCol: The name of the weight column
        """
        return self.getOrDefault(self.weightCol)

    def _create_model(self, java_model):
        try:
            model = DoubleMLModel(java_obj=java_model)
            model._transfer_params_from_java()
        except TypeError:
            model = DoubleMLModel._from_java(java_model)
        return model
    
    def _fit(self, dataset):
        java_model = self._fit_java(dataset)
        return self._create_model(java_model)

    
        