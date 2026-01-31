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
from synapse.ml.services.anomaly.SimpleDetectMultivariateAnomaly import SimpleDetectMultivariateAnomaly

@inherit_doc
class SimpleFitMultivariateAnomaly(ComplexParamsMixin, JavaMLReadable, JavaMLWritable, JavaEstimator):
    """
    Args:
        alignMode (str): An optional field, indicates how we align different variables into the same time-range which is required by the model.{Inner, Outer}
        backoffs (list): array of backoffs to use in the handler
        displayName (str): optional field, name of the model
        endTime (str): A required field, end time of data to be used for detection/generating multivariate anomaly detection model, should be date-time.
        errorCol (str): column to hold http errors
        fillNAMethod (str): An optional field, indicates how missed values will be filled with. Can not be set to NotFill, when alignMode is Outer.{Previous, Subsequent, Linear, Zero, Fixed}
        initialPollingDelay (int): number of milliseconds to wait before first poll for result
        inputCols (list): The names of the input columns
        intermediateSaveDir (str): Blob storage location in HDFS where intermediate data is saved while training.
        maxPollingRetries (int): number of times to poll
        outputCol (str): The name of the output column
        paddingValue (int): optional field, is only useful if FillNAMethod is set to Fixed.
        pollingDelay (int): number of milliseconds to wait between polling
        slidingWindow (int): An optional field, indicates how many history points will be used to determine the anomaly score of one subsequent point.
        startTime (str): A required field, start time of data to be used for detection/generating multivariate anomaly detection model, should be date-time.
        subscriptionKey (object): the API key to use
        suppressMaxRetriesException (bool): set true to suppress the maxumimum retries exception and report in the error column
        timestampCol (str): Timestamp column name
        url (str): Url of the service
    """

    alignMode = Param(Params._dummy(), "alignMode", "An optional field, indicates how we align different variables into the same time-range which is required by the model.{Inner, Outer}", typeConverter=TypeConverters.toString)
    
    backoffs = Param(Params._dummy(), "backoffs", "array of backoffs to use in the handler", typeConverter=TypeConverters.toListInt)
    
    displayName = Param(Params._dummy(), "displayName", "optional field, name of the model", typeConverter=TypeConverters.toString)
    
    endTime = Param(Params._dummy(), "endTime", "A required field, end time of data to be used for detection/generating multivariate anomaly detection model, should be date-time.", typeConverter=TypeConverters.toString)
    
    errorCol = Param(Params._dummy(), "errorCol", "column to hold http errors", typeConverter=TypeConverters.toString)
    
    fillNAMethod = Param(Params._dummy(), "fillNAMethod", "An optional field, indicates how missed values will be filled with. Can not be set to NotFill, when alignMode is Outer.{Previous, Subsequent, Linear, Zero, Fixed}", typeConverter=TypeConverters.toString)
    
    initialPollingDelay = Param(Params._dummy(), "initialPollingDelay", "number of milliseconds to wait before first poll for result", typeConverter=TypeConverters.toInt)
    
    inputCols = Param(Params._dummy(), "inputCols", "The names of the input columns", typeConverter=TypeConverters.toListString)
    
    intermediateSaveDir = Param(Params._dummy(), "intermediateSaveDir", "Blob storage location in HDFS where intermediate data is saved while training.", typeConverter=TypeConverters.toString)
    
    maxPollingRetries = Param(Params._dummy(), "maxPollingRetries", "number of times to poll", typeConverter=TypeConverters.toInt)
    
    outputCol = Param(Params._dummy(), "outputCol", "The name of the output column", typeConverter=TypeConverters.toString)
    
    paddingValue = Param(Params._dummy(), "paddingValue", "optional field, is only useful if FillNAMethod is set to Fixed.", typeConverter=TypeConverters.toInt)
    
    pollingDelay = Param(Params._dummy(), "pollingDelay", "number of milliseconds to wait between polling", typeConverter=TypeConverters.toInt)
    
    slidingWindow = Param(Params._dummy(), "slidingWindow", "An optional field, indicates how many history points will be used to determine the anomaly score of one subsequent point.", typeConverter=TypeConverters.toInt)
    
    startTime = Param(Params._dummy(), "startTime", "A required field, start time of data to be used for detection/generating multivariate anomaly detection model, should be date-time.", typeConverter=TypeConverters.toString)
    
    subscriptionKey = Param(Params._dummy(), "subscriptionKey", "ServiceParam: the API key to use")
    
    suppressMaxRetriesException = Param(Params._dummy(), "suppressMaxRetriesException", "set true to suppress the maxumimum retries exception and report in the error column", typeConverter=TypeConverters.toBoolean)
    
    timestampCol = Param(Params._dummy(), "timestampCol", "Timestamp column name", typeConverter=TypeConverters.toString)
    
    url = Param(Params._dummy(), "url", "Url of the service", typeConverter=TypeConverters.toString)

    
    @keyword_only
    def __init__(
        self,
        java_obj=None,
        alignMode="Outer",
        backoffs=[100,500,1000],
        displayName=None,
        endTime=None,
        errorCol="SimpleFitMultivariateAnomaly_735294d88294_error",
        fillNAMethod="Linear",
        initialPollingDelay=300,
        inputCols=None,
        intermediateSaveDir=None,
        maxPollingRetries=1000,
        outputCol="SimpleFitMultivariateAnomaly_735294d88294_output",
        paddingValue=None,
        pollingDelay=300,
        slidingWindow=300,
        startTime=None,
        subscriptionKey=None,
        subscriptionKeyCol=None,
        suppressMaxRetriesException=False,
        timestampCol="timestamp",
        url=None
        ):
        super(SimpleFitMultivariateAnomaly, self).__init__()
        if java_obj is None:
            self._java_obj = self._new_java_obj("com.microsoft.azure.synapse.ml.services.anomaly.SimpleFitMultivariateAnomaly", self.uid)
        else:
            self._java_obj = java_obj
        self._setDefault(alignMode="Outer")
        self._setDefault(backoffs=[100,500,1000])
        self._setDefault(errorCol="SimpleFitMultivariateAnomaly_735294d88294_error")
        self._setDefault(fillNAMethod="Linear")
        self._setDefault(initialPollingDelay=300)
        self._setDefault(maxPollingRetries=1000)
        self._setDefault(outputCol="SimpleFitMultivariateAnomaly_735294d88294_output")
        self._setDefault(pollingDelay=300)
        self._setDefault(slidingWindow=300)
        self._setDefault(suppressMaxRetriesException=False)
        self._setDefault(timestampCol="timestamp")
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
        alignMode="Outer",
        backoffs=[100,500,1000],
        displayName=None,
        endTime=None,
        errorCol="SimpleFitMultivariateAnomaly_735294d88294_error",
        fillNAMethod="Linear",
        initialPollingDelay=300,
        inputCols=None,
        intermediateSaveDir=None,
        maxPollingRetries=1000,
        outputCol="SimpleFitMultivariateAnomaly_735294d88294_output",
        paddingValue=None,
        pollingDelay=300,
        slidingWindow=300,
        startTime=None,
        subscriptionKey=None,
        subscriptionKeyCol=None,
        suppressMaxRetriesException=False,
        timestampCol="timestamp",
        url=None
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
        return "com.microsoft.azure.synapse.ml.services.anomaly.SimpleFitMultivariateAnomaly"

    @staticmethod
    def _from_java(java_stage):
        module_name=SimpleFitMultivariateAnomaly.__module__
        module_name=module_name.rsplit(".", 1)[0] + ".SimpleFitMultivariateAnomaly"
        return from_java(java_stage, module_name)

    def setAlignMode(self, value):
        """
        Args:
            alignMode: An optional field, indicates how we align different variables into the same time-range which is required by the model.{Inner, Outer}
        """
        self._set(alignMode=value)
        return self
    
    def setBackoffs(self, value):
        """
        Args:
            backoffs: array of backoffs to use in the handler
        """
        self._set(backoffs=value)
        return self
    
    def setDisplayName(self, value):
        """
        Args:
            displayName: optional field, name of the model
        """
        self._set(displayName=value)
        return self
    
    def setEndTime(self, value):
        """
        Args:
            endTime: A required field, end time of data to be used for detection/generating multivariate anomaly detection model, should be date-time.
        """
        self._set(endTime=value)
        return self
    
    def setErrorCol(self, value):
        """
        Args:
            errorCol: column to hold http errors
        """
        self._set(errorCol=value)
        return self
    
    def setFillNAMethod(self, value):
        """
        Args:
            fillNAMethod: An optional field, indicates how missed values will be filled with. Can not be set to NotFill, when alignMode is Outer.{Previous, Subsequent, Linear, Zero, Fixed}
        """
        self._set(fillNAMethod=value)
        return self
    
    def setInitialPollingDelay(self, value):
        """
        Args:
            initialPollingDelay: number of milliseconds to wait before first poll for result
        """
        self._set(initialPollingDelay=value)
        return self
    
    def setInputCols(self, value):
        """
        Args:
            inputCols: The names of the input columns
        """
        self._set(inputCols=value)
        return self
    
    def setIntermediateSaveDir(self, value):
        """
        Args:
            intermediateSaveDir: Blob storage location in HDFS where intermediate data is saved while training.
        """
        self._set(intermediateSaveDir=value)
        return self
    
    def setMaxPollingRetries(self, value):
        """
        Args:
            maxPollingRetries: number of times to poll
        """
        self._set(maxPollingRetries=value)
        return self
    
    def setOutputCol(self, value):
        """
        Args:
            outputCol: The name of the output column
        """
        self._set(outputCol=value)
        return self
    
    def setPaddingValue(self, value):
        """
        Args:
            paddingValue: optional field, is only useful if FillNAMethod is set to Fixed.
        """
        self._set(paddingValue=value)
        return self
    
    def setPollingDelay(self, value):
        """
        Args:
            pollingDelay: number of milliseconds to wait between polling
        """
        self._set(pollingDelay=value)
        return self
    
    def setSlidingWindow(self, value):
        """
        Args:
            slidingWindow: An optional field, indicates how many history points will be used to determine the anomaly score of one subsequent point.
        """
        self._set(slidingWindow=value)
        return self
    
    def setStartTime(self, value):
        """
        Args:
            startTime: A required field, start time of data to be used for detection/generating multivariate anomaly detection model, should be date-time.
        """
        self._set(startTime=value)
        return self
    
    def setSubscriptionKey(self, value):
        """
        Args:
            subscriptionKey: the API key to use
        """
        if isinstance(value, list):
            value = SparkContext._active_spark_context._jvm.com.microsoft.azure.synapse.ml.param.ServiceParam.toSeq(value)
        elif isinstance(value, dict):
            # Recursively convert Python dict/list to Java LinkedHashMap/ArrayList to preserve order
            sc = SparkContext._active_spark_context
            jvm = sc._jvm
            def _convert(val):
                if isinstance(val, dict):
                    jmap = jvm.java.util.LinkedHashMap()
                    for k, v in val.items():
                        jmap.put(k, _convert(v))
                    return jmap
                elif isinstance(val, list):
                    jlist = jvm.java.util.ArrayList()
                    for it in val:
                        jlist.add(_convert(it))
                    return jlist
                else:
                    return val
            value = jvm.com.microsoft.azure.synapse.ml.param.ServiceParam.toMap(_convert(value))
        self._java_obj = self._java_obj.setSubscriptionKey(value)
        return self
    
    def setSubscriptionKeyCol(self, value):
        """
        Args:
            subscriptionKey: the API key to use
        """
        self._java_obj = self._java_obj.setSubscriptionKeyCol(value)
        return self
    
    def setSuppressMaxRetriesException(self, value):
        """
        Args:
            suppressMaxRetriesException: set true to suppress the maxumimum retries exception and report in the error column
        """
        self._set(suppressMaxRetriesException=value)
        return self
    
    def setTimestampCol(self, value):
        """
        Args:
            timestampCol: Timestamp column name
        """
        self._set(timestampCol=value)
        return self
    
    def setUrl(self, value):
        """
        Args:
            url: Url of the service
        """
        self._set(url=value)
        return self

    
    def getAlignMode(self):
        """
        Returns:
            alignMode: An optional field, indicates how we align different variables into the same time-range which is required by the model.{Inner, Outer}
        """
        return self.getOrDefault(self.alignMode)
    
    
    def getBackoffs(self):
        """
        Returns:
            backoffs: array of backoffs to use in the handler
        """
        return self.getOrDefault(self.backoffs)
    
    
    def getDisplayName(self):
        """
        Returns:
            displayName: optional field, name of the model
        """
        return self.getOrDefault(self.displayName)
    
    
    def getEndTime(self):
        """
        Returns:
            endTime: A required field, end time of data to be used for detection/generating multivariate anomaly detection model, should be date-time.
        """
        return self.getOrDefault(self.endTime)
    
    
    def getErrorCol(self):
        """
        Returns:
            errorCol: column to hold http errors
        """
        return self.getOrDefault(self.errorCol)
    
    
    def getFillNAMethod(self):
        """
        Returns:
            fillNAMethod: An optional field, indicates how missed values will be filled with. Can not be set to NotFill, when alignMode is Outer.{Previous, Subsequent, Linear, Zero, Fixed}
        """
        return self.getOrDefault(self.fillNAMethod)
    
    
    def getInitialPollingDelay(self):
        """
        Returns:
            initialPollingDelay: number of milliseconds to wait before first poll for result
        """
        return self.getOrDefault(self.initialPollingDelay)
    
    
    def getInputCols(self):
        """
        Returns:
            inputCols: The names of the input columns
        """
        return self.getOrDefault(self.inputCols)
    
    
    def getIntermediateSaveDir(self):
        """
        Returns:
            intermediateSaveDir: Blob storage location in HDFS where intermediate data is saved while training.
        """
        return self.getOrDefault(self.intermediateSaveDir)
    
    
    def getMaxPollingRetries(self):
        """
        Returns:
            maxPollingRetries: number of times to poll
        """
        return self.getOrDefault(self.maxPollingRetries)
    
    
    def getOutputCol(self):
        """
        Returns:
            outputCol: The name of the output column
        """
        return self.getOrDefault(self.outputCol)
    
    
    def getPaddingValue(self):
        """
        Returns:
            paddingValue: optional field, is only useful if FillNAMethod is set to Fixed.
        """
        return self.getOrDefault(self.paddingValue)
    
    
    def getPollingDelay(self):
        """
        Returns:
            pollingDelay: number of milliseconds to wait between polling
        """
        return self.getOrDefault(self.pollingDelay)
    
    
    def getSlidingWindow(self):
        """
        Returns:
            slidingWindow: An optional field, indicates how many history points will be used to determine the anomaly score of one subsequent point.
        """
        return self.getOrDefault(self.slidingWindow)
    
    
    def getStartTime(self):
        """
        Returns:
            startTime: A required field, start time of data to be used for detection/generating multivariate anomaly detection model, should be date-time.
        """
        return self.getOrDefault(self.startTime)
    
    
    def getSubscriptionKey(self):
        """
        Returns:
            subscriptionKey: the API key to use
        """
        return self._java_obj.getSubscriptionKey()
    
    
    def getSuppressMaxRetriesException(self):
        """
        Returns:
            suppressMaxRetriesException: set true to suppress the maxumimum retries exception and report in the error column
        """
        return self.getOrDefault(self.suppressMaxRetriesException)
    
    
    def getTimestampCol(self):
        """
        Returns:
            timestampCol: Timestamp column name
        """
        return self.getOrDefault(self.timestampCol)
    
    
    def getUrl(self):
        """
        Returns:
            url: Url of the service
        """
        return self.getOrDefault(self.url)

    def _create_model(self, java_model):
        try:
            model = SimpleDetectMultivariateAnomaly(java_obj=java_model)
            model._transfer_params_from_java()
        except TypeError:
            model = SimpleDetectMultivariateAnomaly._from_java(java_model)
        return model
    
    def _fit(self, dataset):
        java_model = self._fit_java(dataset)
        return self._create_model(java_model)

    
    def setLocation(self, value):
        self._java_obj = self._java_obj.setLocation(value)
        return self
    
    def cleanUpIntermediateData(self):
        self._java_obj.cleanUpIntermediateData()
        return
        