import pandas as pd
import numpy as np
from sklearn import datasets
from sklearn.linear_model import Lasso, LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.feature_selection import SelectFromModel
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder

class ModelRun:
    def __init__(self, dataset_csv):
        self.dataset = dataset_csv
        # self.user = user
        self.toNormalize = ['Age', 'Afraid', 'Angry', 'Attractive', 'Babyface', 'Disgusted', 'Dominant', 'Feminine', 'Happy',
              'Masculine', 'Prototypic', 'Sad', 'Surprised', 'Threatening', 'Trustworthy', 'Unusual', 'Luminance_median',
              'Nose_Width', 'Nose_Length', 'Lip_Thickness', 'Face_Length', 'R_Eye_H', 'L_Eye_H', 'Avg_Eye_Height', 'R_Eye_W',
              'L_Eye_W','Avg_Eye_Width','Face_Width_Cheeks','Face_Width_Mouth','Forehead','Pupil_Top_R','Pupil_Top_L','Asymmetry_pupil_top',
              'Pupil_Lip_R','Pupil_Lip_L','Asymmetry_pupil_lip','BottomLip_Chin','Midcheek_Chin_R','Midcheek_Chin_L','Cheeks_avg','Midbrow_Hairline_R',
               'Midbrow_Hairline_L', 'CheekboneProminence']
        dsN = 0
        for c in self.toNormalize:
            dsN = self.normalizeColumn(self.dataset, c)
        self.dataset = dsN
        #lin reg
        self.bestAlpha = float("-inf")
        self.lassoCoef = []
        self.lin_reg_feats = []
        self.reg_rmse = float("-inf")
        #for extra trees
        self.feat_importance_map = {}
        self.rf_rmse = float("-inf")

    def normalizeColumn(self, data, cName):
        data[cName]=((data[cName]-data[cName].min())/(data[cName].max()-data[cName].min()))
        return data

    def pre_processing(self, dataset):
        gender_mapper = {'M': 0, 'F': 1}
        dataset['Gender'].replace(gender_mapper, inplace=True)
        dataset['Credit_rating'] = dataset['Credit_rating'].replace(['Poor'],'1')
        dataset['Credit_rating'] = dataset['Credit_rating'].replace(['Fair'],'2')
        dataset['Credit_rating'] = dataset['Credit_rating'].replace(['Good'],'3')
        dataset['Credit_rating'] = dataset['Credit_rating'].replace(['Very Good'],'4')
        dataset['Credit_rating'] = dataset['Credit_rating'].replace(['Exceptional'],'5')
        dataset['Credit_rating'] = dataset['Credit_rating'].replace(['Eceptional'],'5')
        return dataset

    def data_encoding(self, dataset):
        ct = ColumnTransformer(transformers = [('encoder', OneHotEncoder(), [4])], remainder='passthrough')
        ds = np.array(ct.fit_transform(dataset))
        ds_columns = dataset.columns
        ds_columns = ds_columns.drop('Race')
        ds_columns = ds_columns.insert(0,'r_a')
        ds_columns = ds_columns.insert(1,'r_b')
        ds_columns = ds_columns.insert(2,'r_l')
        ds_columns = ds_columns.insert(3,'r_w')
        ds = pd.DataFrame(ds, columns=ds_columns)
        return ds

    def more_preprocessing(self, dataset):
        dataset = dataset.drop(['Suitability'], axis=1)
        dataset = dataset.drop(['Target'], axis=1)
        dataset = dataset.drop(['NumberofRaters'], axis=1)
        return dataset

    def get_lasso_best_alpha(self, in_this_dataset):
        #X and Y values
        X = in_this_dataset.iloc[0:len(in_this_dataset), :-1]
        y = in_this_dataset.iloc[0:len(in_this_dataset), -1:]
        #Train/Test split
        from sklearn.model_selection import train_test_split
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
        #Lasso instance
        from sklearn.linear_model import LassoCV
        lassoregcv = LassoCV(n_alphas=100, normalize=False, random_state=1)
        #Fit lasso model
        lassoregcv.fit(X_train, y_train)
        #model score
        lassoregcv.score(X_test, y_test), lassoregcv.score(X_train, y_train)
        #return the alpha
        return lassoregcv.alpha_

    def compute_lasso(self, in_this_dataset, alpha_value):
        #X and Y values
        X = in_this_dataset.iloc[0:len(in_this_dataset), :-1]
        y = in_this_dataset.iloc[0:len(in_this_dataset), -1:]
        dfX = X
        #Train/Test split
        from sklearn.model_selection import train_test_split
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
        #Lasso instance
        lasso = Lasso(alpha=alpha_value, max_iter=10000)
        #Fit lasso model
        lasso.fit(X_train, y_train)
        #model score
        lasso.score(X_test, y_test), lasso.score(X_train, y_train)
        #return lasso and features
        return lasso, pd.Series(lasso.coef_, index=dfX.columns)

    def run_regressor(self, dataset_param, features):
        regressor = 0
        user_id = ''
        group_id = ''
        accuracy = 0
        rmse_scores = 0
        dataset_param = dataset_param[features]
        X = dataset_param.iloc[0:len(dataset_param), :-1]
        y = dataset_param.iloc[0:len(dataset_param), -1:]
        X = X.astype(float)
        y = y.astype(float)
        #split dataset into train/test
        from sklearn.model_selection import train_test_split
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size = 0.25, random_state = 0)
        #creating the model
        from sklearn.linear_model import LinearRegression
        regressor = LinearRegression()
        #train the model
        regressor.fit(X_train, y_train)
        #testing the model
        y_pred = regressor.predict(X_test)
        for pred in y_pred:
            pred[0] = round(pred[0])
        from sklearn.metrics import mean_squared_error
        score = np.sqrt(mean_squared_error(y_test, y_pred))
        return regressor, score

    def run_random_forest(self, dataset_param, features, file_with_scores='dt_scores.csv', save_report=False):
        classifier = 0
        user_id = ''
        group_id = ''
        accuracy = 0
        rmse_scores = 0
        dataset_param = dataset_param[features]
        X = dataset_param.iloc[0:len(dataset_param), :-1]
        y = dataset_param.iloc[0:len(dataset_param), -1:]
        X = X.astype(float)
        y = y.astype(float)
        #split dataset into train/test
        from sklearn.model_selection import train_test_split
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size = 0.25, random_state = 0)
        #creating the model
        from sklearn.ensemble import RandomForestRegressor
        regressor = RandomForestRegressor(n_estimators = 50, random_state = 0)
        #train the model
        regressor.fit(X_train, y_train)
        #testing the model
        y_pred = regressor.predict(X_test)
        #compute scores
        from sklearn.metrics import mean_squared_error
        score = np.sqrt(mean_squared_error(y_test, y_pred))
        return regressor, score

    def run_grid_search_cv(self, dataset_param):
            from sklearn.model_selection import GridSearchCV
            from sklearn.ensemble import RandomForestRegressor, ExtraTreesRegressor
            from sklearn.metrics import mean_squared_error
            X = dataset_param.iloc[0:len(dataset_param), :-1]
            y = dataset_param.iloc[0:len(dataset_param), -1:]
            X = X.astype(float)
            y = (y.astype(float))
            params = {'max_depth': [2,3,4,5], 'max_features': ['auto', 'sqrt', 'log2'],'warm_start': [True, False], 'min_samples_split': [2, 5, 10, 15, 20]}
            grid_search_cv = GridSearchCV(ExtraTreesRegressor(n_estimators=50, random_state=42), params, verbose=1, cv=3)#, n_jobs=-1)
            grid_search_cv.fit(X, y.values.ravel())
            y_pred = grid_search_cv.best_estimator_.predict(X)
            score = np.sqrt(mean_squared_error(y, y_pred))
            return grid_search_cv.best_estimator_, score

    def get_feats_from(self, col_names):
        all_feat_names = pd.DataFrame(col_names)
        all_feat_names = all_feat_names.T
        feats_to_use = []
        for f in all_feat_names.columns:
            val = all_feat_names[f]
            if abs(val[0]) > 0.0003:
                feats_to_use.append(f)
        feats_to_use.append('User_choice')
        return feats_to_use

    def remove_feats_for_reg_in(self, ds_for_feat_selection):
        # ds_for_feat_selection = ds_for_feat_selection.drop(['User'], axis=1)
        ds_for_feat_selection = ds_for_feat_selection.drop(['Treatment'], axis=1)
        ds_for_feat_selection = ds_for_feat_selection.drop(['TreatID'], axis=1)
        return ds_for_feat_selection

    def deal_with_null_cases(self):
        return ['Credit_rating', 'Attractive','Disgusted', 'Feminine','Sad', 'Trustworthy', 'User_choice']

    def save_model(self, folder, file_name, classifier):
        import pickle
        classifier_file_name = folder + file_name + '.pkl'
        with open(classifier_file_name, 'wb') as file:
            pickle.dump(classifier, file)

    def load_model(self, file_name):
        import pickle
        classifer = 0
        with open(file_name, 'rb') as file:
            classifier = pickle.load(file)
        return classifier

    def get_feat_importance_for_this(self, model, user_data_set):
        key_list = user_data_set.columns.tolist()
        feat_importance_ = model.feature_importances_
        # feat_importance_map = {}
        # for key in key_list:
        #     feat_importance_map[key] = 0

        # for i in range(0, len(feat_importance_)):
        #     feat_importance_map[temp[i]] = feat_importance_[i]
        feat_importance_map = zip(key_list, feat_importance_)

        return feat_importance_map

    def get_lasso_coef(self, dataset_param, srs):
        allKeys = dataset_param.columns.tolist()
        map_feat_lasso = {}
        for key in allKeys:
            map_feat_lasso[key] = srs.get(key)
        return map_feat_lasso

    def whole_procedure(self, user):
        self.dataset = self.pre_processing(self.dataset)
        self.dataset = self.data_encoding(self.dataset)
        #print(self.dataset)
        self.dataset = self.more_preprocessing(self.dataset)
        self.dataset = self.remove_feats_for_reg_in(self.dataset)
        # alpha = self.get_lasso_best_alpha(in_this_dataset=self.dataset)
        # lasso, cnames = self.compute_lasso(in_this_dataset=self.dataset, alpha_value=alpha)
        feats_to_use = []
        # feats_to_use = self.get_feats_from(col_names=cnames)
        #less than 1% of the models will have only one featured selected - we
        #use the ones pointed by the REF in these cases
        # if len(feats_to_use) <= 1:
        #     feats_to_use = self.deal_with_null_cases()
        rf_reg, rf_score = self.run_grid_search_cv(dataset_param=self.dataset)
        # reg, reg_score = self.run_regressor(dataset_param=self.dataset, features=feats_to_use)
        self.save_model(folder='rf_regs/', file_name=user, classifier=rf_reg)
        # self.save_model(folder='regs/', file_name=user, classifier=reg)
        # self.bestAlpha = alpha
        # self.lassoCoef = self.get_lasso_coef(dataset_param=self.dataset, srs=cnames)
        self.lin_reg_feats = feats_to_use
        # self.reg_rmse = reg_score
        self.feat_importance_map = self.get_feat_importance_for_this(model=rf_reg, user_data_set=self.dataset)
        self.rf_rmse = rf_score

    def pre_process_for_rec(self):
        self.dataset = self.pre_processing(self.dataset)
        self.dataset = self.data_encoding(self.dataset)
        self.dataset = self.more_preprocessing(self.dataset)
        # self.dataset = self.remove_feats_for_reg_in(self.dataset)
        return self.dataset

    def rec(self, user):
        model = self.load_model('rf_regs/' + user + '.pkl')
        self.dataset = self.pre_process_for_rec()
        # X = new_data.iloc[0:len(ds)]
        # x = self.dataset.loc[self.dataset['TreatID'].isin(treat_id)]
        # x = data
        x = self.remove_feats_for_reg_in(self.dataset)
        x = x.astype(float)
        # x['prediction'] = model.predict(x[x.columns.difference(["Treatment","TreatID"],sort=False)])
        self.dataset['prediction'] = model.predict(x)
        recommendation = pd.Series(self.dataset.prediction.values, index=self.dataset.TreatID).to_dict()

        return recommendation
