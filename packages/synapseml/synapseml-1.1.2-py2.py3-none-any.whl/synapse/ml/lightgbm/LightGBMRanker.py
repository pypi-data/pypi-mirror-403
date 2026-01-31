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
from synapse.ml.lightgbm.LightGBMRankerModel import LightGBMRankerModel

@inherit_doc
class LightGBMRanker(ComplexParamsMixin, JavaMLReadable, JavaMLWritable, JavaEstimator):
    """
    Args:
        baggingFraction (float): Bagging fraction
        baggingFreq (int): Bagging frequency
        baggingSeed (int): Bagging seed
        binSampleCount (int): Number of samples considered at computing histogram bins
        boostFromAverage (bool): Adjusts initial score to the mean of labels for faster convergence
        boostingType (str): Default gbdt = traditional Gradient Boosting Decision Tree. Options are: gbdt, gbrt, rf (Random Forest), random_forest, dart (Dropouts meet Multiple Additive Regression Trees), goss (Gradient-based One-Side Sampling). 
        catSmooth (float): this can reduce the effect of noises in categorical features, especially for categories with few data
        categoricalSlotIndexes (list): List of categorical column indexes, the slot index in the features column
        categoricalSlotNames (list): List of categorical column slot names, the slot name in the features column
        catl2 (float): L2 regularization in categorical split
        chunkSize (int): Advanced parameter to specify the chunk size for copying Java data to native.  If set too high, memory may be wasted, but if set too low, performance may be reduced during data copy.If dataset size is known beforehand, set to the number of rows in the dataset.
        dataRandomSeed (int): Random seed for sampling data to construct histogram bins.
        dataTransferMode (str): Specify how SynapseML transfers data from Spark to LightGBM.  Values can be streaming, bulk. Default is streaming.
        defaultListenPort (int): The default listen port on executors, used for testing
        deterministic (bool): Used only with cpu devide type. Setting this to true should ensure stable results when using the same data and the same parameters.  Note: setting this to true may slow down training.  To avoid potential instability due to numerical issues, please set force_col_wise=true or force_row_wise=true when setting deterministic=true
        driverListenPort (int): The listen port on a driver. Default value is 0 (random)
        dropRate (float): Dropout rate: a fraction of previous trees to drop during the dropout
        dropSeed (int): Random seed to choose dropping models. Only used in dart.
        earlyStoppingRound (int): Early stopping round
        evalAt (list): NDCG and MAP evaluation positions, separated by comma
        executionMode (str): Deprecated. Please use dataTransferMode.
        extraSeed (int): Random seed for selecting threshold when extra_trees is true
        featureFraction (float): Feature fraction
        featureFractionByNode (float): Feature fraction by node
        featureFractionSeed (int): Feature fraction seed
        featuresCol (str): features column name
        featuresShapCol (str): Output SHAP vector column name after prediction containing the feature contribution values
        fobj (object): Customized objective function. Should accept two parameters: preds, train_data, and return (grad, hess).
        groupCol (str): The name of the group column
        improvementTolerance (float): Tolerance to consider improvement in metric
        initScoreCol (str): The name of the initial score column, used for continued training
        isEnableSparse (bool): Used to enable/disable sparse optimization
        isProvideTrainingMetric (bool): Whether output metric result over training dataset.
        labelCol (str): label column name
        labelGain (list): graded relevance for each label in NDCG
        lambdaL1 (float): L1 regularization
        lambdaL2 (float): L2 regularization
        leafPredictionCol (str): Predicted leaf indices's column name
        learningRate (float): Learning rate or shrinkage rate
        matrixType (str): Advanced parameter to specify whether the native lightgbm matrix constructed should be sparse or dense.  Values can be auto, sparse or dense. Default value is auto, which samples first ten rows to determine type.
        maxBin (int): Max bin
        maxBinByFeature (list): Max number of bins for each feature
        maxCatThreshold (int): limit number of split points considered for categorical features
        maxCatToOnehot (int): when number of categories of one feature smaller than or equal to this, one-vs-other split algorithm will be used
        maxDeltaStep (float): Used to limit the max output of tree leaves
        maxDepth (int): Max depth
        maxDrop (int): Max number of dropped trees during one boosting iteration
        maxNumClasses (int): Number of max classes to infer numClass in multi-class classification.
        maxPosition (int): optimized NDCG at this position
        maxStreamingOMPThreads (int): Maximum number of OpenMP threads used by a LightGBM thread. Used only for thread-safe buffer allocation. Use -1 to use OpenMP default, but in a Spark environment it's best to set a fixed value.
        metric (str): Metrics to be evaluated on the evaluation data.  Options are: empty string or not specified means that metric corresponding to specified objective will be used (this is possible only for pre-defined objective functions, otherwise no evaluation metric will be added). None (string, not a None value) means that no metric will be registered, aliases: na, null, custom. l1, absolute loss, aliases: mean_absolute_error, mae, regression_l1. l2, square loss, aliases: mean_squared_error, mse, regression_l2, regression. rmse, root square loss, aliases: root_mean_squared_error, l2_root. quantile, Quantile regression. mape, MAPE loss, aliases: mean_absolute_percentage_error. huber, Huber loss. fair, Fair loss. poisson, negative log-likelihood for Poisson regression. gamma, negative log-likelihood for Gamma regression. gamma_deviance, residual deviance for Gamma regression. tweedie, negative log-likelihood for Tweedie regression. ndcg, NDCG, aliases: lambdarank. map, MAP, aliases: mean_average_precision. auc, AUC. binary_logloss, log loss, aliases: binary. binary_error, for one sample: 0 for correct classification, 1 for error classification. multi_logloss, log loss for multi-class classification, aliases: multiclass, softmax, multiclassova, multiclass_ova, ova, ovr. multi_error, error rate for multi-class classification. cross_entropy, cross-entropy (with optional linear weights), aliases: xentropy. cross_entropy_lambda, intensity-weighted cross-entropy, aliases: xentlambda. kullback_leibler, Kullback-Leibler divergence, aliases: kldiv. 
        microBatchSize (int): Specify how many elements are sent in a streaming micro-batch.
        minDataInLeaf (int): Minimal number of data in one leaf. Can be used to deal with over-fitting.
        minDataPerBin (int): Minimal number of data inside one bin
        minDataPerGroup (int): minimal number of data per categorical group
        minGainToSplit (float): The minimal gain to perform split
        minSumHessianInLeaf (float): Minimal sum hessian in one leaf
        modelString (str): LightGBM model to retrain
        monotoneConstraints (list): used for constraints of monotonic features. 1 means increasing, -1 means decreasing, 0 means non-constraint. Specify all features in order.
        monotoneConstraintsMethod (str): Monotone constraints method. basic, intermediate, or advanced.
        monotonePenalty (float): A penalization parameter X forbids any monotone splits on the first X (rounded down) level(s) of the tree.
        negBaggingFraction (float): Negative Bagging fraction
        numBatches (int): If greater than 0, splits data into separate batches during training
        numIterations (int): Number of iterations, LightGBM constructs num_class * num_iterations trees
        numLeaves (int): Number of leaves
        numTasks (int): Advanced parameter to specify the number of tasks.  SynapseML tries to guess this based on cluster configuration, but this parameter can be used to override.
        numThreads (int): Number of threads per executor for LightGBM. For the best speed, set this to the number of real CPU cores.
        objective (str): The Objective. For regression applications, this can be: regression_l2, regression_l1, huber, fair, poisson, quantile, mape, gamma or tweedie. For classification applications, this can be: binary, multiclass, or multiclassova. 
        objectiveSeed (int): Random seed for objectives, if random process is needed.  Currently used only for rank_xendcg objective.
        otherRate (float): The retain ratio of small gradient data. Only used in goss.
        parallelism (str): Tree learner parallelism, can be set to data_parallel or voting_parallel
        passThroughArgs (str): Direct string to pass through to LightGBM library (appended with other explicitly set params). Will override any parameters given with explicit setters. Can include multiple parameters in one string. e.g., force_row_wise=true
        posBaggingFraction (float): Positive Bagging fraction
        predictDisableShapeCheck (bool): control whether or not LightGBM raises an error when you try to predict on data with a different number of features than the training data
        predictionCol (str): prediction column name
        referenceDataset (list): The reference Dataset that was used for the fit. If using samplingMode=custom, this must be set before fit().
        repartitionByGroupingColumn (bool): Repartition training data according to grouping column, on by default.
        samplingMode (str): Data sampling for streaming mode. Sampled data is used to define bins. 'global': sample from all data, 'subset': sample from first N rows, or 'fixed': Take first N rows as sample.Values can be global, subset, or fixed. Default is subset.
        samplingSubsetSize (int): Specify subset size N for the sampling mode 'subset'. 'binSampleCount' rows will be chosen from the first N values of the dataset. Subset can be used when rows are expected to be random and data is huge.
        seed (int): Main seed, used to generate other seeds
        skipDrop (float): Probability of skipping the dropout procedure during a boosting iteration
        slotNames (list): List of slot names in the features column
        timeout (float): Timeout in seconds
        topK (int): The top_k value used in Voting parallel, set this to larger value for more accurate result, but it will slow down the training speed. It should be greater than 0
        topRate (float): The retain ratio of large gradient data. Only used in goss.
        uniformDrop (bool): Set this to true to use uniform drop in dart mode
        useBarrierExecutionMode (bool): Barrier execution mode which uses a barrier stage, off by default.
        useMissing (bool): Set this to false to disable the special handle of missing value
        useSingleDatasetMode (bool): Use single dataset execution mode to create a single native dataset per executor (singleton) to reduce memory and communication overhead.
        validationIndicatorCol (str): Indicates whether the row is for training or validation
        verbosity (int): Verbosity where lt 0 is Fatal, eq 0 is Error, eq 1 is Info, gt 1 is Debug
        weightCol (str): The name of the weight column
        xGBoostDartMode (bool): Set this to true to use xgboost dart mode
        zeroAsMissing (bool): Set to true to treat all zero as missing values (including the unshown values in LibSVM / sparse matrices). Set to false to use na for representing missing values
    """

    baggingFraction = Param(Params._dummy(), "baggingFraction", "Bagging fraction", typeConverter=TypeConverters.toFloat)
    
    baggingFreq = Param(Params._dummy(), "baggingFreq", "Bagging frequency", typeConverter=TypeConverters.toInt)
    
    baggingSeed = Param(Params._dummy(), "baggingSeed", "Bagging seed", typeConverter=TypeConverters.toInt)
    
    binSampleCount = Param(Params._dummy(), "binSampleCount", "Number of samples considered at computing histogram bins", typeConverter=TypeConverters.toInt)
    
    boostFromAverage = Param(Params._dummy(), "boostFromAverage", "Adjusts initial score to the mean of labels for faster convergence", typeConverter=TypeConverters.toBoolean)
    
    boostingType = Param(Params._dummy(), "boostingType", "Default gbdt = traditional Gradient Boosting Decision Tree. Options are: gbdt, gbrt, rf (Random Forest), random_forest, dart (Dropouts meet Multiple Additive Regression Trees), goss (Gradient-based One-Side Sampling). ", typeConverter=TypeConverters.toString)
    
    catSmooth = Param(Params._dummy(), "catSmooth", "this can reduce the effect of noises in categorical features, especially for categories with few data", typeConverter=TypeConverters.toFloat)
    
    categoricalSlotIndexes = Param(Params._dummy(), "categoricalSlotIndexes", "List of categorical column indexes, the slot index in the features column", typeConverter=TypeConverters.toListInt)
    
    categoricalSlotNames = Param(Params._dummy(), "categoricalSlotNames", "List of categorical column slot names, the slot name in the features column", typeConverter=TypeConverters.toListString)
    
    catl2 = Param(Params._dummy(), "catl2", "L2 regularization in categorical split", typeConverter=TypeConverters.toFloat)
    
    chunkSize = Param(Params._dummy(), "chunkSize", "Advanced parameter to specify the chunk size for copying Java data to native.  If set too high, memory may be wasted, but if set too low, performance may be reduced during data copy.If dataset size is known beforehand, set to the number of rows in the dataset.", typeConverter=TypeConverters.toInt)
    
    dataRandomSeed = Param(Params._dummy(), "dataRandomSeed", "Random seed for sampling data to construct histogram bins.", typeConverter=TypeConverters.toInt)
    
    dataTransferMode = Param(Params._dummy(), "dataTransferMode", "Specify how SynapseML transfers data from Spark to LightGBM.  Values can be streaming, bulk. Default is streaming.", typeConverter=TypeConverters.toString)
    
    defaultListenPort = Param(Params._dummy(), "defaultListenPort", "The default listen port on executors, used for testing", typeConverter=TypeConverters.toInt)
    
    deterministic = Param(Params._dummy(), "deterministic", "Used only with cpu devide type. Setting this to true should ensure stable results when using the same data and the same parameters.  Note: setting this to true may slow down training.  To avoid potential instability due to numerical issues, please set force_col_wise=true or force_row_wise=true when setting deterministic=true", typeConverter=TypeConverters.toBoolean)
    
    driverListenPort = Param(Params._dummy(), "driverListenPort", "The listen port on a driver. Default value is 0 (random)", typeConverter=TypeConverters.toInt)
    
    dropRate = Param(Params._dummy(), "dropRate", "Dropout rate: a fraction of previous trees to drop during the dropout", typeConverter=TypeConverters.toFloat)
    
    dropSeed = Param(Params._dummy(), "dropSeed", "Random seed to choose dropping models. Only used in dart.", typeConverter=TypeConverters.toInt)
    
    earlyStoppingRound = Param(Params._dummy(), "earlyStoppingRound", "Early stopping round", typeConverter=TypeConverters.toInt)
    
    evalAt = Param(Params._dummy(), "evalAt", "NDCG and MAP evaluation positions, separated by comma", typeConverter=TypeConverters.toListInt)
    
    executionMode = Param(Params._dummy(), "executionMode", "Deprecated. Please use dataTransferMode.", typeConverter=TypeConverters.toString)
    
    extraSeed = Param(Params._dummy(), "extraSeed", "Random seed for selecting threshold when extra_trees is true", typeConverter=TypeConverters.toInt)
    
    featureFraction = Param(Params._dummy(), "featureFraction", "Feature fraction", typeConverter=TypeConverters.toFloat)
    
    featureFractionByNode = Param(Params._dummy(), "featureFractionByNode", "Feature fraction by node", typeConverter=TypeConverters.toFloat)
    
    featureFractionSeed = Param(Params._dummy(), "featureFractionSeed", "Feature fraction seed", typeConverter=TypeConverters.toInt)
    
    featuresCol = Param(Params._dummy(), "featuresCol", "features column name", typeConverter=TypeConverters.toString)
    
    featuresShapCol = Param(Params._dummy(), "featuresShapCol", "Output SHAP vector column name after prediction containing the feature contribution values", typeConverter=TypeConverters.toString)
    
    fobj = Param(Params._dummy(), "fobj", "Customized objective function. Should accept two parameters: preds, train_data, and return (grad, hess).")
    
    groupCol = Param(Params._dummy(), "groupCol", "The name of the group column", typeConverter=TypeConverters.toString)
    
    improvementTolerance = Param(Params._dummy(), "improvementTolerance", "Tolerance to consider improvement in metric", typeConverter=TypeConverters.toFloat)
    
    initScoreCol = Param(Params._dummy(), "initScoreCol", "The name of the initial score column, used for continued training", typeConverter=TypeConverters.toString)
    
    isEnableSparse = Param(Params._dummy(), "isEnableSparse", "Used to enable/disable sparse optimization", typeConverter=TypeConverters.toBoolean)
    
    isProvideTrainingMetric = Param(Params._dummy(), "isProvideTrainingMetric", "Whether output metric result over training dataset.", typeConverter=TypeConverters.toBoolean)
    
    labelCol = Param(Params._dummy(), "labelCol", "label column name", typeConverter=TypeConverters.toString)
    
    labelGain = Param(Params._dummy(), "labelGain", "graded relevance for each label in NDCG", typeConverter=TypeConverters.toListFloat)
    
    lambdaL1 = Param(Params._dummy(), "lambdaL1", "L1 regularization", typeConverter=TypeConverters.toFloat)
    
    lambdaL2 = Param(Params._dummy(), "lambdaL2", "L2 regularization", typeConverter=TypeConverters.toFloat)
    
    leafPredictionCol = Param(Params._dummy(), "leafPredictionCol", "Predicted leaf indices's column name", typeConverter=TypeConverters.toString)
    
    learningRate = Param(Params._dummy(), "learningRate", "Learning rate or shrinkage rate", typeConverter=TypeConverters.toFloat)
    
    matrixType = Param(Params._dummy(), "matrixType", "Advanced parameter to specify whether the native lightgbm matrix constructed should be sparse or dense.  Values can be auto, sparse or dense. Default value is auto, which samples first ten rows to determine type.", typeConverter=TypeConverters.toString)
    
    maxBin = Param(Params._dummy(), "maxBin", "Max bin", typeConverter=TypeConverters.toInt)
    
    maxBinByFeature = Param(Params._dummy(), "maxBinByFeature", "Max number of bins for each feature", typeConverter=TypeConverters.toListInt)
    
    maxCatThreshold = Param(Params._dummy(), "maxCatThreshold", "limit number of split points considered for categorical features", typeConverter=TypeConverters.toInt)
    
    maxCatToOnehot = Param(Params._dummy(), "maxCatToOnehot", "when number of categories of one feature smaller than or equal to this, one-vs-other split algorithm will be used", typeConverter=TypeConverters.toInt)
    
    maxDeltaStep = Param(Params._dummy(), "maxDeltaStep", "Used to limit the max output of tree leaves", typeConverter=TypeConverters.toFloat)
    
    maxDepth = Param(Params._dummy(), "maxDepth", "Max depth", typeConverter=TypeConverters.toInt)
    
    maxDrop = Param(Params._dummy(), "maxDrop", "Max number of dropped trees during one boosting iteration", typeConverter=TypeConverters.toInt)
    
    maxNumClasses = Param(Params._dummy(), "maxNumClasses", "Number of max classes to infer numClass in multi-class classification.", typeConverter=TypeConverters.toInt)
    
    maxPosition = Param(Params._dummy(), "maxPosition", "optimized NDCG at this position", typeConverter=TypeConverters.toInt)
    
    maxStreamingOMPThreads = Param(Params._dummy(), "maxStreamingOMPThreads", "Maximum number of OpenMP threads used by a LightGBM thread. Used only for thread-safe buffer allocation. Use -1 to use OpenMP default, but in a Spark environment it's best to set a fixed value.", typeConverter=TypeConverters.toInt)
    
    metric = Param(Params._dummy(), "metric", "Metrics to be evaluated on the evaluation data.  Options are: empty string or not specified means that metric corresponding to specified objective will be used (this is possible only for pre-defined objective functions, otherwise no evaluation metric will be added). None (string, not a None value) means that no metric will be registered, aliases: na, null, custom. l1, absolute loss, aliases: mean_absolute_error, mae, regression_l1. l2, square loss, aliases: mean_squared_error, mse, regression_l2, regression. rmse, root square loss, aliases: root_mean_squared_error, l2_root. quantile, Quantile regression. mape, MAPE loss, aliases: mean_absolute_percentage_error. huber, Huber loss. fair, Fair loss. poisson, negative log-likelihood for Poisson regression. gamma, negative log-likelihood for Gamma regression. gamma_deviance, residual deviance for Gamma regression. tweedie, negative log-likelihood for Tweedie regression. ndcg, NDCG, aliases: lambdarank. map, MAP, aliases: mean_average_precision. auc, AUC. binary_logloss, log loss, aliases: binary. binary_error, for one sample: 0 for correct classification, 1 for error classification. multi_logloss, log loss for multi-class classification, aliases: multiclass, softmax, multiclassova, multiclass_ova, ova, ovr. multi_error, error rate for multi-class classification. cross_entropy, cross-entropy (with optional linear weights), aliases: xentropy. cross_entropy_lambda, intensity-weighted cross-entropy, aliases: xentlambda. kullback_leibler, Kullback-Leibler divergence, aliases: kldiv. ", typeConverter=TypeConverters.toString)
    
    microBatchSize = Param(Params._dummy(), "microBatchSize", "Specify how many elements are sent in a streaming micro-batch.", typeConverter=TypeConverters.toInt)
    
    minDataInLeaf = Param(Params._dummy(), "minDataInLeaf", "Minimal number of data in one leaf. Can be used to deal with over-fitting.", typeConverter=TypeConverters.toInt)
    
    minDataPerBin = Param(Params._dummy(), "minDataPerBin", "Minimal number of data inside one bin", typeConverter=TypeConverters.toInt)
    
    minDataPerGroup = Param(Params._dummy(), "minDataPerGroup", "minimal number of data per categorical group", typeConverter=TypeConverters.toInt)
    
    minGainToSplit = Param(Params._dummy(), "minGainToSplit", "The minimal gain to perform split", typeConverter=TypeConverters.toFloat)
    
    minSumHessianInLeaf = Param(Params._dummy(), "minSumHessianInLeaf", "Minimal sum hessian in one leaf", typeConverter=TypeConverters.toFloat)
    
    modelString = Param(Params._dummy(), "modelString", "LightGBM model to retrain", typeConverter=TypeConverters.toString)
    
    monotoneConstraints = Param(Params._dummy(), "monotoneConstraints", "used for constraints of monotonic features. 1 means increasing, -1 means decreasing, 0 means non-constraint. Specify all features in order.", typeConverter=TypeConverters.toListInt)
    
    monotoneConstraintsMethod = Param(Params._dummy(), "monotoneConstraintsMethod", "Monotone constraints method. basic, intermediate, or advanced.", typeConverter=TypeConverters.toString)
    
    monotonePenalty = Param(Params._dummy(), "monotonePenalty", "A penalization parameter X forbids any monotone splits on the first X (rounded down) level(s) of the tree.", typeConverter=TypeConverters.toFloat)
    
    negBaggingFraction = Param(Params._dummy(), "negBaggingFraction", "Negative Bagging fraction", typeConverter=TypeConverters.toFloat)
    
    numBatches = Param(Params._dummy(), "numBatches", "If greater than 0, splits data into separate batches during training", typeConverter=TypeConverters.toInt)
    
    numIterations = Param(Params._dummy(), "numIterations", "Number of iterations, LightGBM constructs num_class * num_iterations trees", typeConverter=TypeConverters.toInt)
    
    numLeaves = Param(Params._dummy(), "numLeaves", "Number of leaves", typeConverter=TypeConverters.toInt)
    
    numTasks = Param(Params._dummy(), "numTasks", "Advanced parameter to specify the number of tasks.  SynapseML tries to guess this based on cluster configuration, but this parameter can be used to override.", typeConverter=TypeConverters.toInt)
    
    numThreads = Param(Params._dummy(), "numThreads", "Number of threads per executor for LightGBM. For the best speed, set this to the number of real CPU cores.", typeConverter=TypeConverters.toInt)
    
    objective = Param(Params._dummy(), "objective", "The Objective. For regression applications, this can be: regression_l2, regression_l1, huber, fair, poisson, quantile, mape, gamma or tweedie. For classification applications, this can be: binary, multiclass, or multiclassova. ", typeConverter=TypeConverters.toString)
    
    objectiveSeed = Param(Params._dummy(), "objectiveSeed", "Random seed for objectives, if random process is needed.  Currently used only for rank_xendcg objective.", typeConverter=TypeConverters.toInt)
    
    otherRate = Param(Params._dummy(), "otherRate", "The retain ratio of small gradient data. Only used in goss.", typeConverter=TypeConverters.toFloat)
    
    parallelism = Param(Params._dummy(), "parallelism", "Tree learner parallelism, can be set to data_parallel or voting_parallel", typeConverter=TypeConverters.toString)
    
    passThroughArgs = Param(Params._dummy(), "passThroughArgs", "Direct string to pass through to LightGBM library (appended with other explicitly set params). Will override any parameters given with explicit setters. Can include multiple parameters in one string. e.g., force_row_wise=true", typeConverter=TypeConverters.toString)
    
    posBaggingFraction = Param(Params._dummy(), "posBaggingFraction", "Positive Bagging fraction", typeConverter=TypeConverters.toFloat)
    
    predictDisableShapeCheck = Param(Params._dummy(), "predictDisableShapeCheck", "control whether or not LightGBM raises an error when you try to predict on data with a different number of features than the training data", typeConverter=TypeConverters.toBoolean)
    
    predictionCol = Param(Params._dummy(), "predictionCol", "prediction column name", typeConverter=TypeConverters.toString)
    
    referenceDataset = Param(Params._dummy(), "referenceDataset", "The reference Dataset that was used for the fit. If using samplingMode=custom, this must be set before fit().")
    
    repartitionByGroupingColumn = Param(Params._dummy(), "repartitionByGroupingColumn", "Repartition training data according to grouping column, on by default.", typeConverter=TypeConverters.toBoolean)
    
    samplingMode = Param(Params._dummy(), "samplingMode", "Data sampling for streaming mode. Sampled data is used to define bins. 'global': sample from all data, 'subset': sample from first N rows, or 'fixed': Take first N rows as sample.Values can be global, subset, or fixed. Default is subset.", typeConverter=TypeConverters.toString)
    
    samplingSubsetSize = Param(Params._dummy(), "samplingSubsetSize", "Specify subset size N for the sampling mode 'subset'. 'binSampleCount' rows will be chosen from the first N values of the dataset. Subset can be used when rows are expected to be random and data is huge.", typeConverter=TypeConverters.toInt)
    
    seed = Param(Params._dummy(), "seed", "Main seed, used to generate other seeds", typeConverter=TypeConverters.toInt)
    
    skipDrop = Param(Params._dummy(), "skipDrop", "Probability of skipping the dropout procedure during a boosting iteration", typeConverter=TypeConverters.toFloat)
    
    slotNames = Param(Params._dummy(), "slotNames", "List of slot names in the features column", typeConverter=TypeConverters.toListString)
    
    timeout = Param(Params._dummy(), "timeout", "Timeout in seconds", typeConverter=TypeConverters.toFloat)
    
    topK = Param(Params._dummy(), "topK", "The top_k value used in Voting parallel, set this to larger value for more accurate result, but it will slow down the training speed. It should be greater than 0", typeConverter=TypeConverters.toInt)
    
    topRate = Param(Params._dummy(), "topRate", "The retain ratio of large gradient data. Only used in goss.", typeConverter=TypeConverters.toFloat)
    
    uniformDrop = Param(Params._dummy(), "uniformDrop", "Set this to true to use uniform drop in dart mode", typeConverter=TypeConverters.toBoolean)
    
    useBarrierExecutionMode = Param(Params._dummy(), "useBarrierExecutionMode", "Barrier execution mode which uses a barrier stage, off by default.", typeConverter=TypeConverters.toBoolean)
    
    useMissing = Param(Params._dummy(), "useMissing", "Set this to false to disable the special handle of missing value", typeConverter=TypeConverters.toBoolean)
    
    useSingleDatasetMode = Param(Params._dummy(), "useSingleDatasetMode", "Use single dataset execution mode to create a single native dataset per executor (singleton) to reduce memory and communication overhead.", typeConverter=TypeConverters.toBoolean)
    
    validationIndicatorCol = Param(Params._dummy(), "validationIndicatorCol", "Indicates whether the row is for training or validation", typeConverter=TypeConverters.toString)
    
    verbosity = Param(Params._dummy(), "verbosity", "Verbosity where lt 0 is Fatal, eq 0 is Error, eq 1 is Info, gt 1 is Debug", typeConverter=TypeConverters.toInt)
    
    weightCol = Param(Params._dummy(), "weightCol", "The name of the weight column", typeConverter=TypeConverters.toString)
    
    xGBoostDartMode = Param(Params._dummy(), "xGBoostDartMode", "Set this to true to use xgboost dart mode", typeConverter=TypeConverters.toBoolean)
    
    zeroAsMissing = Param(Params._dummy(), "zeroAsMissing", "Set to true to treat all zero as missing values (including the unshown values in LibSVM / sparse matrices). Set to false to use na for representing missing values", typeConverter=TypeConverters.toBoolean)

    
    @keyword_only
    def __init__(
        self,
        java_obj=None,
        baggingFraction=1.0,
        baggingFreq=0,
        baggingSeed=3,
        binSampleCount=200000,
        boostFromAverage=True,
        boostingType="gbdt",
        catSmooth=10.0,
        categoricalSlotIndexes=[],
        categoricalSlotNames=[],
        catl2=10.0,
        chunkSize=10000,
        dataRandomSeed=1,
        dataTransferMode="streaming",
        defaultListenPort=12400,
        deterministic=False,
        driverListenPort=0,
        dropRate=0.1,
        dropSeed=4,
        earlyStoppingRound=0,
        evalAt=[1,2,3,4,5],
        executionMode=None,
        extraSeed=6,
        featureFraction=1.0,
        featureFractionByNode=None,
        featureFractionSeed=2,
        featuresCol="features",
        featuresShapCol="",
        fobj=None,
        groupCol=None,
        improvementTolerance=0.0,
        initScoreCol=None,
        isEnableSparse=True,
        isProvideTrainingMetric=False,
        labelCol="label",
        labelGain=[],
        lambdaL1=0.0,
        lambdaL2=0.0,
        leafPredictionCol="",
        learningRate=0.1,
        matrixType="auto",
        maxBin=255,
        maxBinByFeature=[],
        maxCatThreshold=32,
        maxCatToOnehot=4,
        maxDeltaStep=0.0,
        maxDepth=-1,
        maxDrop=50,
        maxNumClasses=100,
        maxPosition=20,
        maxStreamingOMPThreads=16,
        metric="",
        microBatchSize=100,
        minDataInLeaf=20,
        minDataPerBin=3,
        minDataPerGroup=100,
        minGainToSplit=0.0,
        minSumHessianInLeaf=0.001,
        modelString="",
        monotoneConstraints=[],
        monotoneConstraintsMethod="basic",
        monotonePenalty=0.0,
        negBaggingFraction=1.0,
        numBatches=0,
        numIterations=100,
        numLeaves=31,
        numTasks=0,
        numThreads=0,
        objective="lambdarank",
        objectiveSeed=5,
        otherRate=0.1,
        parallelism="data_parallel",
        passThroughArgs="",
        posBaggingFraction=1.0,
        predictDisableShapeCheck=False,
        predictionCol="prediction",
        referenceDataset=None,
        repartitionByGroupingColumn=True,
        samplingMode="subset",
        samplingSubsetSize=1000000,
        seed=None,
        skipDrop=0.5,
        slotNames=[],
        timeout=1200.0,
        topK=20,
        topRate=0.2,
        uniformDrop=False,
        useBarrierExecutionMode=False,
        useMissing=True,
        useSingleDatasetMode=True,
        validationIndicatorCol=None,
        verbosity=-1,
        weightCol=None,
        xGBoostDartMode=False,
        zeroAsMissing=False
        ):
        super(LightGBMRanker, self).__init__()
        if java_obj is None:
            self._java_obj = self._new_java_obj("com.microsoft.azure.synapse.ml.lightgbm.LightGBMRanker", self.uid)
        else:
            self._java_obj = java_obj
        self._setDefault(baggingFraction=1.0)
        self._setDefault(baggingFreq=0)
        self._setDefault(baggingSeed=3)
        self._setDefault(binSampleCount=200000)
        self._setDefault(boostFromAverage=True)
        self._setDefault(boostingType="gbdt")
        self._setDefault(catSmooth=10.0)
        self._setDefault(categoricalSlotIndexes=[])
        self._setDefault(categoricalSlotNames=[])
        self._setDefault(catl2=10.0)
        self._setDefault(chunkSize=10000)
        self._setDefault(dataRandomSeed=1)
        self._setDefault(dataTransferMode="streaming")
        self._setDefault(defaultListenPort=12400)
        self._setDefault(deterministic=False)
        self._setDefault(driverListenPort=0)
        self._setDefault(dropRate=0.1)
        self._setDefault(dropSeed=4)
        self._setDefault(earlyStoppingRound=0)
        self._setDefault(evalAt=[1,2,3,4,5])
        self._setDefault(extraSeed=6)
        self._setDefault(featureFraction=1.0)
        self._setDefault(featureFractionSeed=2)
        self._setDefault(featuresCol="features")
        self._setDefault(featuresShapCol="")
        self._setDefault(improvementTolerance=0.0)
        self._setDefault(isEnableSparse=True)
        self._setDefault(isProvideTrainingMetric=False)
        self._setDefault(labelCol="label")
        self._setDefault(labelGain=[])
        self._setDefault(lambdaL1=0.0)
        self._setDefault(lambdaL2=0.0)
        self._setDefault(leafPredictionCol="")
        self._setDefault(learningRate=0.1)
        self._setDefault(matrixType="auto")
        self._setDefault(maxBin=255)
        self._setDefault(maxBinByFeature=[])
        self._setDefault(maxCatThreshold=32)
        self._setDefault(maxCatToOnehot=4)
        self._setDefault(maxDeltaStep=0.0)
        self._setDefault(maxDepth=-1)
        self._setDefault(maxDrop=50)
        self._setDefault(maxNumClasses=100)
        self._setDefault(maxPosition=20)
        self._setDefault(maxStreamingOMPThreads=16)
        self._setDefault(metric="")
        self._setDefault(microBatchSize=100)
        self._setDefault(minDataInLeaf=20)
        self._setDefault(minDataPerBin=3)
        self._setDefault(minDataPerGroup=100)
        self._setDefault(minGainToSplit=0.0)
        self._setDefault(minSumHessianInLeaf=0.001)
        self._setDefault(modelString="")
        self._setDefault(monotoneConstraints=[])
        self._setDefault(monotoneConstraintsMethod="basic")
        self._setDefault(monotonePenalty=0.0)
        self._setDefault(negBaggingFraction=1.0)
        self._setDefault(numBatches=0)
        self._setDefault(numIterations=100)
        self._setDefault(numLeaves=31)
        self._setDefault(numTasks=0)
        self._setDefault(numThreads=0)
        self._setDefault(objective="lambdarank")
        self._setDefault(objectiveSeed=5)
        self._setDefault(otherRate=0.1)
        self._setDefault(parallelism="data_parallel")
        self._setDefault(passThroughArgs="")
        self._setDefault(posBaggingFraction=1.0)
        self._setDefault(predictDisableShapeCheck=False)
        self._setDefault(predictionCol="prediction")
        self._setDefault(repartitionByGroupingColumn=True)
        self._setDefault(samplingMode="subset")
        self._setDefault(samplingSubsetSize=1000000)
        self._setDefault(skipDrop=0.5)
        self._setDefault(slotNames=[])
        self._setDefault(timeout=1200.0)
        self._setDefault(topK=20)
        self._setDefault(topRate=0.2)
        self._setDefault(uniformDrop=False)
        self._setDefault(useBarrierExecutionMode=False)
        self._setDefault(useMissing=True)
        self._setDefault(useSingleDatasetMode=True)
        self._setDefault(verbosity=-1)
        self._setDefault(xGBoostDartMode=False)
        self._setDefault(zeroAsMissing=False)
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
        baggingFraction=1.0,
        baggingFreq=0,
        baggingSeed=3,
        binSampleCount=200000,
        boostFromAverage=True,
        boostingType="gbdt",
        catSmooth=10.0,
        categoricalSlotIndexes=[],
        categoricalSlotNames=[],
        catl2=10.0,
        chunkSize=10000,
        dataRandomSeed=1,
        dataTransferMode="streaming",
        defaultListenPort=12400,
        deterministic=False,
        driverListenPort=0,
        dropRate=0.1,
        dropSeed=4,
        earlyStoppingRound=0,
        evalAt=[1,2,3,4,5],
        executionMode=None,
        extraSeed=6,
        featureFraction=1.0,
        featureFractionByNode=None,
        featureFractionSeed=2,
        featuresCol="features",
        featuresShapCol="",
        fobj=None,
        groupCol=None,
        improvementTolerance=0.0,
        initScoreCol=None,
        isEnableSparse=True,
        isProvideTrainingMetric=False,
        labelCol="label",
        labelGain=[],
        lambdaL1=0.0,
        lambdaL2=0.0,
        leafPredictionCol="",
        learningRate=0.1,
        matrixType="auto",
        maxBin=255,
        maxBinByFeature=[],
        maxCatThreshold=32,
        maxCatToOnehot=4,
        maxDeltaStep=0.0,
        maxDepth=-1,
        maxDrop=50,
        maxNumClasses=100,
        maxPosition=20,
        maxStreamingOMPThreads=16,
        metric="",
        microBatchSize=100,
        minDataInLeaf=20,
        minDataPerBin=3,
        minDataPerGroup=100,
        minGainToSplit=0.0,
        minSumHessianInLeaf=0.001,
        modelString="",
        monotoneConstraints=[],
        monotoneConstraintsMethod="basic",
        monotonePenalty=0.0,
        negBaggingFraction=1.0,
        numBatches=0,
        numIterations=100,
        numLeaves=31,
        numTasks=0,
        numThreads=0,
        objective="lambdarank",
        objectiveSeed=5,
        otherRate=0.1,
        parallelism="data_parallel",
        passThroughArgs="",
        posBaggingFraction=1.0,
        predictDisableShapeCheck=False,
        predictionCol="prediction",
        referenceDataset=None,
        repartitionByGroupingColumn=True,
        samplingMode="subset",
        samplingSubsetSize=1000000,
        seed=None,
        skipDrop=0.5,
        slotNames=[],
        timeout=1200.0,
        topK=20,
        topRate=0.2,
        uniformDrop=False,
        useBarrierExecutionMode=False,
        useMissing=True,
        useSingleDatasetMode=True,
        validationIndicatorCol=None,
        verbosity=-1,
        weightCol=None,
        xGBoostDartMode=False,
        zeroAsMissing=False
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
        return "com.microsoft.azure.synapse.ml.lightgbm.LightGBMRanker"

    @staticmethod
    def _from_java(java_stage):
        module_name=LightGBMRanker.__module__
        module_name=module_name.rsplit(".", 1)[0] + ".LightGBMRanker"
        return from_java(java_stage, module_name)

    def setBaggingFraction(self, value):
        """
        Args:
            baggingFraction: Bagging fraction
        """
        self._set(baggingFraction=value)
        return self
    
    def setBaggingFreq(self, value):
        """
        Args:
            baggingFreq: Bagging frequency
        """
        self._set(baggingFreq=value)
        return self
    
    def setBaggingSeed(self, value):
        """
        Args:
            baggingSeed: Bagging seed
        """
        self._set(baggingSeed=value)
        return self
    
    def setBinSampleCount(self, value):
        """
        Args:
            binSampleCount: Number of samples considered at computing histogram bins
        """
        self._set(binSampleCount=value)
        return self
    
    def setBoostFromAverage(self, value):
        """
        Args:
            boostFromAverage: Adjusts initial score to the mean of labels for faster convergence
        """
        self._set(boostFromAverage=value)
        return self
    
    def setBoostingType(self, value):
        """
        Args:
            boostingType: Default gbdt = traditional Gradient Boosting Decision Tree. Options are: gbdt, gbrt, rf (Random Forest), random_forest, dart (Dropouts meet Multiple Additive Regression Trees), goss (Gradient-based One-Side Sampling). 
        """
        self._set(boostingType=value)
        return self
    
    def setCatSmooth(self, value):
        """
        Args:
            catSmooth: this can reduce the effect of noises in categorical features, especially for categories with few data
        """
        self._set(catSmooth=value)
        return self
    
    def setCategoricalSlotIndexes(self, value):
        """
        Args:
            categoricalSlotIndexes: List of categorical column indexes, the slot index in the features column
        """
        self._set(categoricalSlotIndexes=value)
        return self
    
    def setCategoricalSlotNames(self, value):
        """
        Args:
            categoricalSlotNames: List of categorical column slot names, the slot name in the features column
        """
        self._set(categoricalSlotNames=value)
        return self
    
    def setCatl2(self, value):
        """
        Args:
            catl2: L2 regularization in categorical split
        """
        self._set(catl2=value)
        return self
    
    def setChunkSize(self, value):
        """
        Args:
            chunkSize: Advanced parameter to specify the chunk size for copying Java data to native.  If set too high, memory may be wasted, but if set too low, performance may be reduced during data copy.If dataset size is known beforehand, set to the number of rows in the dataset.
        """
        self._set(chunkSize=value)
        return self
    
    def setDataRandomSeed(self, value):
        """
        Args:
            dataRandomSeed: Random seed for sampling data to construct histogram bins.
        """
        self._set(dataRandomSeed=value)
        return self
    
    def setDataTransferMode(self, value):
        """
        Args:
            dataTransferMode: Specify how SynapseML transfers data from Spark to LightGBM.  Values can be streaming, bulk. Default is streaming.
        """
        self._set(dataTransferMode=value)
        return self
    
    def setDefaultListenPort(self, value):
        """
        Args:
            defaultListenPort: The default listen port on executors, used for testing
        """
        self._set(defaultListenPort=value)
        return self
    
    def setDeterministic(self, value):
        """
        Args:
            deterministic: Used only with cpu devide type. Setting this to true should ensure stable results when using the same data and the same parameters.  Note: setting this to true may slow down training.  To avoid potential instability due to numerical issues, please set force_col_wise=true or force_row_wise=true when setting deterministic=true
        """
        self._set(deterministic=value)
        return self
    
    def setDriverListenPort(self, value):
        """
        Args:
            driverListenPort: The listen port on a driver. Default value is 0 (random)
        """
        self._set(driverListenPort=value)
        return self
    
    def setDropRate(self, value):
        """
        Args:
            dropRate: Dropout rate: a fraction of previous trees to drop during the dropout
        """
        self._set(dropRate=value)
        return self
    
    def setDropSeed(self, value):
        """
        Args:
            dropSeed: Random seed to choose dropping models. Only used in dart.
        """
        self._set(dropSeed=value)
        return self
    
    def setEarlyStoppingRound(self, value):
        """
        Args:
            earlyStoppingRound: Early stopping round
        """
        self._set(earlyStoppingRound=value)
        return self
    
    def setEvalAt(self, value):
        """
        Args:
            evalAt: NDCG and MAP evaluation positions, separated by comma
        """
        self._set(evalAt=value)
        return self
    
    def setExecutionMode(self, value):
        """
        Args:
            executionMode: Deprecated. Please use dataTransferMode.
        """
        self._set(executionMode=value)
        return self
    
    def setExtraSeed(self, value):
        """
        Args:
            extraSeed: Random seed for selecting threshold when extra_trees is true
        """
        self._set(extraSeed=value)
        return self
    
    def setFeatureFraction(self, value):
        """
        Args:
            featureFraction: Feature fraction
        """
        self._set(featureFraction=value)
        return self
    
    def setFeatureFractionByNode(self, value):
        """
        Args:
            featureFractionByNode: Feature fraction by node
        """
        self._set(featureFractionByNode=value)
        return self
    
    def setFeatureFractionSeed(self, value):
        """
        Args:
            featureFractionSeed: Feature fraction seed
        """
        self._set(featureFractionSeed=value)
        return self
    
    def setFeaturesCol(self, value):
        """
        Args:
            featuresCol: features column name
        """
        self._set(featuresCol=value)
        return self
    
    def setFeaturesShapCol(self, value):
        """
        Args:
            featuresShapCol: Output SHAP vector column name after prediction containing the feature contribution values
        """
        self._set(featuresShapCol=value)
        return self
    
    def setFobj(self, value):
        """
        Args:
            fobj: Customized objective function. Should accept two parameters: preds, train_data, and return (grad, hess).
        """
        self._set(fobj=value)
        return self
    
    def setGroupCol(self, value):
        """
        Args:
            groupCol: The name of the group column
        """
        self._set(groupCol=value)
        return self
    
    def setImprovementTolerance(self, value):
        """
        Args:
            improvementTolerance: Tolerance to consider improvement in metric
        """
        self._set(improvementTolerance=value)
        return self
    
    def setInitScoreCol(self, value):
        """
        Args:
            initScoreCol: The name of the initial score column, used for continued training
        """
        self._set(initScoreCol=value)
        return self
    
    def setIsEnableSparse(self, value):
        """
        Args:
            isEnableSparse: Used to enable/disable sparse optimization
        """
        self._set(isEnableSparse=value)
        return self
    
    def setIsProvideTrainingMetric(self, value):
        """
        Args:
            isProvideTrainingMetric: Whether output metric result over training dataset.
        """
        self._set(isProvideTrainingMetric=value)
        return self
    
    def setLabelCol(self, value):
        """
        Args:
            labelCol: label column name
        """
        self._set(labelCol=value)
        return self
    
    def setLabelGain(self, value):
        """
        Args:
            labelGain: graded relevance for each label in NDCG
        """
        self._set(labelGain=value)
        return self
    
    def setLambdaL1(self, value):
        """
        Args:
            lambdaL1: L1 regularization
        """
        self._set(lambdaL1=value)
        return self
    
    def setLambdaL2(self, value):
        """
        Args:
            lambdaL2: L2 regularization
        """
        self._set(lambdaL2=value)
        return self
    
    def setLeafPredictionCol(self, value):
        """
        Args:
            leafPredictionCol: Predicted leaf indices's column name
        """
        self._set(leafPredictionCol=value)
        return self
    
    def setLearningRate(self, value):
        """
        Args:
            learningRate: Learning rate or shrinkage rate
        """
        self._set(learningRate=value)
        return self
    
    def setMatrixType(self, value):
        """
        Args:
            matrixType: Advanced parameter to specify whether the native lightgbm matrix constructed should be sparse or dense.  Values can be auto, sparse or dense. Default value is auto, which samples first ten rows to determine type.
        """
        self._set(matrixType=value)
        return self
    
    def setMaxBin(self, value):
        """
        Args:
            maxBin: Max bin
        """
        self._set(maxBin=value)
        return self
    
    def setMaxBinByFeature(self, value):
        """
        Args:
            maxBinByFeature: Max number of bins for each feature
        """
        self._set(maxBinByFeature=value)
        return self
    
    def setMaxCatThreshold(self, value):
        """
        Args:
            maxCatThreshold: limit number of split points considered for categorical features
        """
        self._set(maxCatThreshold=value)
        return self
    
    def setMaxCatToOnehot(self, value):
        """
        Args:
            maxCatToOnehot: when number of categories of one feature smaller than or equal to this, one-vs-other split algorithm will be used
        """
        self._set(maxCatToOnehot=value)
        return self
    
    def setMaxDeltaStep(self, value):
        """
        Args:
            maxDeltaStep: Used to limit the max output of tree leaves
        """
        self._set(maxDeltaStep=value)
        return self
    
    def setMaxDepth(self, value):
        """
        Args:
            maxDepth: Max depth
        """
        self._set(maxDepth=value)
        return self
    
    def setMaxDrop(self, value):
        """
        Args:
            maxDrop: Max number of dropped trees during one boosting iteration
        """
        self._set(maxDrop=value)
        return self
    
    def setMaxNumClasses(self, value):
        """
        Args:
            maxNumClasses: Number of max classes to infer numClass in multi-class classification.
        """
        self._set(maxNumClasses=value)
        return self
    
    def setMaxPosition(self, value):
        """
        Args:
            maxPosition: optimized NDCG at this position
        """
        self._set(maxPosition=value)
        return self
    
    def setMaxStreamingOMPThreads(self, value):
        """
        Args:
            maxStreamingOMPThreads: Maximum number of OpenMP threads used by a LightGBM thread. Used only for thread-safe buffer allocation. Use -1 to use OpenMP default, but in a Spark environment it's best to set a fixed value.
        """
        self._set(maxStreamingOMPThreads=value)
        return self
    
    def setMetric(self, value):
        """
        Args:
            metric: Metrics to be evaluated on the evaluation data.  Options are: empty string or not specified means that metric corresponding to specified objective will be used (this is possible only for pre-defined objective functions, otherwise no evaluation metric will be added). None (string, not a None value) means that no metric will be registered, aliases: na, null, custom. l1, absolute loss, aliases: mean_absolute_error, mae, regression_l1. l2, square loss, aliases: mean_squared_error, mse, regression_l2, regression. rmse, root square loss, aliases: root_mean_squared_error, l2_root. quantile, Quantile regression. mape, MAPE loss, aliases: mean_absolute_percentage_error. huber, Huber loss. fair, Fair loss. poisson, negative log-likelihood for Poisson regression. gamma, negative log-likelihood for Gamma regression. gamma_deviance, residual deviance for Gamma regression. tweedie, negative log-likelihood for Tweedie regression. ndcg, NDCG, aliases: lambdarank. map, MAP, aliases: mean_average_precision. auc, AUC. binary_logloss, log loss, aliases: binary. binary_error, for one sample: 0 for correct classification, 1 for error classification. multi_logloss, log loss for multi-class classification, aliases: multiclass, softmax, multiclassova, multiclass_ova, ova, ovr. multi_error, error rate for multi-class classification. cross_entropy, cross-entropy (with optional linear weights), aliases: xentropy. cross_entropy_lambda, intensity-weighted cross-entropy, aliases: xentlambda. kullback_leibler, Kullback-Leibler divergence, aliases: kldiv. 
        """
        self._set(metric=value)
        return self
    
    def setMicroBatchSize(self, value):
        """
        Args:
            microBatchSize: Specify how many elements are sent in a streaming micro-batch.
        """
        self._set(microBatchSize=value)
        return self
    
    def setMinDataInLeaf(self, value):
        """
        Args:
            minDataInLeaf: Minimal number of data in one leaf. Can be used to deal with over-fitting.
        """
        self._set(minDataInLeaf=value)
        return self
    
    def setMinDataPerBin(self, value):
        """
        Args:
            minDataPerBin: Minimal number of data inside one bin
        """
        self._set(minDataPerBin=value)
        return self
    
    def setMinDataPerGroup(self, value):
        """
        Args:
            minDataPerGroup: minimal number of data per categorical group
        """
        self._set(minDataPerGroup=value)
        return self
    
    def setMinGainToSplit(self, value):
        """
        Args:
            minGainToSplit: The minimal gain to perform split
        """
        self._set(minGainToSplit=value)
        return self
    
    def setMinSumHessianInLeaf(self, value):
        """
        Args:
            minSumHessianInLeaf: Minimal sum hessian in one leaf
        """
        self._set(minSumHessianInLeaf=value)
        return self
    
    def setModelString(self, value):
        """
        Args:
            modelString: LightGBM model to retrain
        """
        self._set(modelString=value)
        return self
    
    def setMonotoneConstraints(self, value):
        """
        Args:
            monotoneConstraints: used for constraints of monotonic features. 1 means increasing, -1 means decreasing, 0 means non-constraint. Specify all features in order.
        """
        self._set(monotoneConstraints=value)
        return self
    
    def setMonotoneConstraintsMethod(self, value):
        """
        Args:
            monotoneConstraintsMethod: Monotone constraints method. basic, intermediate, or advanced.
        """
        self._set(monotoneConstraintsMethod=value)
        return self
    
    def setMonotonePenalty(self, value):
        """
        Args:
            monotonePenalty: A penalization parameter X forbids any monotone splits on the first X (rounded down) level(s) of the tree.
        """
        self._set(monotonePenalty=value)
        return self
    
    def setNegBaggingFraction(self, value):
        """
        Args:
            negBaggingFraction: Negative Bagging fraction
        """
        self._set(negBaggingFraction=value)
        return self
    
    def setNumBatches(self, value):
        """
        Args:
            numBatches: If greater than 0, splits data into separate batches during training
        """
        self._set(numBatches=value)
        return self
    
    def setNumIterations(self, value):
        """
        Args:
            numIterations: Number of iterations, LightGBM constructs num_class * num_iterations trees
        """
        self._set(numIterations=value)
        return self
    
    def setNumLeaves(self, value):
        """
        Args:
            numLeaves: Number of leaves
        """
        self._set(numLeaves=value)
        return self
    
    def setNumTasks(self, value):
        """
        Args:
            numTasks: Advanced parameter to specify the number of tasks.  SynapseML tries to guess this based on cluster configuration, but this parameter can be used to override.
        """
        self._set(numTasks=value)
        return self
    
    def setNumThreads(self, value):
        """
        Args:
            numThreads: Number of threads per executor for LightGBM. For the best speed, set this to the number of real CPU cores.
        """
        self._set(numThreads=value)
        return self
    
    def setObjective(self, value):
        """
        Args:
            objective: The Objective. For regression applications, this can be: regression_l2, regression_l1, huber, fair, poisson, quantile, mape, gamma or tweedie. For classification applications, this can be: binary, multiclass, or multiclassova. 
        """
        self._set(objective=value)
        return self
    
    def setObjectiveSeed(self, value):
        """
        Args:
            objectiveSeed: Random seed for objectives, if random process is needed.  Currently used only for rank_xendcg objective.
        """
        self._set(objectiveSeed=value)
        return self
    
    def setOtherRate(self, value):
        """
        Args:
            otherRate: The retain ratio of small gradient data. Only used in goss.
        """
        self._set(otherRate=value)
        return self
    
    def setParallelism(self, value):
        """
        Args:
            parallelism: Tree learner parallelism, can be set to data_parallel or voting_parallel
        """
        self._set(parallelism=value)
        return self
    
    def setPassThroughArgs(self, value):
        """
        Args:
            passThroughArgs: Direct string to pass through to LightGBM library (appended with other explicitly set params). Will override any parameters given with explicit setters. Can include multiple parameters in one string. e.g., force_row_wise=true
        """
        self._set(passThroughArgs=value)
        return self
    
    def setPosBaggingFraction(self, value):
        """
        Args:
            posBaggingFraction: Positive Bagging fraction
        """
        self._set(posBaggingFraction=value)
        return self
    
    def setPredictDisableShapeCheck(self, value):
        """
        Args:
            predictDisableShapeCheck: control whether or not LightGBM raises an error when you try to predict on data with a different number of features than the training data
        """
        self._set(predictDisableShapeCheck=value)
        return self
    
    def setPredictionCol(self, value):
        """
        Args:
            predictionCol: prediction column name
        """
        self._set(predictionCol=value)
        return self
    
    def setReferenceDataset(self, value):
        """
        Args:
            referenceDataset: The reference Dataset that was used for the fit. If using samplingMode=custom, this must be set before fit().
        """
        self._set(referenceDataset=value)
        return self
    
    def setRepartitionByGroupingColumn(self, value):
        """
        Args:
            repartitionByGroupingColumn: Repartition training data according to grouping column, on by default.
        """
        self._set(repartitionByGroupingColumn=value)
        return self
    
    def setSamplingMode(self, value):
        """
        Args:
            samplingMode: Data sampling for streaming mode. Sampled data is used to define bins. 'global': sample from all data, 'subset': sample from first N rows, or 'fixed': Take first N rows as sample.Values can be global, subset, or fixed. Default is subset.
        """
        self._set(samplingMode=value)
        return self
    
    def setSamplingSubsetSize(self, value):
        """
        Args:
            samplingSubsetSize: Specify subset size N for the sampling mode 'subset'. 'binSampleCount' rows will be chosen from the first N values of the dataset. Subset can be used when rows are expected to be random and data is huge.
        """
        self._set(samplingSubsetSize=value)
        return self
    
    def setSeed(self, value):
        """
        Args:
            seed: Main seed, used to generate other seeds
        """
        self._set(seed=value)
        return self
    
    def setSkipDrop(self, value):
        """
        Args:
            skipDrop: Probability of skipping the dropout procedure during a boosting iteration
        """
        self._set(skipDrop=value)
        return self
    
    def setSlotNames(self, value):
        """
        Args:
            slotNames: List of slot names in the features column
        """
        self._set(slotNames=value)
        return self
    
    def setTimeout(self, value):
        """
        Args:
            timeout: Timeout in seconds
        """
        self._set(timeout=value)
        return self
    
    def setTopK(self, value):
        """
        Args:
            topK: The top_k value used in Voting parallel, set this to larger value for more accurate result, but it will slow down the training speed. It should be greater than 0
        """
        self._set(topK=value)
        return self
    
    def setTopRate(self, value):
        """
        Args:
            topRate: The retain ratio of large gradient data. Only used in goss.
        """
        self._set(topRate=value)
        return self
    
    def setUniformDrop(self, value):
        """
        Args:
            uniformDrop: Set this to true to use uniform drop in dart mode
        """
        self._set(uniformDrop=value)
        return self
    
    def setUseBarrierExecutionMode(self, value):
        """
        Args:
            useBarrierExecutionMode: Barrier execution mode which uses a barrier stage, off by default.
        """
        self._set(useBarrierExecutionMode=value)
        return self
    
    def setUseMissing(self, value):
        """
        Args:
            useMissing: Set this to false to disable the special handle of missing value
        """
        self._set(useMissing=value)
        return self
    
    def setUseSingleDatasetMode(self, value):
        """
        Args:
            useSingleDatasetMode: Use single dataset execution mode to create a single native dataset per executor (singleton) to reduce memory and communication overhead.
        """
        self._set(useSingleDatasetMode=value)
        return self
    
    def setValidationIndicatorCol(self, value):
        """
        Args:
            validationIndicatorCol: Indicates whether the row is for training or validation
        """
        self._set(validationIndicatorCol=value)
        return self
    
    def setVerbosity(self, value):
        """
        Args:
            verbosity: Verbosity where lt 0 is Fatal, eq 0 is Error, eq 1 is Info, gt 1 is Debug
        """
        self._set(verbosity=value)
        return self
    
    def setWeightCol(self, value):
        """
        Args:
            weightCol: The name of the weight column
        """
        self._set(weightCol=value)
        return self
    
    def setXGBoostDartMode(self, value):
        """
        Args:
            xGBoostDartMode: Set this to true to use xgboost dart mode
        """
        self._set(xGBoostDartMode=value)
        return self
    
    def setZeroAsMissing(self, value):
        """
        Args:
            zeroAsMissing: Set to true to treat all zero as missing values (including the unshown values in LibSVM / sparse matrices). Set to false to use na for representing missing values
        """
        self._set(zeroAsMissing=value)
        return self

    
    def getBaggingFraction(self):
        """
        Returns:
            baggingFraction: Bagging fraction
        """
        return self.getOrDefault(self.baggingFraction)
    
    
    def getBaggingFreq(self):
        """
        Returns:
            baggingFreq: Bagging frequency
        """
        return self.getOrDefault(self.baggingFreq)
    
    
    def getBaggingSeed(self):
        """
        Returns:
            baggingSeed: Bagging seed
        """
        return self.getOrDefault(self.baggingSeed)
    
    
    def getBinSampleCount(self):
        """
        Returns:
            binSampleCount: Number of samples considered at computing histogram bins
        """
        return self.getOrDefault(self.binSampleCount)
    
    
    def getBoostFromAverage(self):
        """
        Returns:
            boostFromAverage: Adjusts initial score to the mean of labels for faster convergence
        """
        return self.getOrDefault(self.boostFromAverage)
    
    
    def getBoostingType(self):
        """
        Returns:
            boostingType: Default gbdt = traditional Gradient Boosting Decision Tree. Options are: gbdt, gbrt, rf (Random Forest), random_forest, dart (Dropouts meet Multiple Additive Regression Trees), goss (Gradient-based One-Side Sampling). 
        """
        return self.getOrDefault(self.boostingType)
    
    
    def getCatSmooth(self):
        """
        Returns:
            catSmooth: this can reduce the effect of noises in categorical features, especially for categories with few data
        """
        return self.getOrDefault(self.catSmooth)
    
    
    def getCategoricalSlotIndexes(self):
        """
        Returns:
            categoricalSlotIndexes: List of categorical column indexes, the slot index in the features column
        """
        return self.getOrDefault(self.categoricalSlotIndexes)
    
    
    def getCategoricalSlotNames(self):
        """
        Returns:
            categoricalSlotNames: List of categorical column slot names, the slot name in the features column
        """
        return self.getOrDefault(self.categoricalSlotNames)
    
    
    def getCatl2(self):
        """
        Returns:
            catl2: L2 regularization in categorical split
        """
        return self.getOrDefault(self.catl2)
    
    
    def getChunkSize(self):
        """
        Returns:
            chunkSize: Advanced parameter to specify the chunk size for copying Java data to native.  If set too high, memory may be wasted, but if set too low, performance may be reduced during data copy.If dataset size is known beforehand, set to the number of rows in the dataset.
        """
        return self.getOrDefault(self.chunkSize)
    
    
    def getDataRandomSeed(self):
        """
        Returns:
            dataRandomSeed: Random seed for sampling data to construct histogram bins.
        """
        return self.getOrDefault(self.dataRandomSeed)
    
    
    def getDataTransferMode(self):
        """
        Returns:
            dataTransferMode: Specify how SynapseML transfers data from Spark to LightGBM.  Values can be streaming, bulk. Default is streaming.
        """
        return self.getOrDefault(self.dataTransferMode)
    
    
    def getDefaultListenPort(self):
        """
        Returns:
            defaultListenPort: The default listen port on executors, used for testing
        """
        return self.getOrDefault(self.defaultListenPort)
    
    
    def getDeterministic(self):
        """
        Returns:
            deterministic: Used only with cpu devide type. Setting this to true should ensure stable results when using the same data and the same parameters.  Note: setting this to true may slow down training.  To avoid potential instability due to numerical issues, please set force_col_wise=true or force_row_wise=true when setting deterministic=true
        """
        return self.getOrDefault(self.deterministic)
    
    
    def getDriverListenPort(self):
        """
        Returns:
            driverListenPort: The listen port on a driver. Default value is 0 (random)
        """
        return self.getOrDefault(self.driverListenPort)
    
    
    def getDropRate(self):
        """
        Returns:
            dropRate: Dropout rate: a fraction of previous trees to drop during the dropout
        """
        return self.getOrDefault(self.dropRate)
    
    
    def getDropSeed(self):
        """
        Returns:
            dropSeed: Random seed to choose dropping models. Only used in dart.
        """
        return self.getOrDefault(self.dropSeed)
    
    
    def getEarlyStoppingRound(self):
        """
        Returns:
            earlyStoppingRound: Early stopping round
        """
        return self.getOrDefault(self.earlyStoppingRound)
    
    
    def getEvalAt(self):
        """
        Returns:
            evalAt: NDCG and MAP evaluation positions, separated by comma
        """
        return self.getOrDefault(self.evalAt)
    
    
    def getExecutionMode(self):
        """
        Returns:
            executionMode: Deprecated. Please use dataTransferMode.
        """
        return self.getOrDefault(self.executionMode)
    
    
    def getExtraSeed(self):
        """
        Returns:
            extraSeed: Random seed for selecting threshold when extra_trees is true
        """
        return self.getOrDefault(self.extraSeed)
    
    
    def getFeatureFraction(self):
        """
        Returns:
            featureFraction: Feature fraction
        """
        return self.getOrDefault(self.featureFraction)
    
    
    def getFeatureFractionByNode(self):
        """
        Returns:
            featureFractionByNode: Feature fraction by node
        """
        return self.getOrDefault(self.featureFractionByNode)
    
    
    def getFeatureFractionSeed(self):
        """
        Returns:
            featureFractionSeed: Feature fraction seed
        """
        return self.getOrDefault(self.featureFractionSeed)
    
    
    def getFeaturesCol(self):
        """
        Returns:
            featuresCol: features column name
        """
        return self.getOrDefault(self.featuresCol)
    
    
    def getFeaturesShapCol(self):
        """
        Returns:
            featuresShapCol: Output SHAP vector column name after prediction containing the feature contribution values
        """
        return self.getOrDefault(self.featuresShapCol)
    
    
    def getFobj(self):
        """
        Returns:
            fobj: Customized objective function. Should accept two parameters: preds, train_data, and return (grad, hess).
        """
        return self.getOrDefault(self.fobj)
    
    
    def getGroupCol(self):
        """
        Returns:
            groupCol: The name of the group column
        """
        return self.getOrDefault(self.groupCol)
    
    
    def getImprovementTolerance(self):
        """
        Returns:
            improvementTolerance: Tolerance to consider improvement in metric
        """
        return self.getOrDefault(self.improvementTolerance)
    
    
    def getInitScoreCol(self):
        """
        Returns:
            initScoreCol: The name of the initial score column, used for continued training
        """
        return self.getOrDefault(self.initScoreCol)
    
    
    def getIsEnableSparse(self):
        """
        Returns:
            isEnableSparse: Used to enable/disable sparse optimization
        """
        return self.getOrDefault(self.isEnableSparse)
    
    
    def getIsProvideTrainingMetric(self):
        """
        Returns:
            isProvideTrainingMetric: Whether output metric result over training dataset.
        """
        return self.getOrDefault(self.isProvideTrainingMetric)
    
    
    def getLabelCol(self):
        """
        Returns:
            labelCol: label column name
        """
        return self.getOrDefault(self.labelCol)
    
    
    def getLabelGain(self):
        """
        Returns:
            labelGain: graded relevance for each label in NDCG
        """
        return self.getOrDefault(self.labelGain)
    
    
    def getLambdaL1(self):
        """
        Returns:
            lambdaL1: L1 regularization
        """
        return self.getOrDefault(self.lambdaL1)
    
    
    def getLambdaL2(self):
        """
        Returns:
            lambdaL2: L2 regularization
        """
        return self.getOrDefault(self.lambdaL2)
    
    
    def getLeafPredictionCol(self):
        """
        Returns:
            leafPredictionCol: Predicted leaf indices's column name
        """
        return self.getOrDefault(self.leafPredictionCol)
    
    
    def getLearningRate(self):
        """
        Returns:
            learningRate: Learning rate or shrinkage rate
        """
        return self.getOrDefault(self.learningRate)
    
    
    def getMatrixType(self):
        """
        Returns:
            matrixType: Advanced parameter to specify whether the native lightgbm matrix constructed should be sparse or dense.  Values can be auto, sparse or dense. Default value is auto, which samples first ten rows to determine type.
        """
        return self.getOrDefault(self.matrixType)
    
    
    def getMaxBin(self):
        """
        Returns:
            maxBin: Max bin
        """
        return self.getOrDefault(self.maxBin)
    
    
    def getMaxBinByFeature(self):
        """
        Returns:
            maxBinByFeature: Max number of bins for each feature
        """
        return self.getOrDefault(self.maxBinByFeature)
    
    
    def getMaxCatThreshold(self):
        """
        Returns:
            maxCatThreshold: limit number of split points considered for categorical features
        """
        return self.getOrDefault(self.maxCatThreshold)
    
    
    def getMaxCatToOnehot(self):
        """
        Returns:
            maxCatToOnehot: when number of categories of one feature smaller than or equal to this, one-vs-other split algorithm will be used
        """
        return self.getOrDefault(self.maxCatToOnehot)
    
    
    def getMaxDeltaStep(self):
        """
        Returns:
            maxDeltaStep: Used to limit the max output of tree leaves
        """
        return self.getOrDefault(self.maxDeltaStep)
    
    
    def getMaxDepth(self):
        """
        Returns:
            maxDepth: Max depth
        """
        return self.getOrDefault(self.maxDepth)
    
    
    def getMaxDrop(self):
        """
        Returns:
            maxDrop: Max number of dropped trees during one boosting iteration
        """
        return self.getOrDefault(self.maxDrop)
    
    
    def getMaxNumClasses(self):
        """
        Returns:
            maxNumClasses: Number of max classes to infer numClass in multi-class classification.
        """
        return self.getOrDefault(self.maxNumClasses)
    
    
    def getMaxPosition(self):
        """
        Returns:
            maxPosition: optimized NDCG at this position
        """
        return self.getOrDefault(self.maxPosition)
    
    
    def getMaxStreamingOMPThreads(self):
        """
        Returns:
            maxStreamingOMPThreads: Maximum number of OpenMP threads used by a LightGBM thread. Used only for thread-safe buffer allocation. Use -1 to use OpenMP default, but in a Spark environment it's best to set a fixed value.
        """
        return self.getOrDefault(self.maxStreamingOMPThreads)
    
    
    def getMetric(self):
        """
        Returns:
            metric: Metrics to be evaluated on the evaluation data.  Options are: empty string or not specified means that metric corresponding to specified objective will be used (this is possible only for pre-defined objective functions, otherwise no evaluation metric will be added). None (string, not a None value) means that no metric will be registered, aliases: na, null, custom. l1, absolute loss, aliases: mean_absolute_error, mae, regression_l1. l2, square loss, aliases: mean_squared_error, mse, regression_l2, regression. rmse, root square loss, aliases: root_mean_squared_error, l2_root. quantile, Quantile regression. mape, MAPE loss, aliases: mean_absolute_percentage_error. huber, Huber loss. fair, Fair loss. poisson, negative log-likelihood for Poisson regression. gamma, negative log-likelihood for Gamma regression. gamma_deviance, residual deviance for Gamma regression. tweedie, negative log-likelihood for Tweedie regression. ndcg, NDCG, aliases: lambdarank. map, MAP, aliases: mean_average_precision. auc, AUC. binary_logloss, log loss, aliases: binary. binary_error, for one sample: 0 for correct classification, 1 for error classification. multi_logloss, log loss for multi-class classification, aliases: multiclass, softmax, multiclassova, multiclass_ova, ova, ovr. multi_error, error rate for multi-class classification. cross_entropy, cross-entropy (with optional linear weights), aliases: xentropy. cross_entropy_lambda, intensity-weighted cross-entropy, aliases: xentlambda. kullback_leibler, Kullback-Leibler divergence, aliases: kldiv. 
        """
        return self.getOrDefault(self.metric)
    
    
    def getMicroBatchSize(self):
        """
        Returns:
            microBatchSize: Specify how many elements are sent in a streaming micro-batch.
        """
        return self.getOrDefault(self.microBatchSize)
    
    
    def getMinDataInLeaf(self):
        """
        Returns:
            minDataInLeaf: Minimal number of data in one leaf. Can be used to deal with over-fitting.
        """
        return self.getOrDefault(self.minDataInLeaf)
    
    
    def getMinDataPerBin(self):
        """
        Returns:
            minDataPerBin: Minimal number of data inside one bin
        """
        return self.getOrDefault(self.minDataPerBin)
    
    
    def getMinDataPerGroup(self):
        """
        Returns:
            minDataPerGroup: minimal number of data per categorical group
        """
        return self.getOrDefault(self.minDataPerGroup)
    
    
    def getMinGainToSplit(self):
        """
        Returns:
            minGainToSplit: The minimal gain to perform split
        """
        return self.getOrDefault(self.minGainToSplit)
    
    
    def getMinSumHessianInLeaf(self):
        """
        Returns:
            minSumHessianInLeaf: Minimal sum hessian in one leaf
        """
        return self.getOrDefault(self.minSumHessianInLeaf)
    
    
    def getModelString(self):
        """
        Returns:
            modelString: LightGBM model to retrain
        """
        return self.getOrDefault(self.modelString)
    
    
    def getMonotoneConstraints(self):
        """
        Returns:
            monotoneConstraints: used for constraints of monotonic features. 1 means increasing, -1 means decreasing, 0 means non-constraint. Specify all features in order.
        """
        return self.getOrDefault(self.monotoneConstraints)
    
    
    def getMonotoneConstraintsMethod(self):
        """
        Returns:
            monotoneConstraintsMethod: Monotone constraints method. basic, intermediate, or advanced.
        """
        return self.getOrDefault(self.monotoneConstraintsMethod)
    
    
    def getMonotonePenalty(self):
        """
        Returns:
            monotonePenalty: A penalization parameter X forbids any monotone splits on the first X (rounded down) level(s) of the tree.
        """
        return self.getOrDefault(self.monotonePenalty)
    
    
    def getNegBaggingFraction(self):
        """
        Returns:
            negBaggingFraction: Negative Bagging fraction
        """
        return self.getOrDefault(self.negBaggingFraction)
    
    
    def getNumBatches(self):
        """
        Returns:
            numBatches: If greater than 0, splits data into separate batches during training
        """
        return self.getOrDefault(self.numBatches)
    
    
    def getNumIterations(self):
        """
        Returns:
            numIterations: Number of iterations, LightGBM constructs num_class * num_iterations trees
        """
        return self.getOrDefault(self.numIterations)
    
    
    def getNumLeaves(self):
        """
        Returns:
            numLeaves: Number of leaves
        """
        return self.getOrDefault(self.numLeaves)
    
    
    def getNumTasks(self):
        """
        Returns:
            numTasks: Advanced parameter to specify the number of tasks.  SynapseML tries to guess this based on cluster configuration, but this parameter can be used to override.
        """
        return self.getOrDefault(self.numTasks)
    
    
    def getNumThreads(self):
        """
        Returns:
            numThreads: Number of threads per executor for LightGBM. For the best speed, set this to the number of real CPU cores.
        """
        return self.getOrDefault(self.numThreads)
    
    
    def getObjective(self):
        """
        Returns:
            objective: The Objective. For regression applications, this can be: regression_l2, regression_l1, huber, fair, poisson, quantile, mape, gamma or tweedie. For classification applications, this can be: binary, multiclass, or multiclassova. 
        """
        return self.getOrDefault(self.objective)
    
    
    def getObjectiveSeed(self):
        """
        Returns:
            objectiveSeed: Random seed for objectives, if random process is needed.  Currently used only for rank_xendcg objective.
        """
        return self.getOrDefault(self.objectiveSeed)
    
    
    def getOtherRate(self):
        """
        Returns:
            otherRate: The retain ratio of small gradient data. Only used in goss.
        """
        return self.getOrDefault(self.otherRate)
    
    
    def getParallelism(self):
        """
        Returns:
            parallelism: Tree learner parallelism, can be set to data_parallel or voting_parallel
        """
        return self.getOrDefault(self.parallelism)
    
    
    def getPassThroughArgs(self):
        """
        Returns:
            passThroughArgs: Direct string to pass through to LightGBM library (appended with other explicitly set params). Will override any parameters given with explicit setters. Can include multiple parameters in one string. e.g., force_row_wise=true
        """
        return self.getOrDefault(self.passThroughArgs)
    
    
    def getPosBaggingFraction(self):
        """
        Returns:
            posBaggingFraction: Positive Bagging fraction
        """
        return self.getOrDefault(self.posBaggingFraction)
    
    
    def getPredictDisableShapeCheck(self):
        """
        Returns:
            predictDisableShapeCheck: control whether or not LightGBM raises an error when you try to predict on data with a different number of features than the training data
        """
        return self.getOrDefault(self.predictDisableShapeCheck)
    
    
    def getPredictionCol(self):
        """
        Returns:
            predictionCol: prediction column name
        """
        return self.getOrDefault(self.predictionCol)
    
    
    def getReferenceDataset(self):
        """
        Returns:
            referenceDataset: The reference Dataset that was used for the fit. If using samplingMode=custom, this must be set before fit().
        """
        return self.getOrDefault(self.referenceDataset)
    
    
    def getRepartitionByGroupingColumn(self):
        """
        Returns:
            repartitionByGroupingColumn: Repartition training data according to grouping column, on by default.
        """
        return self.getOrDefault(self.repartitionByGroupingColumn)
    
    
    def getSamplingMode(self):
        """
        Returns:
            samplingMode: Data sampling for streaming mode. Sampled data is used to define bins. 'global': sample from all data, 'subset': sample from first N rows, or 'fixed': Take first N rows as sample.Values can be global, subset, or fixed. Default is subset.
        """
        return self.getOrDefault(self.samplingMode)
    
    
    def getSamplingSubsetSize(self):
        """
        Returns:
            samplingSubsetSize: Specify subset size N for the sampling mode 'subset'. 'binSampleCount' rows will be chosen from the first N values of the dataset. Subset can be used when rows are expected to be random and data is huge.
        """
        return self.getOrDefault(self.samplingSubsetSize)
    
    
    def getSeed(self):
        """
        Returns:
            seed: Main seed, used to generate other seeds
        """
        return self.getOrDefault(self.seed)
    
    
    def getSkipDrop(self):
        """
        Returns:
            skipDrop: Probability of skipping the dropout procedure during a boosting iteration
        """
        return self.getOrDefault(self.skipDrop)
    
    
    def getSlotNames(self):
        """
        Returns:
            slotNames: List of slot names in the features column
        """
        return self.getOrDefault(self.slotNames)
    
    
    def getTimeout(self):
        """
        Returns:
            timeout: Timeout in seconds
        """
        return self.getOrDefault(self.timeout)
    
    
    def getTopK(self):
        """
        Returns:
            topK: The top_k value used in Voting parallel, set this to larger value for more accurate result, but it will slow down the training speed. It should be greater than 0
        """
        return self.getOrDefault(self.topK)
    
    
    def getTopRate(self):
        """
        Returns:
            topRate: The retain ratio of large gradient data. Only used in goss.
        """
        return self.getOrDefault(self.topRate)
    
    
    def getUniformDrop(self):
        """
        Returns:
            uniformDrop: Set this to true to use uniform drop in dart mode
        """
        return self.getOrDefault(self.uniformDrop)
    
    
    def getUseBarrierExecutionMode(self):
        """
        Returns:
            useBarrierExecutionMode: Barrier execution mode which uses a barrier stage, off by default.
        """
        return self.getOrDefault(self.useBarrierExecutionMode)
    
    
    def getUseMissing(self):
        """
        Returns:
            useMissing: Set this to false to disable the special handle of missing value
        """
        return self.getOrDefault(self.useMissing)
    
    
    def getUseSingleDatasetMode(self):
        """
        Returns:
            useSingleDatasetMode: Use single dataset execution mode to create a single native dataset per executor (singleton) to reduce memory and communication overhead.
        """
        return self.getOrDefault(self.useSingleDatasetMode)
    
    
    def getValidationIndicatorCol(self):
        """
        Returns:
            validationIndicatorCol: Indicates whether the row is for training or validation
        """
        return self.getOrDefault(self.validationIndicatorCol)
    
    
    def getVerbosity(self):
        """
        Returns:
            verbosity: Verbosity where lt 0 is Fatal, eq 0 is Error, eq 1 is Info, gt 1 is Debug
        """
        return self.getOrDefault(self.verbosity)
    
    
    def getWeightCol(self):
        """
        Returns:
            weightCol: The name of the weight column
        """
        return self.getOrDefault(self.weightCol)
    
    
    def getXGBoostDartMode(self):
        """
        Returns:
            xGBoostDartMode: Set this to true to use xgboost dart mode
        """
        return self.getOrDefault(self.xGBoostDartMode)
    
    
    def getZeroAsMissing(self):
        """
        Returns:
            zeroAsMissing: Set to true to treat all zero as missing values (including the unshown values in LibSVM / sparse matrices). Set to false to use na for representing missing values
        """
        return self.getOrDefault(self.zeroAsMissing)

    def _create_model(self, java_model):
        try:
            model = LightGBMRankerModel(java_obj=java_model)
            model._transfer_params_from_java()
        except TypeError:
            model = LightGBMRankerModel._from_java(java_model)
        return model
    
    def _fit(self, dataset):
        java_model = self._fit_java(dataset)
        return self._create_model(java_model)

    
        