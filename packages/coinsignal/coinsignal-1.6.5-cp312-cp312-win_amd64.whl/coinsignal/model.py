# --------------------------------------------------------------------------------
# Copyright (c) 2025 Zehao Yang
#
# Author: Zehao Yang
#
# This module implements the main model training and evaluation pipeline:
# • Handling data splitting, scaling, cross-validation,
# • Training and evaluating models with various metrics
# --------------------------------------------------------------------------------


import _ext.model as _model


DEFAULT_MODEL_PARAMS_DICT = {
    'existing_model_dir': '',
    'stats_percentiles': [0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 0.75, 0.9, 0.95, 0.975, 0.99],
    'group_count': 5,
    'train_ratio': 0.8,
    'valid_sub_ratio': 0.25,
    'test_isolate_time': 0,
    'is_random_start': False,
    'is_cv': True,
    'cv_split_count': 4,
    'cv_eval_train_metric': True,
    'cv_selection_metric': 'loss',
    'cv_selection_signal_idx': 0,
    'num_boost_round': 1000,
    'log_evaluation_period': 50,
    'num_iterations': [400, 700, 1000],
    'signal_idxs': None,
    'is_symbol_evaluated': False,
    'X_scaler_sub_params': {
        'name': '',
        'vlimits': None,
        'qlimits': [0, 1],
        'inner_scale': 1,
        'outer_scale': 1
    },
    'y_scaler_sub_params': {
        'name': '',
        'vlimits': None,
        'qlimits': [0, 1],
        'inner_scale': 1,
        'outer_scale': 1
    },
    'loss_sub_params': {
        'name': '',
        'init_method': '',
        'dof': 1,
        'fee': 0,
        'sensitivity': 1
    },
    'weight_sub_params': {
        'name': '',
        'weight_limit': 1,
        'is_sign_balanced': False
    },
    'training_sub_params': {
        'boosting_type': 'gbdt',
        'num_leaves': 25,
        'max_depth': 5,
        'learning_rate': 0.005,
        'reg_alpha': 1,
        'reg_lambda': 1,
        'min_gain_to_split': 0.1,
        'extra_trees': True,
        'objective': 'regression',
        'metric': '',
        'num_class': 1,
        'verbose': -1
    }
}


def run_model(full_features_df, model_params_dict):
    model_evaluations = _model.run_model(full_features_df, model_params_dict)
    return model_evaluations