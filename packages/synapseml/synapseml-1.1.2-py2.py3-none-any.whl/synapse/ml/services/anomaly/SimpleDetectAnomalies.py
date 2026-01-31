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
class SimpleDetectAnomalies(ComplexParamsMixin, JavaMLReadable, JavaMLWritable, JavaTransformer):
    """
    Args:
        AADToken (object): AAD Token used for authentication
        CustomAuthHeader (object): A Custom Value for Authorization Header
        concurrency (int): max number of concurrent calls
        concurrentTimeout (float): max number seconds to wait on futures if concurrency >= 1
        customHeaders (object): Map of Custom Header Key-Value Tuples.
        customInterval (object):  Custom Interval is used to set non-standard time interval, for example, if the series is 5 minutes,  request can be set as granularity=minutely, customInterval=5.     
        customUrlRoot (str): The custom URL root for the service. This will not append OpenAI specific model path completions (i.e. /chat/completions) to the URL.
        errorCol (str): column to hold http errors
        granularity (object):  Can only be one of yearly, monthly, weekly, daily, hourly or minutely. Granularity is used for verify whether input series is valid.     
        groupbyCol (str): column that groups the series
        handler (object): Which strategy to use when handling requests
        imputeFixedValue (object):  Optional argument, fixed value to use when imputeMode is set to "fixed"     
        imputeMode (object):  Optional argument, impute mode of a time series. Possible values: auto, previous, linear, fixed, zero, notFill     
        maxAnomalyRatio (object):  Optional argument, advanced model parameter, max anomaly ratio in a time series.     
        outputCol (str): The name of the output column
        period (object):  Optional argument, periodic value of a time series. If the value is null or does not present, the API will determine the period automatically.     
        sensitivity (object):  Optional argument, advanced model parameter, between 0-99, the lower the value is, the larger the margin value will be which means less anomalies will be accepted     
        series (object):  Time series data points. Points should be sorted by timestamp in ascending order to match the anomaly detection result. If the data is not sorted correctly or there is duplicated timestamp, the API will not work. In such case, an error message will be returned.     
        subscriptionKey (object): the API key to use
        telemHeaders (object): Map of Custom Header Key-Value Tuples.
        timeout (float): number of seconds to wait before closing the connection
        timestampCol (str): column representing the time of the series
        url (str): Url of the service
        valueCol (str): column representing the value of the series
    """

    AADToken = Param(Params._dummy(), "AADToken", "ServiceParam: AAD Token used for authentication")
    
    CustomAuthHeader = Param(Params._dummy(), "CustomAuthHeader", "ServiceParam: A Custom Value for Authorization Header")
    
    concurrency = Param(Params._dummy(), "concurrency", "max number of concurrent calls", typeConverter=TypeConverters.toInt)
    
    concurrentTimeout = Param(Params._dummy(), "concurrentTimeout", "max number seconds to wait on futures if concurrency >= 1", typeConverter=TypeConverters.toFloat)
    
    customHeaders = Param(Params._dummy(), "customHeaders", "ServiceParam: Map of Custom Header Key-Value Tuples.")
    
    customInterval = Param(Params._dummy(), "customInterval", "ServiceParam:  Custom Interval is used to set non-standard time interval, for example, if the series is 5 minutes,  request can be set as granularity=minutely, customInterval=5.     ")
    
    customUrlRoot = Param(Params._dummy(), "customUrlRoot", "The custom URL root for the service. This will not append OpenAI specific model path completions (i.e. /chat/completions) to the URL.", typeConverter=TypeConverters.toString)
    
    errorCol = Param(Params._dummy(), "errorCol", "column to hold http errors", typeConverter=TypeConverters.toString)
    
    granularity = Param(Params._dummy(), "granularity", "ServiceParam:  Can only be one of yearly, monthly, weekly, daily, hourly or minutely. Granularity is used for verify whether input series is valid.     ")
    
    groupbyCol = Param(Params._dummy(), "groupbyCol", "column that groups the series", typeConverter=TypeConverters.toString)
    
    handler = Param(Params._dummy(), "handler", "Which strategy to use when handling requests")
    
    imputeFixedValue = Param(Params._dummy(), "imputeFixedValue", "ServiceParam:  Optional argument, fixed value to use when imputeMode is set to \"fixed\"     ")
    
    imputeMode = Param(Params._dummy(), "imputeMode", "ServiceParam:  Optional argument, impute mode of a time series. Possible values: auto, previous, linear, fixed, zero, notFill     ")
    
    maxAnomalyRatio = Param(Params._dummy(), "maxAnomalyRatio", "ServiceParam:  Optional argument, advanced model parameter, max anomaly ratio in a time series.     ")
    
    outputCol = Param(Params._dummy(), "outputCol", "The name of the output column", typeConverter=TypeConverters.toString)
    
    period = Param(Params._dummy(), "period", "ServiceParam:  Optional argument, periodic value of a time series. If the value is null or does not present, the API will determine the period automatically.     ")
    
    sensitivity = Param(Params._dummy(), "sensitivity", "ServiceParam:  Optional argument, advanced model parameter, between 0-99, the lower the value is, the larger the margin value will be which means less anomalies will be accepted     ")
    
    series = Param(Params._dummy(), "series", "ServiceParam:  Time series data points. Points should be sorted by timestamp in ascending order to match the anomaly detection result. If the data is not sorted correctly or there is duplicated timestamp, the API will not work. In such case, an error message will be returned.     ")
    
    subscriptionKey = Param(Params._dummy(), "subscriptionKey", "ServiceParam: the API key to use")
    
    telemHeaders = Param(Params._dummy(), "telemHeaders", "ServiceParam: Map of Custom Header Key-Value Tuples.")
    
    timeout = Param(Params._dummy(), "timeout", "number of seconds to wait before closing the connection", typeConverter=TypeConverters.toFloat)
    
    timestampCol = Param(Params._dummy(), "timestampCol", "column representing the time of the series", typeConverter=TypeConverters.toString)
    
    url = Param(Params._dummy(), "url", "Url of the service", typeConverter=TypeConverters.toString)
    
    valueCol = Param(Params._dummy(), "valueCol", "column representing the value of the series", typeConverter=TypeConverters.toString)

    
    @keyword_only
    def __init__(
        self,
        java_obj=None,
        AADToken=None,
        AADTokenCol=None,
        CustomAuthHeader=None,
        CustomAuthHeaderCol=None,
        concurrency=1,
        concurrentTimeout=None,
        customHeaders=None,
        customHeadersCol=None,
        customInterval=None,
        customIntervalCol=None,
        customUrlRoot=None,
        errorCol="SimpleDetectAnomalies_dea468448a77_error",
        granularity=None,
        granularityCol=None,
        groupbyCol=None,
        handler=None,
        imputeFixedValue=None,
        imputeFixedValueCol=None,
        imputeMode=None,
        imputeModeCol=None,
        maxAnomalyRatio=None,
        maxAnomalyRatioCol=None,
        outputCol="SimpleDetectAnomalies_dea468448a77_output",
        period=None,
        periodCol=None,
        sensitivity=None,
        sensitivityCol=None,
        series=None,
        seriesCol=None,
        subscriptionKey=None,
        subscriptionKeyCol=None,
        telemHeaders=None,
        telemHeadersCol=None,
        timeout=60.0,
        timestampCol="timestamp",
        url=None,
        valueCol="value"
        ):
        super(SimpleDetectAnomalies, self).__init__()
        if java_obj is None:
            self._java_obj = self._new_java_obj("com.microsoft.azure.synapse.ml.services.anomaly.SimpleDetectAnomalies", self.uid)
        else:
            self._java_obj = java_obj
        self._setDefault(concurrency=1)
        self._setDefault(errorCol="SimpleDetectAnomalies_dea468448a77_error")
        self._setDefault(outputCol="SimpleDetectAnomalies_dea468448a77_output")
        self._setDefault(timeout=60.0)
        self._setDefault(timestampCol="timestamp")
        self._setDefault(valueCol="value")
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
        AADToken=None,
        AADTokenCol=None,
        CustomAuthHeader=None,
        CustomAuthHeaderCol=None,
        concurrency=1,
        concurrentTimeout=None,
        customHeaders=None,
        customHeadersCol=None,
        customInterval=None,
        customIntervalCol=None,
        customUrlRoot=None,
        errorCol="SimpleDetectAnomalies_dea468448a77_error",
        granularity=None,
        granularityCol=None,
        groupbyCol=None,
        handler=None,
        imputeFixedValue=None,
        imputeFixedValueCol=None,
        imputeMode=None,
        imputeModeCol=None,
        maxAnomalyRatio=None,
        maxAnomalyRatioCol=None,
        outputCol="SimpleDetectAnomalies_dea468448a77_output",
        period=None,
        periodCol=None,
        sensitivity=None,
        sensitivityCol=None,
        series=None,
        seriesCol=None,
        subscriptionKey=None,
        subscriptionKeyCol=None,
        telemHeaders=None,
        telemHeadersCol=None,
        timeout=60.0,
        timestampCol="timestamp",
        url=None,
        valueCol="value"
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
        return "com.microsoft.azure.synapse.ml.services.anomaly.SimpleDetectAnomalies"

    @staticmethod
    def _from_java(java_stage):
        module_name=SimpleDetectAnomalies.__module__
        module_name=module_name.rsplit(".", 1)[0] + ".SimpleDetectAnomalies"
        return from_java(java_stage, module_name)

    def setAADToken(self, value):
        """
        Args:
            AADToken: AAD Token used for authentication
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
        self._java_obj = self._java_obj.setAADToken(value)
        return self
    
    def setAADTokenCol(self, value):
        """
        Args:
            AADToken: AAD Token used for authentication
        """
        self._java_obj = self._java_obj.setAADTokenCol(value)
        return self
    
    def setCustomAuthHeader(self, value):
        """
        Args:
            CustomAuthHeader: A Custom Value for Authorization Header
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
        self._java_obj = self._java_obj.setCustomAuthHeader(value)
        return self
    
    def setCustomAuthHeaderCol(self, value):
        """
        Args:
            CustomAuthHeader: A Custom Value for Authorization Header
        """
        self._java_obj = self._java_obj.setCustomAuthHeaderCol(value)
        return self
    
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
    
    def setCustomHeaders(self, value):
        """
        Args:
            customHeaders: Map of Custom Header Key-Value Tuples.
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
        self._java_obj = self._java_obj.setCustomHeaders(value)
        return self
    
    def setCustomHeadersCol(self, value):
        """
        Args:
            customHeaders: Map of Custom Header Key-Value Tuples.
        """
        self._java_obj = self._java_obj.setCustomHeadersCol(value)
        return self
    
    def setCustomInterval(self, value):
        """
        Args:
            customInterval:  Custom Interval is used to set non-standard time interval, for example, if the series is 5 minutes,  request can be set as granularity=minutely, customInterval=5.     
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
        self._java_obj = self._java_obj.setCustomInterval(value)
        return self
    
    def setCustomIntervalCol(self, value):
        """
        Args:
            customInterval:  Custom Interval is used to set non-standard time interval, for example, if the series is 5 minutes,  request can be set as granularity=minutely, customInterval=5.     
        """
        self._java_obj = self._java_obj.setCustomIntervalCol(value)
        return self
    
    def setCustomUrlRoot(self, value):
        """
        Args:
            customUrlRoot: The custom URL root for the service. This will not append OpenAI specific model path completions (i.e. /chat/completions) to the URL.
        """
        self._set(customUrlRoot=value)
        return self
    
    def setErrorCol(self, value):
        """
        Args:
            errorCol: column to hold http errors
        """
        self._set(errorCol=value)
        return self
    
    def setGranularity(self, value):
        """
        Args:
            granularity:  Can only be one of yearly, monthly, weekly, daily, hourly or minutely. Granularity is used for verify whether input series is valid.     
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
        self._java_obj = self._java_obj.setGranularity(value)
        return self
    
    def setGranularityCol(self, value):
        """
        Args:
            granularity:  Can only be one of yearly, monthly, weekly, daily, hourly or minutely. Granularity is used for verify whether input series is valid.     
        """
        self._java_obj = self._java_obj.setGranularityCol(value)
        return self
    
    def setGroupbyCol(self, value):
        """
        Args:
            groupbyCol: column that groups the series
        """
        self._set(groupbyCol=value)
        return self
    
    def setHandler(self, value):
        """
        Args:
            handler: Which strategy to use when handling requests
        """
        self._set(handler=value)
        return self
    
    def setImputeFixedValue(self, value):
        """
        Args:
            imputeFixedValue:  Optional argument, fixed value to use when imputeMode is set to "fixed"     
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
        self._java_obj = self._java_obj.setImputeFixedValue(value)
        return self
    
    def setImputeFixedValueCol(self, value):
        """
        Args:
            imputeFixedValue:  Optional argument, fixed value to use when imputeMode is set to "fixed"     
        """
        self._java_obj = self._java_obj.setImputeFixedValueCol(value)
        return self
    
    def setImputeMode(self, value):
        """
        Args:
            imputeMode:  Optional argument, impute mode of a time series. Possible values: auto, previous, linear, fixed, zero, notFill     
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
        self._java_obj = self._java_obj.setImputeMode(value)
        return self
    
    def setImputeModeCol(self, value):
        """
        Args:
            imputeMode:  Optional argument, impute mode of a time series. Possible values: auto, previous, linear, fixed, zero, notFill     
        """
        self._java_obj = self._java_obj.setImputeModeCol(value)
        return self
    
    def setMaxAnomalyRatio(self, value):
        """
        Args:
            maxAnomalyRatio:  Optional argument, advanced model parameter, max anomaly ratio in a time series.     
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
        self._java_obj = self._java_obj.setMaxAnomalyRatio(value)
        return self
    
    def setMaxAnomalyRatioCol(self, value):
        """
        Args:
            maxAnomalyRatio:  Optional argument, advanced model parameter, max anomaly ratio in a time series.     
        """
        self._java_obj = self._java_obj.setMaxAnomalyRatioCol(value)
        return self
    
    def setOutputCol(self, value):
        """
        Args:
            outputCol: The name of the output column
        """
        self._set(outputCol=value)
        return self
    
    def setPeriod(self, value):
        """
        Args:
            period:  Optional argument, periodic value of a time series. If the value is null or does not present, the API will determine the period automatically.     
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
        self._java_obj = self._java_obj.setPeriod(value)
        return self
    
    def setPeriodCol(self, value):
        """
        Args:
            period:  Optional argument, periodic value of a time series. If the value is null or does not present, the API will determine the period automatically.     
        """
        self._java_obj = self._java_obj.setPeriodCol(value)
        return self
    
    def setSensitivity(self, value):
        """
        Args:
            sensitivity:  Optional argument, advanced model parameter, between 0-99, the lower the value is, the larger the margin value will be which means less anomalies will be accepted     
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
        self._java_obj = self._java_obj.setSensitivity(value)
        return self
    
    def setSensitivityCol(self, value):
        """
        Args:
            sensitivity:  Optional argument, advanced model parameter, between 0-99, the lower the value is, the larger the margin value will be which means less anomalies will be accepted     
        """
        self._java_obj = self._java_obj.setSensitivityCol(value)
        return self
    
    def setSeries(self, value):
        """
        Args:
            series:  Time series data points. Points should be sorted by timestamp in ascending order to match the anomaly detection result. If the data is not sorted correctly or there is duplicated timestamp, the API will not work. In such case, an error message will be returned.     
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
        self._java_obj = self._java_obj.setSeries(value)
        return self
    
    def setSeriesCol(self, value):
        """
        Args:
            series:  Time series data points. Points should be sorted by timestamp in ascending order to match the anomaly detection result. If the data is not sorted correctly or there is duplicated timestamp, the API will not work. In such case, an error message will be returned.     
        """
        self._java_obj = self._java_obj.setSeriesCol(value)
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
    
    def setTelemHeaders(self, value):
        """
        Args:
            telemHeaders: Map of Custom Header Key-Value Tuples.
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
        self._java_obj = self._java_obj.setTelemHeaders(value)
        return self
    
    def setTelemHeadersCol(self, value):
        """
        Args:
            telemHeaders: Map of Custom Header Key-Value Tuples.
        """
        self._java_obj = self._java_obj.setTelemHeadersCol(value)
        return self
    
    def setTimeout(self, value):
        """
        Args:
            timeout: number of seconds to wait before closing the connection
        """
        self._set(timeout=value)
        return self
    
    def setTimestampCol(self, value):
        """
        Args:
            timestampCol: column representing the time of the series
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
    
    def setValueCol(self, value):
        """
        Args:
            valueCol: column representing the value of the series
        """
        self._set(valueCol=value)
        return self

    
    def getAADToken(self):
        """
        Returns:
            AADToken: AAD Token used for authentication
        """
        return self._java_obj.getAADToken()
    
    
    def getCustomAuthHeader(self):
        """
        Returns:
            CustomAuthHeader: A Custom Value for Authorization Header
        """
        return self._java_obj.getCustomAuthHeader()
    
    
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
    
    
    def getCustomHeaders(self):
        """
        Returns:
            customHeaders: Map of Custom Header Key-Value Tuples.
        """
        return self._java_obj.getCustomHeaders()
    
    
    def getCustomInterval(self):
        """
        Returns:
            customInterval:  Custom Interval is used to set non-standard time interval, for example, if the series is 5 minutes,  request can be set as granularity=minutely, customInterval=5.     
        """
        return self._java_obj.getCustomInterval()
    
    
    def getCustomUrlRoot(self):
        """
        Returns:
            customUrlRoot: The custom URL root for the service. This will not append OpenAI specific model path completions (i.e. /chat/completions) to the URL.
        """
        return self.getOrDefault(self.customUrlRoot)
    
    
    def getErrorCol(self):
        """
        Returns:
            errorCol: column to hold http errors
        """
        return self.getOrDefault(self.errorCol)
    
    
    def getGranularity(self):
        """
        Returns:
            granularity:  Can only be one of yearly, monthly, weekly, daily, hourly or minutely. Granularity is used for verify whether input series is valid.     
        """
        return self._java_obj.getGranularity()
    
    
    def getGroupbyCol(self):
        """
        Returns:
            groupbyCol: column that groups the series
        """
        return self.getOrDefault(self.groupbyCol)
    
    
    def getHandler(self):
        """
        Returns:
            handler: Which strategy to use when handling requests
        """
        return self.getOrDefault(self.handler)
    
    
    def getImputeFixedValue(self):
        """
        Returns:
            imputeFixedValue:  Optional argument, fixed value to use when imputeMode is set to "fixed"     
        """
        return self._java_obj.getImputeFixedValue()
    
    
    def getImputeMode(self):
        """
        Returns:
            imputeMode:  Optional argument, impute mode of a time series. Possible values: auto, previous, linear, fixed, zero, notFill     
        """
        return self._java_obj.getImputeMode()
    
    
    def getMaxAnomalyRatio(self):
        """
        Returns:
            maxAnomalyRatio:  Optional argument, advanced model parameter, max anomaly ratio in a time series.     
        """
        return self._java_obj.getMaxAnomalyRatio()
    
    
    def getOutputCol(self):
        """
        Returns:
            outputCol: The name of the output column
        """
        return self.getOrDefault(self.outputCol)
    
    
    def getPeriod(self):
        """
        Returns:
            period:  Optional argument, periodic value of a time series. If the value is null or does not present, the API will determine the period automatically.     
        """
        return self._java_obj.getPeriod()
    
    
    def getSensitivity(self):
        """
        Returns:
            sensitivity:  Optional argument, advanced model parameter, between 0-99, the lower the value is, the larger the margin value will be which means less anomalies will be accepted     
        """
        return self._java_obj.getSensitivity()
    
    
    def getSeries(self):
        """
        Returns:
            series:  Time series data points. Points should be sorted by timestamp in ascending order to match the anomaly detection result. If the data is not sorted correctly or there is duplicated timestamp, the API will not work. In such case, an error message will be returned.     
        """
        return self._java_obj.getSeries()
    
    
    def getSubscriptionKey(self):
        """
        Returns:
            subscriptionKey: the API key to use
        """
        return self._java_obj.getSubscriptionKey()
    
    
    def getTelemHeaders(self):
        """
        Returns:
            telemHeaders: Map of Custom Header Key-Value Tuples.
        """
        return self._java_obj.getTelemHeaders()
    
    
    def getTimeout(self):
        """
        Returns:
            timeout: number of seconds to wait before closing the connection
        """
        return self.getOrDefault(self.timeout)
    
    
    def getTimestampCol(self):
        """
        Returns:
            timestampCol: column representing the time of the series
        """
        return self.getOrDefault(self.timestampCol)
    
    
    def getUrl(self):
        """
        Returns:
            url: Url of the service
        """
        return self.getOrDefault(self.url)
    
    
    def getValueCol(self):
        """
        Returns:
            valueCol: column representing the value of the series
        """
        return self.getOrDefault(self.valueCol)

    

    def setCustomServiceName(self, value):
        self._java_obj = self._java_obj.setCustomServiceName(value)
        return self
    
    def setEndpoint(self, value):
        self._java_obj = self._java_obj.setEndpoint(value)
        return self
    
    def setDefaultInternalEndpoint(self, value):
        self._java_obj = self._java_obj.setDefaultInternalEndpoint(value)
        return self
    
    def _transform(self, dataset: DataFrame) -> DataFrame:
        return super()._transform(dataset)
    
    def setLocation(self, value):
        self._java_obj = self._java_obj.setLocation(value)
        return self
    
    def setLinkedService(self, value):
        self._java_obj = self._java_obj.setLinkedService(value)
        return self
        