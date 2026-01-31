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
from synapse.ml.automl.TuneHyperparametersModel import TuneHyperparametersModel

@inherit_doc
class TuneHyperparameters(ComplexParamsMixin, JavaMLReadable, JavaMLWritable, JavaEstimator):
    """
    Args:
        evaluationMetric (str): Metric to evaluate models with
        models (object): Estimators to run
        numFolds (int): Number of folds
        numRuns (int): Termination criteria for randomized search
        parallelism (int): The number of models to run in parallel
        paramSpace (object): Parameter space for generating hyperparameters
        seed (long): Random number generator seed
    """

    evaluationMetric = Param(Params._dummy(), "evaluationMetric", "Metric to evaluate models with", typeConverter=TypeConverters.toString)
    
    models = Param(Params._dummy(), "models", "Estimators to run")
    
    numFolds = Param(Params._dummy(), "numFolds", "Number of folds", typeConverter=TypeConverters.toInt)
    
    numRuns = Param(Params._dummy(), "numRuns", "Termination criteria for randomized search", typeConverter=TypeConverters.toInt)
    
    parallelism = Param(Params._dummy(), "parallelism", "The number of models to run in parallel", typeConverter=TypeConverters.toInt)
    
    paramSpace = Param(Params._dummy(), "paramSpace", "Parameter space for generating hyperparameters")
    
    seed = Param(Params._dummy(), "seed", "Random number generator seed")

    
    @keyword_only
    def __init__(
        self,
        java_obj=None,
        evaluationMetric=None,
        models=None,
        numFolds=None,
        numRuns=None,
        parallelism=None,
        paramSpace=None,
        seed=0
        ):
        super(TuneHyperparameters, self).__init__()
        if java_obj is None:
            self._java_obj = self._new_java_obj("com.microsoft.azure.synapse.ml.automl.TuneHyperparameters", self.uid)
        else:
            self._java_obj = java_obj
        self._setDefault(seed=0)
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
        evaluationMetric=None,
        models=None,
        numFolds=None,
        numRuns=None,
        parallelism=None,
        paramSpace=None,
        seed=0
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
        return "com.microsoft.azure.synapse.ml.automl.TuneHyperparameters"

    @staticmethod
    def _from_java(java_stage):
        module_name=TuneHyperparameters.__module__
        module_name=module_name.rsplit(".", 1)[0] + ".TuneHyperparameters"
        return from_java(java_stage, module_name)

    def setEvaluationMetric(self, value):
        """
        Args:
            evaluationMetric: Metric to evaluate models with
        """
        self._set(evaluationMetric=value)
        return self
    
    def setModels(self, value):
        """
        Args:
            models: Estimators to run
        """
        self._set(models=value)
        return self
    
    def setNumFolds(self, value):
        """
        Args:
            numFolds: Number of folds
        """
        self._set(numFolds=value)
        return self
    
    def setNumRuns(self, value):
        """
        Args:
            numRuns: Termination criteria for randomized search
        """
        self._set(numRuns=value)
        return self
    
    def setParallelism(self, value):
        """
        Args:
            parallelism: The number of models to run in parallel
        """
        self._set(parallelism=value)
        return self
    
    def setParamSpace(self, value):
        """
        Args:
            paramSpace: Parameter space for generating hyperparameters
        """
        self._set(paramSpace=value)
        return self
    
    def setSeed(self, value):
        """
        Args:
            seed: Random number generator seed
        """
        self._set(seed=value)
        return self

    
    def getEvaluationMetric(self):
        """
        Returns:
            evaluationMetric: Metric to evaluate models with
        """
        return self.getOrDefault(self.evaluationMetric)
    
    
    def getModels(self):
        """
        Returns:
            models: Estimators to run
        """
        return self.getOrDefault(self.models)
    
    
    def getNumFolds(self):
        """
        Returns:
            numFolds: Number of folds
        """
        return self.getOrDefault(self.numFolds)
    
    
    def getNumRuns(self):
        """
        Returns:
            numRuns: Termination criteria for randomized search
        """
        return self.getOrDefault(self.numRuns)
    
    
    def getParallelism(self):
        """
        Returns:
            parallelism: The number of models to run in parallel
        """
        return self.getOrDefault(self.parallelism)
    
    
    def getParamSpace(self):
        """
        Returns:
            paramSpace: Parameter space for generating hyperparameters
        """
        return self.getOrDefault(self.paramSpace)
    
    
    def getSeed(self):
        """
        Returns:
            seed: Random number generator seed
        """
        return self.getOrDefault(self.seed)

    def _create_model(self, java_model):
        try:
            model = TuneHyperparametersModel(java_obj=java_model)
            model._transfer_params_from_java()
        except TypeError:
            model = TuneHyperparametersModel._from_java(java_model)
        return model
    
    def _fit(self, dataset):
        java_model = self._fit_java(dataset)
        return self._create_model(java_model)

    
        