import pandas as pd
from sklearn.ensemble import AdaBoostClassifier
import joblib
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer


def train():
    insta_data = pd.read_csv('dataset.csv')
    insta_X = insta_data.drop('fake', axis=1)
    insta_y = insta_data['fake']

    insta_model = Pipeline(steps=[
        ('preprocessor', ColumnTransformer(transformers=[
            ('num', Pipeline(steps=[('scaler', StandardScaler())]),
             ['profile pic', 'nums/length username', 'fullname words', 'nums/length fullname', 'name==username',
              'description length', 'external URL', '#posts', '#followers', '#follows']),
            ('cat', Pipeline(steps=[('onehot', OneHotEncoder())]), ['private'])
        ])
         ),
        ('classifier', AdaBoostClassifier())
    ])
    insta_model.fit(insta_X, insta_y)

    joblib.dump(insta_model, 'insta_model.joblib')
