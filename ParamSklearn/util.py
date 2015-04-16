import importlib
import inspect
import os
import pkgutil
import unittest

import numpy as np
import scipy.sparse
import sklearn
import sklearn.base
import sklearn.datasets


SPARSE = 'SPARSE'
DENSE = 'DENSE'
PREDICTIONS = 'PREDICTIONS'
INPUT = 'INPUT'


def find_sklearn_classes(class_):
    classifiers = set()
    all_subdirectories = []
    sklearn_path = sklearn.__path__[0]
    for root, dirs, files in os.walk(sklearn_path):
        all_subdirectories.append(root)

    for module_loader, module_name, ispkg in \
            pkgutil.iter_modules(all_subdirectories):

        # Work around some issues...
        if module_name in ["hmm", "mixture"]:
            print "Skipping %s" % module_name
            continue

        module_file = module_loader.__dict__["path"]
        sklearn_module = module_file.replace(sklearn_path, "").replace("/", ".")
        full_module_name = "sklearn" + sklearn_module + "." + module_name

        pkg = importlib.import_module(full_module_name)

        for member_name, obj in inspect.getmembers(pkg):
            if inspect.isclass(obj) and \
                    issubclass(obj, class_):
                classifier = obj
                # print member_name, obj
                classifiers.add(classifier)

    print
    print classifiers


def get_dataset(dataset='iris', make_sparse=False, add_NaNs=False):
    iris = getattr(sklearn.datasets, "load_%s" % dataset)()
    X = iris.data.astype(np.float32)
    Y = iris.target
    rs = np.random.RandomState(42)
    indices = np.arange(X.shape[0])
    train_size = min(int(len(indices) / 3. * 2.), 150)
    rs.shuffle(indices)
    X = X[indices]
    Y = Y[indices]
    X_train = X[:train_size]
    Y_train = Y[:train_size]
    X_test = X[train_size:]
    Y_test = Y[train_size:]

    if add_NaNs:
        mask = np.random.choice([True, False], size=(X_train.shape))
        X_train[mask] = np.NaN

    if make_sparse:
        X_train[:,0] = 0
        X_train[np.random.random(X_train.shape) > 0.5] = 0
        X_train = scipy.sparse.csc_matrix(X_train)
        X_train.eliminate_zeros()
        X_test[:,0] = 0
        X_test[np.random.random(X_test.shape) > 0.5] = 0
        X_test = scipy.sparse.csc_matrix(X_test)
        X_test.eliminate_zeros()

    return X_train, Y_train, X_test, Y_test


def _test_classifier(classifier, dataset='iris'):
    X_train, Y_train, X_test, Y_test = get_dataset(dataset=dataset,
                                                   make_sparse=False)
    configuration_space = classifier.get_hyperparameter_search_space()
    default = configuration_space.get_default_configuration()
    classifier = classifier(random_state=1,
                            **{hp.hyperparameter.name: hp.value for hp in
                             default.values.values()})
    predictor = classifier.fit(X_train, Y_train)
    predictions = predictor.predict(X_test)
    return predictions, Y_test


def _test_classifier_predict_proba(classifier, dataset='iris'):
    X_train, Y_train, X_test, Y_test = get_dataset(dataset=dataset,
                                                   make_sparse=False)
    configuration_space = classifier.get_hyperparameter_search_space()
    default = configuration_space.get_default_configuration()
    classifier = classifier(random_state=1,
                            **{hp.hyperparameter.name: hp.value for hp in
                               default.values.values()})
    predictor = classifier.fit(X_train, Y_train)
    predictions = predictor.predict_proba(X_test)
    return predictions, Y_test


def _test_preprocessing(Preprocessor, dataset='iris', make_sparse=False):
    X_train, Y_train, X_test, Y_test = get_dataset(dataset=dataset,
                                                   make_sparse=make_sparse)
    original_X_train = X_train.copy()
    configuration_space = Preprocessor.get_hyperparameter_search_space()
    default = configuration_space.get_default_configuration()
    preprocessor = Preprocessor(random_state=1,
                                **{hp.hyperparameter.name: hp.value for hp in
                                default.values.values()})

    transformer = preprocessor.fit(X_train, Y_train)
    return transformer.transform(X_train), original_X_train


class PreprocessingTestCase(unittest.TestCase):
    def _test_preprocessing_dtype(self, Preprocessor, add_NaNs=False):
        # Dense
        # np.float32
        X_train, Y_train, X_test, Y_test = get_dataset("iris", add_NaNs=add_NaNs)
        self.assertEqual(X_train.dtype, np.float32)

        configuration_space = Preprocessor.get_hyperparameter_search_space()
        default = configuration_space.get_default_configuration()
        preprocessor = Preprocessor(random_state=1,
                                    **{hp.hyperparameter.name: hp.value for hp in
                                       default.values.values()})
        preprocessor.fit(X_train, Y_train)
        Xt = preprocessor.transform(X_train)
        self.assertEqual(Xt.dtype, np.float32)

        # np.float64
        X_train, Y_train, X_test, Y_test = get_dataset("iris", add_NaNs=add_NaNs)
        X_train = X_train.astype(np.float64)
        configuration_space = Preprocessor.get_hyperparameter_search_space()
        default = configuration_space.get_default_configuration()
        preprocessor = Preprocessor(random_state=1,
                                    **{hp.hyperparameter.name: hp.value for hp in
                                       default.values.values()})
        preprocessor.fit(X_train, Y_train)
        Xt = preprocessor.transform(X_train)
        self.assertEqual(Xt.dtype, np.float64)

        # Sparse
        # np.float32
        X_train, Y_train, X_test, Y_test = get_dataset("iris", make_sparse=True,
                                                       add_NaNs=add_NaNs)
        self.assertEqual(X_train.dtype, np.float32)
        configuration_space = Preprocessor.get_hyperparameter_search_space()
        default = configuration_space.get_default_configuration()
        preprocessor = Preprocessor(random_state=1,
                                    **{hp.hyperparameter.name: hp.value for hp in
                                       default.values.values()})
        preprocessor.fit(X_train, Y_train)
        Xt = preprocessor.transform(X_train)
        self.assertEqual(Xt.dtype, np.float32)

        # np.float64
        X_train, Y_train, X_test, Y_test = get_dataset("iris", make_sparse=True,
                                                       add_NaNs=add_NaNs)
        X_train = X_train.astype(np.float64)
        configuration_space = Preprocessor.get_hyperparameter_search_space()
        default = configuration_space.get_default_configuration()
        preprocessor = Preprocessor(random_state=1,
                                    **{hp.hyperparameter.name: hp.value for hp in
                                       default.values.values()})
        preprocessor.fit(X_train)
        Xt = preprocessor.transform(X_train)
        self.assertEqual(Xt.dtype, np.float64)


def _test_regressor(Regressor, dataset='diabetes'):
    X_train, Y_train, X_test, Y_test = get_dataset(dataset=dataset,
                                                   make_sparse=False)
    configuration_space = Regressor.get_hyperparameter_search_space()
    default = configuration_space.get_default_configuration()
    regressor = Regressor(random_state=1,
                          **{hp.hyperparameter.name: hp.value for hp in
                          default.values.values()})
    # Dumb incomplete hacky test to check that we do not alter the data
    X_train_hash = hash(str(X_train))
    X_test_hash = hash(str(X_test))
    Y_train_hash = hash(str(Y_train))
    predictor = regressor.fit(X_train, Y_train)
    predictions = predictor.predict(X_test)
    if X_train_hash != hash(str(X_train)) or \
                    X_test_hash != hash(str(X_test)) or \
                    Y_train_hash != hash(str(Y_train)):
        raise ValueError("Model modified data")
    return predictions, Y_test


if __name__ == "__main__":
    find_sklearn_classes(sklearn.base.ClassifierMixin)
    find_sklearn_classes(sklearn.base.RegressorMixin)
    find_sklearn_classes(sklearn.base.TransformerMixin)
