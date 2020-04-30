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

# pylint: disable=too-many-locals, too-many-statements

np.random.seed(10)


def classify(show_results=False):
    """
        Run classification models
    """
    y_var = 'died'
    n_estimator = 10

    df = pd.read_csv(join(cwd(), 'data', 'flclean.csv'), low_memory=False)
    df.drop(['datetime', 'fips', 'dx', 'dy'], axis=1, inplace=True)
    df.rename(columns={'Male': 'gender', 'land_sqkm': 'landsqkm',
                       'water_sqkm': 'watersqkm'}, inplace=True)
    df.dropna(inplace=True)

    # divide data set
    X = df.loc[:, df.columns != y_var]
    y = df.loc[:, df.columns == y_var]
    X_train, X_test, y_train, y_test = train_test_split(X.values,
                                                        y.values.ravel(), test_size=0.5)

    # It is important to train the ensemble of trees on a different subset
    # of the training data than the linear regression model to avoid
    # overfitting, in particular if the total number of leaves is
    # similar to the number of training samples
    X_train, X_train_lr, y_train, y_train_lr = train_test_split(X_train,
                                                                y_train, test_size=0.5)

    # Unsupervised transformation based on totally random trees
    rt = RandomTreesEmbedding(max_depth=3, n_estimators=n_estimator,
                              random_state=0)
    rt_lm = LogisticRegression(max_iter=1000, solver='lbfgs')
    pipeline = make_pipeline(rt, rt_lm)
    pipeline.fit(X_train, y_train)

    # RT
    y_pred_rt = pipeline.predict_proba(X_test)[:, 1]
    fpr_rt_lm, tpr_rt_lm, _ = roc_curve(y_test, y_pred_rt)

    # Supervised transformation based on random forests
    rf = RandomForestClassifier(max_depth=3, n_estimators=n_estimator)
    rf_enc = OneHotEncoder(categories='auto')
    rf_lm = LogisticRegression(max_iter=1000, solver='lbfgs')
    rf.fit(X_train, y_train)
    rf_enc.fit(rf.apply(X_train))
    rf_lm.fit(rf_enc.transform(rf.apply(X_train_lr)), y_train_lr)

    # RF + LR
    y_pred_rf_lm = rf_lm.predict_proba(
        rf_enc.transform(rf.apply(X_test)))[:, 1]
    fpr_rf_lm, tpr_rf_lm, _ = roc_curve(y_test, y_pred_rf_lm)

    # Supervised transformation based on gradient boosted trees
    grd = GradientBoostingClassifier(n_estimators=n_estimator)
    grd_enc = OneHotEncoder(categories='auto')
    grd_lm = LogisticRegression(max_iter=1000, solver='lbfgs')
    grd.fit(X_train, y_train)
    grd_enc.fit(grd.apply(X_train)[:, :, 0])
    grd_lm.fit(grd_enc.transform(grd.apply(X_train_lr)[:, :, 0]), y_train_lr)

    # GBT + LR
    y_pred_grd_lm = grd_lm.predict_proba(
        grd_enc.transform(grd.apply(X_test)[:, :, 0]))[:, 1]
    fpr_grd_lm, tpr_grd_lm, _ = roc_curve(y_test, y_pred_grd_lm)

    # GBT - The gradient boosted model by itself
    y_pred_grd = grd.predict_proba(X_test)[:, 1]
    fpr_grd, tpr_grd, _ = roc_curve(y_test, y_pred_grd)

    # RF - The random forest model by itself
    y_pred_rf = rf.predict_proba(X_test)[:, 1]
    fpr_rf, tpr_rf, _ = roc_curve(y_test, y_pred_rf)

    # feature importances
    fi = pd.DataFrame({'feature': list(X.columns),
                       'importance': rf.feature_importances_})
    fi.sort_values('importance', ascending=False, inplace=True)
    if show_results:
        plt.figure(figsize=(4, 4))
        ax = plt.subplot(111)
        ax.barh(fi['feature'], fi['importance'])
        plt.gca().invert_yaxis()
        ax.set_ylabel('features')
        plt.title('Feature Importance')
        plt.show()

    # logloss
    logloss_rt_lm = metrics.log_loss(y_test, y_pred_rt)
    logloss_rf_lm = metrics.log_loss(y_test, y_pred_rf_lm)
    logloss_grd_lm = metrics.log_loss(y_test, y_pred_grd_lm)
    logloss_grd = metrics.log_loss(y_test, y_pred_grd)
    logloss_rf = metrics.log_loss(y_test, y_pred_rf)
    if show_results:
        print("=== Log loss ===")
        print(f"RT  + LR = {logloss_rt_lm:.4f}")
        print(f"RF  + LR = {logloss_rf_lm:.4f}")
        print(f"GBT + LR = {logloss_grd_lm:.4f}")
        print(f"GBT      = {logloss_grd:.4f}")
        print(f"RF       = {logloss_rf:.4f}")

    # ROC AUC
    roc_rt_lm = roc_auc_score(y_test, y_pred_rt)
    roc_rf_lm = roc_auc_score(y_test, y_pred_rf_lm)
    roc_grd_lm = roc_auc_score(y_test, y_pred_grd_lm)
    roc_grd = roc_auc_score(y_test, y_pred_grd)
    roc_rf = roc_auc_score(y_test, y_pred_rf)
    if show_results:
        print("=== ROC ===")
        print(f"RT  + LR = {roc_rt_lm:.4f}")
        print(f"RF  + LR = {roc_rf_lm:.4f}")
        print(f"GBT + LR = {roc_grd_lm:.4f}")
        print(f"GBT      = {roc_grd:.4f}")
        print(f"RF       = {roc_rf:.4f}")

        plt.figure(1)
        plt.plot([0, 1], [0, 1], 'k--')
        plt.plot(fpr_rt_lm, tpr_rt_lm, label='RT + LR')
        plt.plot(fpr_rf, tpr_rf, label='RF')
        plt.plot(fpr_rf_lm, tpr_rf_lm, label='RF + LR')
        plt.plot(fpr_grd, tpr_grd, label='GBT')
        plt.plot(fpr_grd_lm, tpr_grd_lm, label='GBT + LR')
        plt.xlabel('False positive rate')
        plt.ylabel('True positive rate')
        plt.title('ROC curve')
        plt.legend(loc='best')
        plt.show()

    # create dataframe with ROC Curves
    df1 = pd.DataFrame({'model': 'Random Trees and Logistic Regression',
                        'abbrev': 'RT + LR', 'logloss': logloss_rt_lm,
                        'auc': roc_rt_lm, 'x': fpr_rt_lm, 'y': tpr_rt_lm})

    df2 = pd.DataFrame({'model': 'Random Forest',
                        'abbrev': 'RF', 'logloss': logloss_rf,
                        'auc': roc_rf, 'x': fpr_rf, 'y': tpr_rf})

    df3 = pd.DataFrame({'model': 'Random Forest and Logistic Regression',
                        'abbrev': 'RF + LR', 'logloss': logloss_rf_lm,
                        'auc': roc_rf_lm, 'x': fpr_rf_lm, 'y': tpr_rf_lm})

    df4 = pd.DataFrame({'model': 'Gradient Boosting Trees',
                        'abbrev': 'GBT', 'logloss': logloss_grd,
                        'auc': roc_grd, 'x': fpr_grd, 'y': tpr_grd})

    df5 = pd.DataFrame({'model': 'Gradient Boosting Trees and Logistic Regression',
                        'abbrev': 'GBT + LR', 'logloss': logloss_grd_lm,
                        'auc': roc_grd_lm, 'x': fpr_grd_lm, 'y': tpr_grd_lm})

    df6 = pd.DataFrame({'model': 'Random',
                        'abbrev': 'Random', 'logloss': -1 * np.log10(0.5),
                        'auc': 0.5, 'x': np.linspace(0, 1, 100),
                        'y': np.linspace(0, 1, 100)})

    df = pd.concat([df1, df2, df3, df4, df5, df6], axis=0, ignore_index=True)
    df['x'] = df['x'].round(3)
    df['y'] = df['y'].round(3)

    df = df.rename(columns={'x': 'False_Positive_Rate',
                            'y': 'True_Positive_Rate'})

    # output datasets
    df.to_csv(join(cwd(), 'output', 'fl_roc_models.csv'), index=False)
    fi.to_csv(join(cwd(), 'output', 'fl_fi_models.csv'), index=False)


if __name__ == "__main__":

    # unit test
    classify(show_results=True)
