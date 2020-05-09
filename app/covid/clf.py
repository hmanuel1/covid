"""Run the following classification models:
    1) Random Trees and Logistic Regression
    2) Random Forest and Logistic Regression
    3) Gradient Boosting Trees
    4) Gradient Boosting Trees and Logistic Regression
    5) Random Forest
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import (
    RandomTreesEmbedding,
    RandomForestClassifier,
    GradientBoostingClassifier
)
from sklearn.preprocessing import OneHotEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_curve
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn import metrics

from database import DataBase
from sql import FLDEM_VIEW_TABLE


# outputs
MODELS_ROC_TABLE = 'models_roc'
IMPORTANCE_TABLE = 'importance'


np.random.seed(10)

def rt_log_reg(X_train, X_test, y_train, y_test, n_estimators):
    """Random Trees and Logistic Reqression classifier

    Arguments:
        X_train {array} -- training set for independent variables
        X_test {array} -- testing set for independent variables
        y_train {array} -- training set for dependent variable
        y_test {array} -- testing set for dependent variable
        n_estimators {integer} -- [description]

    Returns:
        dict -- model's roc[false pos rate, true pos rate], auc and logloss
    """
    # Unsupervised transformation based on totally random trees
    clf_rt = RandomTreesEmbedding(max_depth=3, n_estimators=n_estimators,
                                  random_state=0)

    clf_lm = LogisticRegression(max_iter=1000, solver='lbfgs')

    # fit model
    pipeline = make_pipeline(clf_rt, clf_lm)
    pipeline.fit(X_train, y_train)

    # predict
    y_pred = pipeline.predict_proba(X_test)[:, 1]

    # model metrics
    fpr, tpr, _ = roc_curve(y_test, y_pred)
    auc = roc_auc_score(y_test, y_pred)
    logloss = metrics.log_loss(y_test, y_pred)

    return dict(fpr=fpr, tpr=tpr, auc=auc, logloss=logloss)


def rf_log_reg(X_train, X_test, y_train, y_test, n_estimators):
    """
       Random Forest and Logistic Regression classifier

    Arguments:
        X_train {array} -- training set for independent variables
        X_test {array} -- testing set for independent variables
        y_train {array} -- training set for dependent variable
        y_test {array} -- testing set for dependent variable
        n_estimators {integer} -- [description]

    Returns:
        dict -- model's roc[false pos rate, true pos rate], auc and logloss
    """
    # Unsupervised transformation based on totally random trees
    clf_rf = RandomForestClassifier(max_depth=3, n_estimators=n_estimators)
    rf_enc = OneHotEncoder(categories='auto')
    clf_lm = LogisticRegression(max_iter=1000, solver='lbfgs')

    clf_rf.fit(X_train, y_train)
    rf_enc.fit(clf_rf.apply(X_train))
    clf_lm.fit(rf_enc.transform(clf_rf.apply(X_train)), y_train)

    # predict
    y_pred = clf_lm.predict_proba(rf_enc.transform(clf_rf.apply(X_test)))[:, 1]

    # model metrics
    fpr, tpr, _ = roc_curve(y_test, y_pred)
    auc = roc_auc_score(y_test, y_pred)
    logloss = metrics.log_loss(y_test, y_pred)

    return dict(fpr=fpr, tpr=tpr, auc=auc, logloss=logloss)


def gbt_log_reg(X_train, X_test, y_train, y_test, n_estimators):
    """
       Gradient Boosting Trees and Logistic Regression classifier

    Arguments:
        X_train {array} -- training set for independent variables
        X_test {array} -- testing set for independent variables
        y_train {array} -- training set for dependent variable
        y_test {array} -- testing set for dependent variable
        n_estimators {integer} -- [description]

    Returns:
        dict -- model's roc[false pos rate, true pos rate], auc and logloss
    """
    # Supervised transformation based on gradient boosted trees
    clf_grd = GradientBoostingClassifier(n_estimators=n_estimators)
    grd_enc = OneHotEncoder(categories='auto')
    clf_lm = LogisticRegression(max_iter=1000, solver='lbfgs')

    clf_grd.fit(X_train, y_train)
    grd_enc.fit(clf_grd.apply(X_train)[:, :, 0])
    clf_lm.fit(grd_enc.transform(clf_grd.apply(X_train)[:, :, 0]), y_train)

    # prediction
    y_pred = clf_lm.predict_proba(grd_enc.transform(clf_grd.apply(X_test)[:, :, 0]))[:, 1]

    # model metrics
    fpr, tpr, _ = roc_curve(y_test, y_pred)
    auc = roc_auc_score(y_test, y_pred)
    logloss = metrics.log_loss(y_test, y_pred)

    return dict(fpr=fpr, tpr=tpr, auc=auc, logloss=logloss)


def grd_boosting_trees(X_train, X_test, y_train, y_test, n_estimators):
    """
       Gradient Boosting Trees classifier

    Arguments:
        X_train {array} -- training set for independent variables
        X_test {array} -- testing set for independent variables
        y_train {array} -- training set for dependent variable
        y_test {array} -- testing set for dependent variable
        n_estimators {integer} -- [description]

    Returns:
        dict -- model's roc[false pos rate, true pos rate], auc and logloss
    """
    # Supervised transformation based on gradient boosted trees
    clf_grd = GradientBoostingClassifier(n_estimators=n_estimators)
    grd_enc = OneHotEncoder(categories='auto')

    # fit model
    clf_grd.fit(X_train, y_train)
    grd_enc.fit(clf_grd.apply(X_train)[:, :, 0])

    # predict
    y_pred = clf_grd.predict_proba(X_test)[:, 1]

    # model metrics
    fpr, tpr, _ = roc_curve(y_test, y_pred)
    auc = roc_auc_score(y_test, y_pred)
    logloss = metrics.log_loss(y_test, y_pred)

    return dict(fpr=fpr, tpr=tpr, auc=auc, logloss=logloss)


def random_forest(X_train, X_test, y_train, y_test, n_estimators):
    """
       Random Forest classifier

    Arguments:
        X_train {array} -- training set for independent variables
        X_test {array} -- testing set for independent variables
        y_train {array} -- training set for dependent variable
        y_test {array} -- testing set for dependent variable
        n_estimators {integer} -- [description]

    Returns:
        dict -- model's roc[false pos rate, true pos rate], auc and logloss
    """
    # Unsupervised transformation based on totally random trees
    clf_rf = RandomForestClassifier(max_depth=3, n_estimators=n_estimators)
    rf_enc = OneHotEncoder(categories='auto')

    # fit
    clf_rf.fit(X_train, y_train)
    rf_enc.fit(clf_rf.apply(X_train))

    # predict
    y_pred = clf_rf.predict_proba(X_test)[:, 1]

    # model metrics
    fpr, tpr, _ = roc_curve(y_test, y_pred)
    auc = roc_auc_score(y_test, y_pred)
    logloss = metrics.log_loss(y_test, y_pred)

    return dict(fpr=fpr, tpr=tpr, auc=auc, logloss=logloss)


def feature_importance(X_train, y_train, col_names, n_estimators):
    """
        Feature importance using Random Forest classifier

    Arguments:
        X_train {array} -- training set for independent variables
        X_test {array} -- testing set for independent variables
        y_train {array} -- training set for dependent variable
        y_test {array} -- testing set for dependent variable
        n_estimators {integer} -- [description]

    Returns:
        dict -- model's roc[false pos rate, true pos rate], auc and logloss
    """
    # Unsupervised transformation based on totally random trees
    clf_rf = RandomForestClassifier(max_depth=3, n_estimators=n_estimators)

    # fit
    clf_rf.fit(X_train, y_train)

    # feature importance
    data = pd.DataFrame({'feature': col_names,
                         'importance': clf_rf.feature_importances_})

    data.sort_values('importance', ascending=False, inplace=True)
    return data


def classify():
    """Run classification models:
        1) Random Trees and Logistic Regression
        2) Random Forest and Logistic Regression
        3) Gradient Boosting Trees
        4) Gradient Boosting Trees and Logistic Regression
        5) Random Forest

    Input from database:
        FDEM_VIEW_TABLE {database table} -- fldem cleaned data

    Output to database:
        MODELS_ROC_TABLE {database table} -- models' ROC, LogLoss and AUC
        IMPORTANCE_TABLE {database table } -- random forest feature importances
    """
    y_var = 'died'
    n_estimators = 10

    # get fldem from database
    _db = DataBase()
    cols = ['died', 'age', 'population', 'land_area', 'water_area', 'gender',
            'density']

    data = _db.get_table(FLDEM_VIEW_TABLE, columns=cols)
    data.dropna(inplace=True)
    _db.close()

    # divide data set
    X = data.loc[:, data.columns != y_var]
    y = data.loc[:, data.columns == y_var]
    X_train, X_test, y_train, y_test = train_test_split(X.values,
                                                        y.values.ravel(),
                                                        test_size=0.5)
    # classification models
    models = dict(
        rt_lr=dict(model='RT + LR',
                   **rt_log_reg(X_train, X_test, y_train, y_test, n_estimators)),

        rf_lr=dict(model='RF + LR',
                   **rf_log_reg(X_train, X_test, y_train, y_test, n_estimators)),

        rforest=dict(model='RF',
                     **random_forest(X_train, X_test, y_train, y_test, n_estimators)),

        gbt=dict(model='GBT',
                 **grd_boosting_trees(X_train, X_test, y_train, y_test, n_estimators)),

        gbt_lr=dict(model='GBT + LR',
                    **gbt_log_reg(X_train, X_test, y_train, y_test, n_estimators)),

        rand=dict(model='Random', logloss=-1 * np.log10(0.5), auc=0.5,
                  fpr=np.linspace(0, 1, 100), tpr=np.linspace(0, 1, 100)))

    # conbine result of all models
    data = pd.concat([pd.DataFrame(models['rt_lr']), pd.DataFrame(models['rf_lr']),
                      pd.DataFrame(models['gbt']), pd.DataFrame(models['rforest']),
                      pd.DataFrame(models['gbt_lr']), pd.DataFrame(models['rand'])],
                     axis=0, ignore_index=True)

    data = data.round(4)

    # output to database
    _db = DataBase()
    _db.add_table(MODELS_ROC_TABLE, data, index=False)
    _db.close()

    # output feature importance
    data = feature_importance(X_train, y_train, list(X.columns), n_estimators)

    # output to database
    _db = DataBase()
    _db.add_table(IMPORTANCE_TABLE, data, index=False)
    _db.close()


def utest_models():
    """Plot model results
    """
    _db = DataBase()
    data = _db.get_table(MODELS_ROC_TABLE)
    _db.close()

    plt.figure(1)

    for cat in data['model'].unique():
        xdata = data[data['model'] == cat]['fpr']
        ydata = data[data['model'] == cat]['tpr']
        if cat == 'Random':
            plt.plot(xdata, ydata, color='black', linestyle='--', label=cat)
        else:
            plt.plot(xdata, ydata, label=cat)

    plt.xlabel('False positive rate')
    plt.ylabel('True positive rate')
    plt.title('ROC curve')
    plt.legend(loc='best')
    plt.show()


def utest_feature_importance():
    """Plot feature importance
    """
    _db = DataBase()
    data = _db.get_table(IMPORTANCE_TABLE)
    _db.close()

    plt.figure(figsize=(4, 4))
    ax = plt.subplot(111)
    ax.barh(data['feature'], data['importance'])
    plt.gca().invert_yaxis()
    ax.set_ylabel('features')
    plt.title('Feature Importance')
    plt.show()


if __name__ == "__main__":

    # unit testing
    classify()

    # plot model results
    utest_models()

    # plot feature importances
    utest_feature_importance()
