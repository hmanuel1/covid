"""
    Run the following classification models:
     1) Random Trees and Logistic Regression
     2) Random Forest and Logistic Regression
     3) Gradient Boosting Trees
     4) Gradient Boosting Trees and Logistic Regression
     5) Random Forest
"""

from os.path import join

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import (RandomTreesEmbedding, RandomForestClassifier,
                              GradientBoostingClassifier)
from sklearn.preprocessing import OneHotEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_curve
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn import metrics

from utilities import cwd


np.random.seed(10)


def rt_log_reg(X_train, X_test, y_train, y_test, n_estimators):
    """
       Random Trees and Logistic Regression classifier
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
    roc_fpr, roc_tpr, _ = roc_curve(y_test, y_pred)
    roc_auc = roc_auc_score(y_test, y_pred)
    logloss = metrics.log_loss(y_test, y_pred)

    return dict(x=roc_fpr, y=roc_tpr, auc=roc_auc, logloss=logloss)


def rf_log_reg(X_train, X_test, y_train, y_test, n_estimators):
    """
       Random Forest and Logistic Regression classifier
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
    roc_fpr, roc_tpr, _ = roc_curve(y_test, y_pred)
    roc_auc = roc_auc_score(y_test, y_pred)
    logloss = metrics.log_loss(y_test, y_pred)

    return dict(x=roc_fpr, y=roc_tpr, auc=roc_auc, logloss=logloss)


def gbt_log_reg(X_train, X_test, y_train, y_test, n_estimators):
    """
       Gradient Boosting Trees and Logistic Regression classifier
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
    roc_fpr, roc_tpr, _ = roc_curve(y_test, y_pred)
    roc_auc = roc_auc_score(y_test, y_pred)
    logloss = metrics.log_loss(y_test, y_pred)

    return dict(x=roc_fpr, y=roc_tpr, auc=roc_auc, logloss=logloss)


def grd_boosting_trees(X_train, X_test, y_train, y_test, n_estimators):
    """
       Gradient Boosting Trees classifier
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
    roc_fpr, roc_tpr, _ = roc_curve(y_test, y_pred)
    roc_auc = roc_auc_score(y_test, y_pred)
    logloss = metrics.log_loss(y_test, y_pred)

    return dict(x=roc_fpr, y=roc_tpr, auc=roc_auc, logloss=logloss)


def random_forest(X_train, X_test, y_train, y_test, n_estimators):
    """
       Random Forest classifier
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
    roc_fpr, roc_tpr, _ = roc_curve(y_test, y_pred)
    roc_auc = roc_auc_score(y_test, y_pred)
    logloss = metrics.log_loss(y_test, y_pred)

    return dict(x=roc_fpr, y=roc_tpr, auc=roc_auc, logloss=logloss)


def feature_importance(X_train, y_train, col_names, n_estimators):
    """
        Feature importance using Random Forest classifier
    """

    # Unsupervised transformation based on totally random trees
    clf_rf = RandomForestClassifier(max_depth=3, n_estimators=n_estimators)

    # fit
    clf_rf.fit(X_train, y_train)

    # feature importances
    df = pd.DataFrame({'feature': col_names,
                       'importance': clf_rf.feature_importances_})

    df.sort_values('importance', ascending=False, inplace=True)
    return df


def classify():
    """
        Run classification models
    """

    y_var = 'died'
    n_estimators = 10

    df = pd.read_csv(join(cwd(), 'data', 'flclean.csv'), low_memory=False)
    df.drop(['datetime', 'fips', 'dx', 'dy'], axis=1, inplace=True)
    df.rename(columns={'Male': 'gender', 'land_sqkm': 'landsqkm',
                       'water_sqkm': 'watersqkm'}, inplace=True)
    df.dropna(inplace=True)

    # divide data set
    X = df.loc[:, df.columns != y_var]
    y = df.loc[:, df.columns == y_var]
    X_train, X_test, y_train, y_test = train_test_split(X.values,
                                                        y.values.ravel(),
                                                        test_size=0.5)
    # classification models
    rt_lr = dict(model='Random Trees and Logistic Regression', abbrev='RT + LR',
                 **rt_log_reg(X_train, X_test, y_train, y_test, n_estimators))

    rf_lr = dict(model='Random Forest and Logistic Regression', abbrev='RF + LR',
                 **rf_log_reg(X_train, X_test, y_train, y_test, n_estimators))

    rforest = dict(model='Random Forest', abbrev='RF',
                   **random_forest(X_train, X_test, y_train, y_test, n_estimators))

    gbt = dict(model='Gradient Boosting Trees', abbrev='GBT',
               **grd_boosting_trees(X_train, X_test, y_train, y_test, n_estimators))

    gbt_lr = dict(model='Gradient Boosting Trees and Linear Regression',
                  abbrev='GBT + LR',
                  **gbt_log_reg(X_train, X_test, y_train, y_test, n_estimators))

    rand = dict(model='Random', abbrev='Random', logloss=-1 * np.log10(0.5),
                auc=0.5, x=np.linspace(0, 1, 100), y=np.linspace(0, 1, 100))

    # conbine result of all models
    df = pd.concat([pd.DataFrame(rt_lr), pd.DataFrame(rf_lr), pd.DataFrame(gbt),
                    pd.DataFrame(rforest), pd.DataFrame(gbt_lr), pd.DataFrame(rand)],
                   axis=0, ignore_index=True)

    df = df.rename(columns={'x': 'False_Positive_Rate',
                            'y': 'True_Positive_Rate'})

    # output models metrics
    df.to_csv(join(cwd(), 'output', 'fl_roc_models.csv'), index=False)

    # output feature importance
    df = feature_importance(X_train, y_train, list(X.columns), n_estimators)
    df.to_csv(join(cwd(), 'output', 'fl_fi_models.csv'), index=False)


def utest_models():
    """
        Plot model results
    """

    data = pd.read_csv(join(cwd(), 'output', 'fl_roc_models.csv'))
    plt.figure(1)

    for cat in data['abbrev'].unique():
        xdata = data[data['abbrev'] == cat]['False_Positive_Rate']
        ydata = data[data['abbrev'] == cat]['True_Positive_Rate']
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
    """
        Plot feature importance
    """

    data = pd.read_csv(join(cwd(), 'output', 'fl_fi_models.csv'))
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

    # %% plot model results
    utest_models()

    # %% plot feature importances
    utest_feature_importance()
