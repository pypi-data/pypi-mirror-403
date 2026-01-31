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
class ReverseAddressGeocoder(ComplexParamsMixin, JavaMLReadable, JavaMLWritable, JavaTransformer):
    """
    Args:
        AADToken (object): AAD Token used for authentication
        backoffs (list): array of backoffs to use in the handler
        concurrency (int): max number of concurrent calls
        concurrentTimeout (float): max number seconds to wait on futures if concurrency >= 1
        errorCol (str): column to hold http errors
        initialPollingDelay (int): number of milliseconds to wait before first poll for result
        latitude (object): the latitude of location
        longitude (object): the longitude of location
        maxPollingRetries (int): number of times to poll
        outputCol (str): The name of the output column
        pollingDelay (int): number of milliseconds to wait between polling
        subscriptionKey (object): the API key to use
        suppressMaxRetriesException (bool): set true to suppress the maxumimum retries exception and report in the error column
        timeout (float): number of seconds to wait before closing the connection
        url (str): Url of the service
    """

    AADToken = Param(Params._dummy(), "AADToken", "ServiceParam: AAD Token used for authentication")
    
    backoffs = Param(Params._dummy(), "backoffs", "array of backoffs to use in the handler", typeConverter=TypeConverters.toListInt)
    
    concurrency = Param(Params._dummy(), "concurrency", "max number of concurrent calls", typeConverter=TypeConverters.toInt)
    
    concurrentTimeout = Param(Params._dummy(), "concurrentTimeout", "max number seconds to wait on futures if concurrency >= 1", typeConverter=TypeConverters.toFloat)
    
    errorCol = Param(Params._dummy(), "errorCol", "column to hold http errors", typeConverter=TypeConverters.toString)
    
    initialPollingDelay = Param(Params._dummy(), "initialPollingDelay", "number of milliseconds to wait before first poll for result", typeConverter=TypeConverters.toInt)
    
    latitude = Param(Params._dummy(), "latitude", "ServiceParam: the latitude of location")
    
    longitude = Param(Params._dummy(), "longitude", "ServiceParam: the longitude of location")
    
    maxPollingRetries = Param(Params._dummy(), "maxPollingRetries", "number of times to poll", typeConverter=TypeConverters.toInt)
    
    outputCol = Param(Params._dummy(), "outputCol", "The name of the output column", typeConverter=TypeConverters.toString)
    
    pollingDelay = Param(Params._dummy(), "pollingDelay", "number of milliseconds to wait between polling", typeConverter=TypeConverters.toInt)
    
    subscriptionKey = Param(Params._dummy(), "subscriptionKey", "ServiceParam: the API key to use")
    
    suppressMaxRetriesException = Param(Params._dummy(), "suppressMaxRetriesException", "set true to suppress the maxumimum retries exception and report in the error column", typeConverter=TypeConverters.toBoolean)
    
    timeout = Param(Params._dummy(), "timeout", "number of seconds to wait before closing the connection", typeConverter=TypeConverters.toFloat)
    
    url = Param(Params._dummy(), "url", "Url of the service", typeConverter=TypeConverters.toString)

    
    @keyword_only
    def __init__(
        self,
        java_obj=None,
        AADToken=None,
        AADTokenCol=None,
        backoffs=[100,500,1000],
        concurrency=1,
        concurrentTimeout=None,
        errorCol="ReverseAddressGeocoder_fcce55936e38_error",
        initialPollingDelay=300,
        latitude=None,
        latitudeCol=None,
        longitude=None,
        longitudeCol=None,
        maxPollingRetries=1000,
        outputCol="ReverseAddressGeocoder_fcce55936e38_output",
        pollingDelay=300,
        subscriptionKey=None,
        subscriptionKeyCol=None,
        suppressMaxRetriesException=False,
        timeout=60.0,
        url="https://atlas.microsoft.com/search/address/reverse/batch/json"
        ):
        super(ReverseAddressGeocoder, self).__init__()
        if java_obj is None:
            self._java_obj = self._new_java_obj("com.microsoft.azure.synapse.ml.services.geospatial.ReverseAddressGeocoder", self.uid)
        else:
            self._java_obj = java_obj
        self._setDefault(backoffs=[100,500,1000])
        self._setDefault(concurrency=1)
        self._setDefault(errorCol="ReverseAddressGeocoder_fcce55936e38_error")
        self._setDefault(initialPollingDelay=300)
        self._setDefault(maxPollingRetries=1000)
        self._setDefault(outputCol="ReverseAddressGeocoder_fcce55936e38_output")
        self._setDefault(pollingDelay=300)
        self._setDefault(suppressMaxRetriesException=False)
        self._setDefault(timeout=60.0)
        self._setDefault(url="https://atlas.microsoft.com/search/address/reverse/batch/json")
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
        backoffs=[100,500,1000],
        concurrency=1,
        concurrentTimeout=None,
        errorCol="ReverseAddressGeocoder_fcce55936e38_error",
        initialPollingDelay=300,
        latitude=None,
        latitudeCol=None,
        longitude=None,
        longitudeCol=None,
        maxPollingRetries=1000,
        outputCol="ReverseAddressGeocoder_fcce55936e38_output",
        pollingDelay=300,
        subscriptionKey=None,
        subscriptionKeyCol=None,
        suppressMaxRetriesException=False,
        timeout=60.0,
        url="https://atlas.microsoft.com/search/address/reverse/batch/json"
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
        return "com.microsoft.azure.synapse.ml.services.geospatial.ReverseAddressGeocoder"

    @staticmethod
    def _from_java(java_stage):
        module_name=ReverseAddressGeocoder.__module__
        module_name=module_name.rsplit(".", 1)[0] + ".ReverseAddressGeocoder"
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
    
    def setBackoffs(self, value):
        """
        Args:
            backoffs: array of backoffs to use in the handler
        """
        self._set(backoffs=value)
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
    
    def setErrorCol(self, value):
        """
        Args:
            errorCol: column to hold http errors
        """
        self._set(errorCol=value)
        return self
    
    def setInitialPollingDelay(self, value):
        """
        Args:
            initialPollingDelay: number of milliseconds to wait before first poll for result
        """
        self._set(initialPollingDelay=value)
        return self
    
    def setLatitude(self, value):
        """
        Args:
            latitude: the latitude of location
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
        self._java_obj = self._java_obj.setLatitude(value)
        return self
    
    def setLatitudeCol(self, value):
        """
        Args:
            latitude: the latitude of location
        """
        self._java_obj = self._java_obj.setLatitudeCol(value)
        return self
    
    def setLongitude(self, value):
        """
        Args:
            longitude: the longitude of location
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
        self._java_obj = self._java_obj.setLongitude(value)
        return self
    
    def setLongitudeCol(self, value):
        """
        Args:
            longitude: the longitude of location
        """
        self._java_obj = self._java_obj.setLongitudeCol(value)
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
    
    def setPollingDelay(self, value):
        """
        Args:
            pollingDelay: number of milliseconds to wait between polling
        """
        self._set(pollingDelay=value)
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
    
    def setTimeout(self, value):
        """
        Args:
            timeout: number of seconds to wait before closing the connection
        """
        self._set(timeout=value)
        return self
    
    def setUrl(self, value):
        """
        Args:
            url: Url of the service
        """
        self._set(url=value)
        return self

    
    def getAADToken(self):
        """
        Returns:
            AADToken: AAD Token used for authentication
        """
        return self._java_obj.getAADToken()
    
    
    def getBackoffs(self):
        """
        Returns:
            backoffs: array of backoffs to use in the handler
        """
        return self.getOrDefault(self.backoffs)
    
    
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
    
    
    def getInitialPollingDelay(self):
        """
        Returns:
            initialPollingDelay: number of milliseconds to wait before first poll for result
        """
        return self.getOrDefault(self.initialPollingDelay)
    
    
    def getLatitude(self):
        """
        Returns:
            latitude: the latitude of location
        """
        return self._java_obj.getLatitude()
    
    
    def getLongitude(self):
        """
        Returns:
            longitude: the longitude of location
        """
        return self._java_obj.getLongitude()
    
    
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
    
    
    def getPollingDelay(self):
        """
        Returns:
            pollingDelay: number of milliseconds to wait between polling
        """
        return self.getOrDefault(self.pollingDelay)
    
    
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
    
    
    def getTimeout(self):
        """
        Returns:
            timeout: number of seconds to wait before closing the connection
        """
        return self.getOrDefault(self.timeout)
    
    
    def getUrl(self):
        """
        Returns:
            url: Url of the service
        """
        return self.getOrDefault(self.url)

    

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
        