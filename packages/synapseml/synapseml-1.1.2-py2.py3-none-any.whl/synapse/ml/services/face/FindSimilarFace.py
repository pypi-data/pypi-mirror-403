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
class FindSimilarFace(ComplexParamsMixin, JavaMLReadable, JavaMLWritable, JavaTransformer):
    """
    Args:
        AADToken (object): AAD Token used for authentication
        CustomAuthHeader (object): A Custom Value for Authorization Header
        concurrency (int): max number of concurrent calls
        concurrentTimeout (float): max number seconds to wait on futures if concurrency >= 1
        customHeaders (object): Map of Custom Header Key-Value Tuples.
        customUrlRoot (str): The custom URL root for the service. This will not append OpenAI specific model path completions (i.e. /chat/completions) to the URL.
        errorCol (str): column to hold http errors
        faceId (object): faceId of the query face. User needs to call FaceDetect first to get a valid faceId. Note that this faceId is not persisted and will expire 24 hours after the detection call.
        faceIds (object):  An array of candidate faceIds. All of them are created by FaceDetect and the faceIds will expire 24 hours after the detection call. The number of faceIds is limited to 1000. Parameter faceListId, largeFaceListId and faceIds should not be provided at the same time.
        faceListId (object):  An existing user-specified unique candidate face list, created in FaceList - Create. Face list contains a set of persistedFaceIds which are persisted and will never expire. Parameter faceListId, largeFaceListId and faceIds should not be provided at the same time.
        handler (object): Which strategy to use when handling requests
        largeFaceListId (object):  An existing user-specified unique candidate large face list, created in LargeFaceList - Create. Large face list contains a set of persistedFaceIds which are persisted and will never expire. Parameter faceListId, largeFaceListId and faceIds should not be provided at the same time.
        maxNumOfCandidatesReturned (object):  Optional parameter. The number of top similar faces returned. The valid range is [1, 1000].It defaults to 20.
        mode (object):  Optional parameter. Similar face searching mode. It can be 'matchPerson' or 'matchFace'. It defaults to 'matchPerson'.
        outputCol (str): The name of the output column
        subscriptionKey (object): the API key to use
        telemHeaders (object): Map of Custom Header Key-Value Tuples.
        timeout (float): number of seconds to wait before closing the connection
        url (str): Url of the service
    """

    AADToken = Param(Params._dummy(), "AADToken", "ServiceParam: AAD Token used for authentication")
    
    CustomAuthHeader = Param(Params._dummy(), "CustomAuthHeader", "ServiceParam: A Custom Value for Authorization Header")
    
    concurrency = Param(Params._dummy(), "concurrency", "max number of concurrent calls", typeConverter=TypeConverters.toInt)
    
    concurrentTimeout = Param(Params._dummy(), "concurrentTimeout", "max number seconds to wait on futures if concurrency >= 1", typeConverter=TypeConverters.toFloat)
    
    customHeaders = Param(Params._dummy(), "customHeaders", "ServiceParam: Map of Custom Header Key-Value Tuples.")
    
    customUrlRoot = Param(Params._dummy(), "customUrlRoot", "The custom URL root for the service. This will not append OpenAI specific model path completions (i.e. /chat/completions) to the URL.", typeConverter=TypeConverters.toString)
    
    errorCol = Param(Params._dummy(), "errorCol", "column to hold http errors", typeConverter=TypeConverters.toString)
    
    faceId = Param(Params._dummy(), "faceId", "ServiceParam: faceId of the query face. User needs to call FaceDetect first to get a valid faceId. Note that this faceId is not persisted and will expire 24 hours after the detection call.")
    
    faceIds = Param(Params._dummy(), "faceIds", "ServiceParam:  An array of candidate faceIds. All of them are created by FaceDetect and the faceIds will expire 24 hours after the detection call. The number of faceIds is limited to 1000. Parameter faceListId, largeFaceListId and faceIds should not be provided at the same time.")
    
    faceListId = Param(Params._dummy(), "faceListId", "ServiceParam:  An existing user-specified unique candidate face list, created in FaceList - Create. Face list contains a set of persistedFaceIds which are persisted and will never expire. Parameter faceListId, largeFaceListId and faceIds should not be provided at the same time.")
    
    handler = Param(Params._dummy(), "handler", "Which strategy to use when handling requests")
    
    largeFaceListId = Param(Params._dummy(), "largeFaceListId", "ServiceParam:  An existing user-specified unique candidate large face list, created in LargeFaceList - Create. Large face list contains a set of persistedFaceIds which are persisted and will never expire. Parameter faceListId, largeFaceListId and faceIds should not be provided at the same time.")
    
    maxNumOfCandidatesReturned = Param(Params._dummy(), "maxNumOfCandidatesReturned", "ServiceParam:  Optional parameter. The number of top similar faces returned. The valid range is [1, 1000].It defaults to 20.")
    
    mode = Param(Params._dummy(), "mode", "ServiceParam:  Optional parameter. Similar face searching mode. It can be 'matchPerson' or 'matchFace'. It defaults to 'matchPerson'.")
    
    outputCol = Param(Params._dummy(), "outputCol", "The name of the output column", typeConverter=TypeConverters.toString)
    
    subscriptionKey = Param(Params._dummy(), "subscriptionKey", "ServiceParam: the API key to use")
    
    telemHeaders = Param(Params._dummy(), "telemHeaders", "ServiceParam: Map of Custom Header Key-Value Tuples.")
    
    timeout = Param(Params._dummy(), "timeout", "number of seconds to wait before closing the connection", typeConverter=TypeConverters.toFloat)
    
    url = Param(Params._dummy(), "url", "Url of the service", typeConverter=TypeConverters.toString)

    
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
        customUrlRoot=None,
        errorCol="FindSimilarFace_8cc701f065b4_error",
        faceId=None,
        faceIdCol=None,
        faceIds=None,
        faceIdsCol=None,
        faceListId=None,
        faceListIdCol=None,
        handler=None,
        largeFaceListId=None,
        largeFaceListIdCol=None,
        maxNumOfCandidatesReturned=None,
        maxNumOfCandidatesReturnedCol=None,
        mode=None,
        modeCol=None,
        outputCol="FindSimilarFace_8cc701f065b4_output",
        subscriptionKey=None,
        subscriptionKeyCol=None,
        telemHeaders=None,
        telemHeadersCol=None,
        timeout=60.0,
        url=None
        ):
        super(FindSimilarFace, self).__init__()
        if java_obj is None:
            self._java_obj = self._new_java_obj("com.microsoft.azure.synapse.ml.services.face.FindSimilarFace", self.uid)
        else:
            self._java_obj = java_obj
        self._setDefault(concurrency=1)
        self._setDefault(errorCol="FindSimilarFace_8cc701f065b4_error")
        self._setDefault(outputCol="FindSimilarFace_8cc701f065b4_output")
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
        AADToken=None,
        AADTokenCol=None,
        CustomAuthHeader=None,
        CustomAuthHeaderCol=None,
        concurrency=1,
        concurrentTimeout=None,
        customHeaders=None,
        customHeadersCol=None,
        customUrlRoot=None,
        errorCol="FindSimilarFace_8cc701f065b4_error",
        faceId=None,
        faceIdCol=None,
        faceIds=None,
        faceIdsCol=None,
        faceListId=None,
        faceListIdCol=None,
        handler=None,
        largeFaceListId=None,
        largeFaceListIdCol=None,
        maxNumOfCandidatesReturned=None,
        maxNumOfCandidatesReturnedCol=None,
        mode=None,
        modeCol=None,
        outputCol="FindSimilarFace_8cc701f065b4_output",
        subscriptionKey=None,
        subscriptionKeyCol=None,
        telemHeaders=None,
        telemHeadersCol=None,
        timeout=60.0,
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
        return "com.microsoft.azure.synapse.ml.services.face.FindSimilarFace"

    @staticmethod
    def _from_java(java_stage):
        module_name=FindSimilarFace.__module__
        module_name=module_name.rsplit(".", 1)[0] + ".FindSimilarFace"
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
    
    def setFaceId(self, value):
        """
        Args:
            faceId: faceId of the query face. User needs to call FaceDetect first to get a valid faceId. Note that this faceId is not persisted and will expire 24 hours after the detection call.
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
        self._java_obj = self._java_obj.setFaceId(value)
        return self
    
    def setFaceIdCol(self, value):
        """
        Args:
            faceId: faceId of the query face. User needs to call FaceDetect first to get a valid faceId. Note that this faceId is not persisted and will expire 24 hours after the detection call.
        """
        self._java_obj = self._java_obj.setFaceIdCol(value)
        return self
    
    def setFaceIds(self, value):
        """
        Args:
            faceIds:  An array of candidate faceIds. All of them are created by FaceDetect and the faceIds will expire 24 hours after the detection call. The number of faceIds is limited to 1000. Parameter faceListId, largeFaceListId and faceIds should not be provided at the same time.
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
        self._java_obj = self._java_obj.setFaceIds(value)
        return self
    
    def setFaceIdsCol(self, value):
        """
        Args:
            faceIds:  An array of candidate faceIds. All of them are created by FaceDetect and the faceIds will expire 24 hours after the detection call. The number of faceIds is limited to 1000. Parameter faceListId, largeFaceListId and faceIds should not be provided at the same time.
        """
        self._java_obj = self._java_obj.setFaceIdsCol(value)
        return self
    
    def setFaceListId(self, value):
        """
        Args:
            faceListId:  An existing user-specified unique candidate face list, created in FaceList - Create. Face list contains a set of persistedFaceIds which are persisted and will never expire. Parameter faceListId, largeFaceListId and faceIds should not be provided at the same time.
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
        self._java_obj = self._java_obj.setFaceListId(value)
        return self
    
    def setFaceListIdCol(self, value):
        """
        Args:
            faceListId:  An existing user-specified unique candidate face list, created in FaceList - Create. Face list contains a set of persistedFaceIds which are persisted and will never expire. Parameter faceListId, largeFaceListId and faceIds should not be provided at the same time.
        """
        self._java_obj = self._java_obj.setFaceListIdCol(value)
        return self
    
    def setHandler(self, value):
        """
        Args:
            handler: Which strategy to use when handling requests
        """
        self._set(handler=value)
        return self
    
    def setLargeFaceListId(self, value):
        """
        Args:
            largeFaceListId:  An existing user-specified unique candidate large face list, created in LargeFaceList - Create. Large face list contains a set of persistedFaceIds which are persisted and will never expire. Parameter faceListId, largeFaceListId and faceIds should not be provided at the same time.
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
        self._java_obj = self._java_obj.setLargeFaceListId(value)
        return self
    
    def setLargeFaceListIdCol(self, value):
        """
        Args:
            largeFaceListId:  An existing user-specified unique candidate large face list, created in LargeFaceList - Create. Large face list contains a set of persistedFaceIds which are persisted and will never expire. Parameter faceListId, largeFaceListId and faceIds should not be provided at the same time.
        """
        self._java_obj = self._java_obj.setLargeFaceListIdCol(value)
        return self
    
    def setMaxNumOfCandidatesReturned(self, value):
        """
        Args:
            maxNumOfCandidatesReturned:  Optional parameter. The number of top similar faces returned. The valid range is [1, 1000].It defaults to 20.
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
        self._java_obj = self._java_obj.setMaxNumOfCandidatesReturned(value)
        return self
    
    def setMaxNumOfCandidatesReturnedCol(self, value):
        """
        Args:
            maxNumOfCandidatesReturned:  Optional parameter. The number of top similar faces returned. The valid range is [1, 1000].It defaults to 20.
        """
        self._java_obj = self._java_obj.setMaxNumOfCandidatesReturnedCol(value)
        return self
    
    def setMode(self, value):
        """
        Args:
            mode:  Optional parameter. Similar face searching mode. It can be 'matchPerson' or 'matchFace'. It defaults to 'matchPerson'.
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
        self._java_obj = self._java_obj.setMode(value)
        return self
    
    def setModeCol(self, value):
        """
        Args:
            mode:  Optional parameter. Similar face searching mode. It can be 'matchPerson' or 'matchFace'. It defaults to 'matchPerson'.
        """
        self._java_obj = self._java_obj.setModeCol(value)
        return self
    
    def setOutputCol(self, value):
        """
        Args:
            outputCol: The name of the output column
        """
        self._set(outputCol=value)
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
    
    
    def getFaceId(self):
        """
        Returns:
            faceId: faceId of the query face. User needs to call FaceDetect first to get a valid faceId. Note that this faceId is not persisted and will expire 24 hours after the detection call.
        """
        return self._java_obj.getFaceId()
    
    
    def getFaceIds(self):
        """
        Returns:
            faceIds:  An array of candidate faceIds. All of them are created by FaceDetect and the faceIds will expire 24 hours after the detection call. The number of faceIds is limited to 1000. Parameter faceListId, largeFaceListId and faceIds should not be provided at the same time.
        """
        return self._java_obj.getFaceIds()
    
    
    def getFaceListId(self):
        """
        Returns:
            faceListId:  An existing user-specified unique candidate face list, created in FaceList - Create. Face list contains a set of persistedFaceIds which are persisted and will never expire. Parameter faceListId, largeFaceListId and faceIds should not be provided at the same time.
        """
        return self._java_obj.getFaceListId()
    
    
    def getHandler(self):
        """
        Returns:
            handler: Which strategy to use when handling requests
        """
        return self.getOrDefault(self.handler)
    
    
    def getLargeFaceListId(self):
        """
        Returns:
            largeFaceListId:  An existing user-specified unique candidate large face list, created in LargeFaceList - Create. Large face list contains a set of persistedFaceIds which are persisted and will never expire. Parameter faceListId, largeFaceListId and faceIds should not be provided at the same time.
        """
        return self._java_obj.getLargeFaceListId()
    
    
    def getMaxNumOfCandidatesReturned(self):
        """
        Returns:
            maxNumOfCandidatesReturned:  Optional parameter. The number of top similar faces returned. The valid range is [1, 1000].It defaults to 20.
        """
        return self._java_obj.getMaxNumOfCandidatesReturned()
    
    
    def getMode(self):
        """
        Returns:
            mode:  Optional parameter. Similar face searching mode. It can be 'matchPerson' or 'matchFace'. It defaults to 'matchPerson'.
        """
        return self._java_obj.getMode()
    
    
    def getOutputCol(self):
        """
        Returns:
            outputCol: The name of the output column
        """
        return self.getOrDefault(self.outputCol)
    
    
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
    
    def setLocation(self, value):
        self._java_obj = self._java_obj.setLocation(value)
        return self
    
    def setLinkedService(self, value):
        self._java_obj = self._java_obj.setLinkedService(value)
        return self
        