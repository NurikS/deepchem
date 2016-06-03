"""
Testing reload.
"""
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

__author__ = "Bharath Ramsundar"
__copyright__ = "Copyright 2016, Stanford University"
__license__ = "GPL"

import os
import shutil
import tempfile
import numpy as np
from sklearn.linear_model import LogisticRegression
from deepchem.models.tests import TestAPI
from deepchem.utils.save import load_from_disk
from deepchem.datasets import Dataset
from deepchem.featurizers.featurize import DataFeaturizer
from deepchem.featurizers.fingerprints import CircularFingerprint
from deepchem.splits import ScaffoldSplitter
from deepchem.datasets import Dataset
from deepchem.transformers import BalancingTransformer
from deepchem.hyperparameters import HyperparamOpt
from deepchem.models.multitask import SingletaskToMultitask
from deepchem import metrics
from deepchem.metrics import Metric
from deepchem.models.sklearn_models import SklearnModel
from deepchem.utils.evaluate import relative_difference

class TestReload(TestAPI):
  """
  Test reload for datasets.
  """
  def _run_muv_experiment(self, dataset_file, reload=False, verbosity=None):
    """Loads or reloads a small version of MUV dataset."""
    # Load MUV dataset
    raw_dataset = load_from_disk(dataset_file)
    print("Number of examples in dataset: %s" % str(raw_dataset.shape[0]))

    print("About to featurize compounds")
    featurizers = [CircularFingerprint(size=1024)]
    MUV_tasks = ['MUV-692', 'MUV-689', 'MUV-846', 'MUV-859', 'MUV-644',
                 'MUV-548', 'MUV-852', 'MUV-600', 'MUV-810', 'MUV-712',
                 'MUV-737', 'MUV-858', 'MUV-713', 'MUV-733', 'MUV-652',
                 'MUV-466', 'MUV-832']
    featurizer = DataFeaturizer(tasks=MUV_tasks,
                                smiles_field="smiles",
                                featurizers=featurizers,
                                verbosity=verbosity)
    dataset = featurizer.featurize(dataset_file, self.data_dir)
    assert len(dataset) == len(raw_dataset)

    print("About to split compounds into train/valid/test")
    splitter = ScaffoldSplitter(verbosity=verbosity)
    frac_train, frac_valid, frac_test = .8, .1, .1
    train_dataset, valid_dataset, test_dataset = \
        splitter.train_valid_test_split(
            dataset, self.train_dir, self.valid_dir, self.test_dir,
            log_every_n=1000, frac_train=frac_train,
            frac_test=frac_test, frac_valid=frac_valid)
    # Do an approximate comparison since splits are sometimes slightly off from
    # the exact fraction.
    assert relative_difference(
        len(train_dataset), frac_train * len(dataset)) < 1e-3
    assert relative_difference(
        len(valid_dataset), frac_valid * len(dataset)) < 1e-3
    assert relative_difference(
        len(test_dataset), frac_test * len(dataset)) < 1e-3

    # TODO(rbharath): Transformers don't play nice with reload! Namely,
    # reloading will cause the transform to be reapplied. This is undesirable in
    # almost all cases. Need to understand a method to fix this.
    ##################################### DEBUG
    
    print("_run_muv_experiment()")
    print("train_dataset.get_labels()")
    print(train_dataset.get_labels())
    print("train_dataset.get_weights()")
    print(train_dataset.get_weights())
    ##################################### DEBUG
    transformers = [
        BalancingTransformer(transform_w=True, dataset=train_dataset)]
    print("Transforming datasets")
    for dataset in [train_dataset, valid_dataset, test_dataset]:
      for transformer in transformers:
          transformer.transform(dataset)

    return (len(train_dataset), len(valid_dataset), len(test_dataset))
    
  def test_reload_after_gen(self):
    """Check num samples for loaded and reloaded datasets is equal."""
    reload = False 
    verbosity = None
    current_dir = os.path.dirname(os.path.abspath(__file__))
    dataset_file = os.path.join(
        current_dir, "../../../datasets/mini_muv.csv.gz")
    print("Running experiment for first time without reload.")
    (len_train, len_valid, len_test) = self._run_muv_experiment(
        dataset_file, reload, verbosity)

    print("Running experiment for second time with reload.")
    reload = True 
    (len_reload_train, len_reload_valid, len_reload_test) = (
        self._run_muv_experiment(dataset_file, reload, verbosity))
    assert len_train == len_reload_train
    assert len_valid == len_reload_valid
    assert len_test == len_reload_valid

  def test_reload_twice(self):
    """Check ability to repeatedly run experiments with reload set True."""
    reload = True 
    verbosity = "high"
    current_dir = os.path.dirname(os.path.abspath(__file__))
    dataset_file = os.path.join(
        current_dir, "../../../datasets/mini_muv.csv.gz")
    print("Running experiment for first time with reload.")
    (len_train, len_valid, len_test) = self._run_muv_experiment(
        dataset_file, reload, verbosity)

    print("Running experiment for second time with reload.")
    (len_reload_train, len_reload_valid, len_reload_test) = (
        self._run_muv_experiment(dataset_file, reload, verbosity))
    assert len_train == len_reload_train
    assert len_valid == len_reload_valid
    assert len_test == len_reload_valid
