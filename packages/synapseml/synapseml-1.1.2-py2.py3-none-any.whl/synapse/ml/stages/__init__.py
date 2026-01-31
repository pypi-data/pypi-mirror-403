# Copyright (C) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See LICENSE in project root for information.


"""
SynapseML is an ecosystem of tools aimed towards expanding the distributed computing framework
Apache Spark in several new directions. SynapseML adds many deep learning and data science tools to the Spark
ecosystem, including seamless integration of Spark Machine Learning pipelines with
Microsoft Cognitive Toolkit (CNTK), LightGBM and OpenCV. These tools enable powerful and
highly-scalable predictive and analytical models for a variety of datasources.

SynapseML also brings new networking capabilities to the Spark Ecosystem. With the HTTP on Spark project,
users can embed any web service into their SparkML models. In this vein, SynapseML provides easy to use SparkML
transformers for a wide variety of Microsoft Cognitive Services. For production grade deployment,
the Spark Serving project enables high throughput, sub-millisecond latency web services,
backed by your Spark cluster.

SynapseML requires Scala 2.12, Spark 3.0+, and Python 3.6+.
"""

__version__ = "1.1.2"
__spark_package_version__ = "1.1.2"

from synapse.ml.stages.Cacher import *
from synapse.ml.stages.ClassBalancer import *
from synapse.ml.stages.ClassBalancerModel import *
from synapse.ml.stages.DropColumns import *
from synapse.ml.stages.DynamicMiniBatchTransformer import *
from synapse.ml.stages.EnsembleByKey import *
from synapse.ml.stages.Explode import *
from synapse.ml.stages.FixedMiniBatchTransformer import *
from synapse.ml.stages.FlattenBatch import *
from synapse.ml.stages.Lambda import *
from synapse.ml.stages.MultiColumnAdapter import *
from synapse.ml.stages.PartitionConsolidator import *
from synapse.ml.stages.RenameColumn import *
from synapse.ml.stages.Repartition import *
from synapse.ml.stages.SelectColumns import *
from synapse.ml.stages.StratifiedRepartition import *
from synapse.ml.stages.SummarizeData import *
from synapse.ml.stages.TextPreprocessor import *
from synapse.ml.stages.TimeIntervalMiniBatchTransformer import *
from synapse.ml.stages.Timer import *
from synapse.ml.stages.TimerModel import *
from synapse.ml.stages.UDFTransformer import *
from synapse.ml.stages.UnicodeNormalize import *

