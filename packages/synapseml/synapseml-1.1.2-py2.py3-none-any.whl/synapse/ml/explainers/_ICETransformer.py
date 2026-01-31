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
class _ICETransformer(ComplexParamsMixin, JavaMLReadable, JavaMLWritable, JavaTransformer):
    """
    Args:
        categoricalFeatures (object): The list of categorical features to explain.
        dependenceNameCol (str): Output column name which corresponds to dependence values of PDP-based-feature-importance option (kind == `feature`)
        featureNameCol (str): Output column name which corresponds to names of the features used in calculation of PDP-based-feature-importance option (kind == `feature`)
        kind (str): Whether to return the partial dependence plot (PDP) averaged across all the samples in the dataset or individual feature importance (ICE) per sample. Allowed values are "average" for PDP, "individual" for ICE and "feature" for PDP-based feature importance.
        model (object): The model to be interpreted.
        numSamples (int): Number of samples to generate.
        numericFeatures (object): The list of numeric features to explain.
        targetClasses (list): The indices of the classes for multinomial classification models. Default: 0.For regression models this parameter is ignored.
        targetClassesCol (str): The name of the column that specifies the indices of the classes for multinomial classification models.
        targetCol (str): The column name of the prediction target to explain (i.e. the response variable). This is usually set to "prediction" for regression models and "probability" for probabilistic classification models. Default value: probability
    """

    categoricalFeatures = Param(Params._dummy(), "categoricalFeatures", "The list of categorical features to explain.")
    
    dependenceNameCol = Param(Params._dummy(), "dependenceNameCol", "Output column name which corresponds to dependence values of PDP-based-feature-importance option (kind == `feature`)", typeConverter=TypeConverters.toString)
    
    featureNameCol = Param(Params._dummy(), "featureNameCol", "Output column name which corresponds to names of the features used in calculation of PDP-based-feature-importance option (kind == `feature`)", typeConverter=TypeConverters.toString)
    
    kind = Param(Params._dummy(), "kind", "Whether to return the partial dependence plot (PDP) averaged across all the samples in the dataset or individual feature importance (ICE) per sample. Allowed values are \"average\" for PDP, \"individual\" for ICE and \"feature\" for PDP-based feature importance.", typeConverter=TypeConverters.toString)
    
    model = Param(Params._dummy(), "model", "The model to be interpreted.")
    
    numSamples = Param(Params._dummy(), "numSamples", "Number of samples to generate.", typeConverter=TypeConverters.toInt)
    
    numericFeatures = Param(Params._dummy(), "numericFeatures", "The list of numeric features to explain.")
    
    targetClasses = Param(Params._dummy(), "targetClasses", "The indices of the classes for multinomial classification models. Default: 0.For regression models this parameter is ignored.", typeConverter=TypeConverters.toListInt)
    
    targetClassesCol = Param(Params._dummy(), "targetClassesCol", "The name of the column that specifies the indices of the classes for multinomial classification models.", typeConverter=TypeConverters.toString)
    
    targetCol = Param(Params._dummy(), "targetCol", "The column name of the prediction target to explain (i.e. the response variable). This is usually set to \"prediction\" for regression models and \"probability\" for probabilistic classification models. Default value: probability", typeConverter=TypeConverters.toString)

    
    @keyword_only
    def __init__(
        self,
        java_obj=None,
        categoricalFeatures=[],
        dependenceNameCol="pdpBasedDependence",
        featureNameCol="featureNames",
        kind="individual",
        model=None,
        numSamples=None,
        numericFeatures=[],
        targetClasses=[],
        targetClassesCol=None,
        targetCol="probability"
        ):
        super(_ICETransformer, self).__init__()
        if java_obj is None:
            self._java_obj = self._new_java_obj("com.microsoft.azure.synapse.ml.explainers.ICETransformer", self.uid)
        else:
            self._java_obj = java_obj
        self._setDefault(categoricalFeatures=[])
        self._setDefault(dependenceNameCol="pdpBasedDependence")
        self._setDefault(featureNameCol="featureNames")
        self._setDefault(kind="individual")
        self._setDefault(numericFeatures=[])
        self._setDefault(targetClasses=[])
        self._setDefault(targetCol="probability")
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
        categoricalFeatures=[],
        dependenceNameCol="pdpBasedDependence",
        featureNameCol="featureNames",
        kind="individual",
        model=None,
        numSamples=None,
        numericFeatures=[],
        targetClasses=[],
        targetClassesCol=None,
        targetCol="probability"
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
        return "com.microsoft.azure.synapse.ml.explainers.ICETransformer"

    @staticmethod
    def _from_java(java_stage):
        module_name=_ICETransformer.__module__
        module_name=module_name.rsplit(".", 1)[0] + ".ICETransformer"
        return from_java(java_stage, module_name)

    def setCategoricalFeatures(self, value):
        """
        Args:
            categoricalFeatures: The list of categorical features to explain.
        """
        self._set(categoricalFeatures=value)
        return self
    
    def setDependenceNameCol(self, value):
        """
        Args:
            dependenceNameCol: Output column name which corresponds to dependence values of PDP-based-feature-importance option (kind == `feature`)
        """
        self._set(dependenceNameCol=value)
        return self
    
    def setFeatureNameCol(self, value):
        """
        Args:
            featureNameCol: Output column name which corresponds to names of the features used in calculation of PDP-based-feature-importance option (kind == `feature`)
        """
        self._set(featureNameCol=value)
        return self
    
    def setKind(self, value):
        """
        Args:
            kind: Whether to return the partial dependence plot (PDP) averaged across all the samples in the dataset or individual feature importance (ICE) per sample. Allowed values are "average" for PDP, "individual" for ICE and "feature" for PDP-based feature importance.
        """
        self._set(kind=value)
        return self
    
    def setModel(self, value):
        """
        Args:
            model: The model to be interpreted.
        """
        self._set(model=value)
        return self
    
    def setNumSamples(self, value):
        """
        Args:
            numSamples: Number of samples to generate.
        """
        self._set(numSamples=value)
        return self
    
    def setNumericFeatures(self, value):
        """
        Args:
            numericFeatures: The list of numeric features to explain.
        """
        self._set(numericFeatures=value)
        return self
    
    def setTargetClasses(self, value):
        """
        Args:
            targetClasses: The indices of the classes for multinomial classification models. Default: 0.For regression models this parameter is ignored.
        """
        self._set(targetClasses=value)
        return self
    
    def setTargetClassesCol(self, value):
        """
        Args:
            targetClassesCol: The name of the column that specifies the indices of the classes for multinomial classification models.
        """
        self._set(targetClassesCol=value)
        return self
    
    def setTargetCol(self, value):
        """
        Args:
            targetCol: The column name of the prediction target to explain (i.e. the response variable). This is usually set to "prediction" for regression models and "probability" for probabilistic classification models. Default value: probability
        """
        self._set(targetCol=value)
        return self

    
    def getCategoricalFeatures(self):
        """
        Returns:
            categoricalFeatures: The list of categorical features to explain.
        """
        return self.getOrDefault(self.categoricalFeatures)
    
    
    def getDependenceNameCol(self):
        """
        Returns:
            dependenceNameCol: Output column name which corresponds to dependence values of PDP-based-feature-importance option (kind == `feature`)
        """
        return self.getOrDefault(self.dependenceNameCol)
    
    
    def getFeatureNameCol(self):
        """
        Returns:
            featureNameCol: Output column name which corresponds to names of the features used in calculation of PDP-based-feature-importance option (kind == `feature`)
        """
        return self.getOrDefault(self.featureNameCol)
    
    
    def getKind(self):
        """
        Returns:
            kind: Whether to return the partial dependence plot (PDP) averaged across all the samples in the dataset or individual feature importance (ICE) per sample. Allowed values are "average" for PDP, "individual" for ICE and "feature" for PDP-based feature importance.
        """
        return self.getOrDefault(self.kind)
    
    
    def getModel(self):
        """
        Returns:
            model: The model to be interpreted.
        """
        return JavaParams._from_java(self._java_obj.getModel())
    
    
    def getNumSamples(self):
        """
        Returns:
            numSamples: Number of samples to generate.
        """
        return self.getOrDefault(self.numSamples)
    
    
    def getNumericFeatures(self):
        """
        Returns:
            numericFeatures: The list of numeric features to explain.
        """
        return self.getOrDefault(self.numericFeatures)
    
    
    def getTargetClasses(self):
        """
        Returns:
            targetClasses: The indices of the classes for multinomial classification models. Default: 0.For regression models this parameter is ignored.
        """
        return self.getOrDefault(self.targetClasses)
    
    
    def getTargetClassesCol(self):
        """
        Returns:
            targetClassesCol: The name of the column that specifies the indices of the classes for multinomial classification models.
        """
        return self.getOrDefault(self.targetClassesCol)
    
    
    def getTargetCol(self):
        """
        Returns:
            targetCol: The column name of the prediction target to explain (i.e. the response variable). This is usually set to "prediction" for regression models and "probability" for probabilistic classification models. Default value: probability
        """
        return self.getOrDefault(self.targetCol)

    

    
        