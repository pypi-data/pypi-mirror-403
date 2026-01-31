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
class SpeechToTextSDK(ComplexParamsMixin, JavaMLReadable, JavaMLWritable, JavaTransformer):
    """
    Args:
        audioDataCol (str): Column holding audio data, must be either ByteArrays or Strings representing file URIs
        endpointId (str): endpoint for custom speech models
        extraFfmpegArgs (list): extra arguments to for ffmpeg output decoding
        fileType (object): The file type of the sound files, supported types: wav, ogg, mp3
        format (object):  Specifies the result format. Accepted values are simple and detailed. Default is simple.     
        language (object):  Identifies the spoken language that is being recognized.     
        outputCol (str): The name of the output column
        participantsJson (object): a json representation of a list of conversation participants (email, language, user)
        profanity (object):  Specifies how to handle profanity in recognition results. Accepted values are masked, which replaces profanity with asterisks, removed, which remove all profanity from the result, or raw, which includes the profanity in the result. The default setting is masked.     
        recordAudioData (bool): Whether to record audio data to a file location, for use only with m3u8 streams
        recordedFileNameCol (str): Column holding file names to write audio data to if ``recordAudioData'' is set to true
        streamIntermediateResults (bool): Whether or not to immediately return itermediate results, or group in a sequence
        subscriptionKey (object): the API key to use
        url (str): Url of the service
        wordLevelTimestamps (object): Whether to request timestamps foe each indivdual word
    """

    audioDataCol = Param(Params._dummy(), "audioDataCol", "Column holding audio data, must be either ByteArrays or Strings representing file URIs", typeConverter=TypeConverters.toString)
    
    endpointId = Param(Params._dummy(), "endpointId", "endpoint for custom speech models", typeConverter=TypeConverters.toString)
    
    extraFfmpegArgs = Param(Params._dummy(), "extraFfmpegArgs", "extra arguments to for ffmpeg output decoding", typeConverter=TypeConverters.toListString)
    
    fileType = Param(Params._dummy(), "fileType", "ServiceParam: The file type of the sound files, supported types: wav, ogg, mp3")
    
    format = Param(Params._dummy(), "format", "ServiceParam:  Specifies the result format. Accepted values are simple and detailed. Default is simple.     ")
    
    language = Param(Params._dummy(), "language", "ServiceParam:  Identifies the spoken language that is being recognized.     ")
    
    outputCol = Param(Params._dummy(), "outputCol", "The name of the output column", typeConverter=TypeConverters.toString)
    
    participantsJson = Param(Params._dummy(), "participantsJson", "ServiceParam: a json representation of a list of conversation participants (email, language, user)")
    
    profanity = Param(Params._dummy(), "profanity", "ServiceParam:  Specifies how to handle profanity in recognition results. Accepted values are masked, which replaces profanity with asterisks, removed, which remove all profanity from the result, or raw, which includes the profanity in the result. The default setting is masked.     ")
    
    recordAudioData = Param(Params._dummy(), "recordAudioData", "Whether to record audio data to a file location, for use only with m3u8 streams", typeConverter=TypeConverters.toBoolean)
    
    recordedFileNameCol = Param(Params._dummy(), "recordedFileNameCol", "Column holding file names to write audio data to if ``recordAudioData'' is set to true", typeConverter=TypeConverters.toString)
    
    streamIntermediateResults = Param(Params._dummy(), "streamIntermediateResults", "Whether or not to immediately return itermediate results, or group in a sequence", typeConverter=TypeConverters.toBoolean)
    
    subscriptionKey = Param(Params._dummy(), "subscriptionKey", "ServiceParam: the API key to use")
    
    url = Param(Params._dummy(), "url", "Url of the service", typeConverter=TypeConverters.toString)
    
    wordLevelTimestamps = Param(Params._dummy(), "wordLevelTimestamps", "ServiceParam: Whether to request timestamps foe each indivdual word")

    
    @keyword_only
    def __init__(
        self,
        java_obj=None,
        audioDataCol=None,
        endpointId=None,
        extraFfmpegArgs=[],
        fileType=None,
        fileTypeCol=None,
        format=None,
        formatCol=None,
        language=None,
        languageCol=None,
        outputCol=None,
        participantsJson=None,
        participantsJsonCol=None,
        profanity=None,
        profanityCol=None,
        recordAudioData=False,
        recordedFileNameCol=None,
        streamIntermediateResults=True,
        subscriptionKey=None,
        subscriptionKeyCol=None,
        url=None,
        wordLevelTimestamps=None,
        wordLevelTimestampsCol=None
        ):
        super(SpeechToTextSDK, self).__init__()
        if java_obj is None:
            self._java_obj = self._new_java_obj("com.microsoft.azure.synapse.ml.services.speech.SpeechToTextSDK", self.uid)
        else:
            self._java_obj = java_obj
        self._setDefault(extraFfmpegArgs=[])
        self._setDefault(recordAudioData=False)
        self._setDefault(streamIntermediateResults=True)
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
        audioDataCol=None,
        endpointId=None,
        extraFfmpegArgs=[],
        fileType=None,
        fileTypeCol=None,
        format=None,
        formatCol=None,
        language=None,
        languageCol=None,
        outputCol=None,
        participantsJson=None,
        participantsJsonCol=None,
        profanity=None,
        profanityCol=None,
        recordAudioData=False,
        recordedFileNameCol=None,
        streamIntermediateResults=True,
        subscriptionKey=None,
        subscriptionKeyCol=None,
        url=None,
        wordLevelTimestamps=None,
        wordLevelTimestampsCol=None
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
        return "com.microsoft.azure.synapse.ml.services.speech.SpeechToTextSDK"

    @staticmethod
    def _from_java(java_stage):
        module_name=SpeechToTextSDK.__module__
        module_name=module_name.rsplit(".", 1)[0] + ".SpeechToTextSDK"
        return from_java(java_stage, module_name)

    def setAudioDataCol(self, value):
        """
        Args:
            audioDataCol: Column holding audio data, must be either ByteArrays or Strings representing file URIs
        """
        self._set(audioDataCol=value)
        return self
    
    def setEndpointId(self, value):
        """
        Args:
            endpointId: endpoint for custom speech models
        """
        self._set(endpointId=value)
        return self
    
    def setExtraFfmpegArgs(self, value):
        """
        Args:
            extraFfmpegArgs: extra arguments to for ffmpeg output decoding
        """
        self._set(extraFfmpegArgs=value)
        return self
    
    def setFileType(self, value):
        """
        Args:
            fileType: The file type of the sound files, supported types: wav, ogg, mp3
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
        self._java_obj = self._java_obj.setFileType(value)
        return self
    
    def setFileTypeCol(self, value):
        """
        Args:
            fileType: The file type of the sound files, supported types: wav, ogg, mp3
        """
        self._java_obj = self._java_obj.setFileTypeCol(value)
        return self
    
    def setFormat(self, value):
        """
        Args:
            format:  Specifies the result format. Accepted values are simple and detailed. Default is simple.     
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
        self._java_obj = self._java_obj.setFormat(value)
        return self
    
    def setFormatCol(self, value):
        """
        Args:
            format:  Specifies the result format. Accepted values are simple and detailed. Default is simple.     
        """
        self._java_obj = self._java_obj.setFormatCol(value)
        return self
    
    def setLanguage(self, value):
        """
        Args:
            language:  Identifies the spoken language that is being recognized.     
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
        self._java_obj = self._java_obj.setLanguage(value)
        return self
    
    def setLanguageCol(self, value):
        """
        Args:
            language:  Identifies the spoken language that is being recognized.     
        """
        self._java_obj = self._java_obj.setLanguageCol(value)
        return self
    
    def setOutputCol(self, value):
        """
        Args:
            outputCol: The name of the output column
        """
        self._set(outputCol=value)
        return self
    
    def setParticipantsJson(self, value):
        """
        Args:
            participantsJson: a json representation of a list of conversation participants (email, language, user)
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
        self._java_obj = self._java_obj.setParticipantsJson(value)
        return self
    
    def setParticipantsJsonCol(self, value):
        """
        Args:
            participantsJson: a json representation of a list of conversation participants (email, language, user)
        """
        self._java_obj = self._java_obj.setParticipantsJsonCol(value)
        return self
    
    def setProfanity(self, value):
        """
        Args:
            profanity:  Specifies how to handle profanity in recognition results. Accepted values are masked, which replaces profanity with asterisks, removed, which remove all profanity from the result, or raw, which includes the profanity in the result. The default setting is masked.     
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
        self._java_obj = self._java_obj.setProfanity(value)
        return self
    
    def setProfanityCol(self, value):
        """
        Args:
            profanity:  Specifies how to handle profanity in recognition results. Accepted values are masked, which replaces profanity with asterisks, removed, which remove all profanity from the result, or raw, which includes the profanity in the result. The default setting is masked.     
        """
        self._java_obj = self._java_obj.setProfanityCol(value)
        return self
    
    def setRecordAudioData(self, value):
        """
        Args:
            recordAudioData: Whether to record audio data to a file location, for use only with m3u8 streams
        """
        self._set(recordAudioData=value)
        return self
    
    def setRecordedFileNameCol(self, value):
        """
        Args:
            recordedFileNameCol: Column holding file names to write audio data to if ``recordAudioData'' is set to true
        """
        self._set(recordedFileNameCol=value)
        return self
    
    def setStreamIntermediateResults(self, value):
        """
        Args:
            streamIntermediateResults: Whether or not to immediately return itermediate results, or group in a sequence
        """
        self._set(streamIntermediateResults=value)
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
    
    def setUrl(self, value):
        """
        Args:
            url: Url of the service
        """
        self._set(url=value)
        return self
    
    def setWordLevelTimestamps(self, value):
        """
        Args:
            wordLevelTimestamps: Whether to request timestamps foe each indivdual word
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
        self._java_obj = self._java_obj.setWordLevelTimestamps(value)
        return self
    
    def setWordLevelTimestampsCol(self, value):
        """
        Args:
            wordLevelTimestamps: Whether to request timestamps foe each indivdual word
        """
        self._java_obj = self._java_obj.setWordLevelTimestampsCol(value)
        return self

    
    def getAudioDataCol(self):
        """
        Returns:
            audioDataCol: Column holding audio data, must be either ByteArrays or Strings representing file URIs
        """
        return self.getOrDefault(self.audioDataCol)
    
    
    def getEndpointId(self):
        """
        Returns:
            endpointId: endpoint for custom speech models
        """
        return self.getOrDefault(self.endpointId)
    
    
    def getExtraFfmpegArgs(self):
        """
        Returns:
            extraFfmpegArgs: extra arguments to for ffmpeg output decoding
        """
        return self.getOrDefault(self.extraFfmpegArgs)
    
    
    def getFileType(self):
        """
        Returns:
            fileType: The file type of the sound files, supported types: wav, ogg, mp3
        """
        return self._java_obj.getFileType()
    
    
    def getFormat(self):
        """
        Returns:
            format:  Specifies the result format. Accepted values are simple and detailed. Default is simple.     
        """
        return self._java_obj.getFormat()
    
    
    def getLanguage(self):
        """
        Returns:
            language:  Identifies the spoken language that is being recognized.     
        """
        return self._java_obj.getLanguage()
    
    
    def getOutputCol(self):
        """
        Returns:
            outputCol: The name of the output column
        """
        return self.getOrDefault(self.outputCol)
    
    
    def getParticipantsJson(self):
        """
        Returns:
            participantsJson: a json representation of a list of conversation participants (email, language, user)
        """
        return self._java_obj.getParticipantsJson()
    
    
    def getProfanity(self):
        """
        Returns:
            profanity:  Specifies how to handle profanity in recognition results. Accepted values are masked, which replaces profanity with asterisks, removed, which remove all profanity from the result, or raw, which includes the profanity in the result. The default setting is masked.     
        """
        return self._java_obj.getProfanity()
    
    
    def getRecordAudioData(self):
        """
        Returns:
            recordAudioData: Whether to record audio data to a file location, for use only with m3u8 streams
        """
        return self.getOrDefault(self.recordAudioData)
    
    
    def getRecordedFileNameCol(self):
        """
        Returns:
            recordedFileNameCol: Column holding file names to write audio data to if ``recordAudioData'' is set to true
        """
        return self.getOrDefault(self.recordedFileNameCol)
    
    
    def getStreamIntermediateResults(self):
        """
        Returns:
            streamIntermediateResults: Whether or not to immediately return itermediate results, or group in a sequence
        """
        return self.getOrDefault(self.streamIntermediateResults)
    
    
    def getSubscriptionKey(self):
        """
        Returns:
            subscriptionKey: the API key to use
        """
        return self._java_obj.getSubscriptionKey()
    
    
    def getUrl(self):
        """
        Returns:
            url: Url of the service
        """
        return self.getOrDefault(self.url)
    
    
    def getWordLevelTimestamps(self):
        """
        Returns:
            wordLevelTimestamps: Whether to request timestamps foe each indivdual word
        """
        return self._java_obj.getWordLevelTimestamps()

    

    
    def setLocation(self, value):
        self._java_obj = self._java_obj.setLocation(value)
        return self
    
    def setLinkedService(self, value):
        self._java_obj = self._java_obj.setLinkedService(value)
        return self
        