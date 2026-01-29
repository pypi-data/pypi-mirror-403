# mlaunch

## About the Project
mlaunch is a Python package that automatically generates a complete machine learning model from a CSV file. It handles data preprocessing, encoding, model selection, and evaluation.

## Functions
### AutoML
this function will preprocess the data and create the model for you
```python
from mlaunch import AutoML
model = AutoML(path,y_column,model_name,type = "pipeline")
```
#### parameteres
- path: the path for your csv file
- y_column: the target column in your dataset
- model_name: the name of your model out of these current model:
    - Linear Regression
    - Logistic Regression
    - Random Forest Regression
    - Hist Gradient Boosting Regression
    - Random Forest classifier
    - Hist Gradient Boosting classifier
    - Auto Select : it will select the best model for your data
    more will be added in the future
- type: how will the output be:
    - pipeline: it will output the model as a pipeline
    - python file: it will export the model to `model.pkl` file and run a python file to input the data

### preprocessing
this function will handle the outliers and encode your data and output it as a ColumnTransformer
```python 
from mlaunch import preprocessing
preprocessor = preprocessing(model,df,y_column)
model = Pipeline([
    ("preprocessor",preprocessor)
])
```
#### parameteres
- model: put your model here
- df: put the dataframe here
- y_column: the target column in your dataset

### dataset_info
this function returns a dictionary of the size, cat_columns and num_columns
```python
from mlaunch import dataset_info
info = dataset_info(df,y_column)
```
#### parameteres
- df: put the dataframe here
- y_column: the target column in your dataset

### column_statistics
this function returns a bunch of stats for every column in the dataframe
```python
from automl import column_statistics
stats = column_statistics(df,y_column)
```
#### parameteres
- df: put the dataframe here
- y_column: the target column in your dataset