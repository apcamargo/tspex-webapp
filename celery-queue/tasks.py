import os

import pandas as pd
from celery import Celery
import tspex


CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379')


celery = Celery('tasks', broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)


@celery.task
def start_tspex(data_json, output_file_path, method, log):
    data = pd.read_json(data_json)
    data = data.select_dtypes(include='number')
    tspex_obj = tspex.TissueSpecificity(data, method, log=log)
    results = tspex_obj.tissue_specificity
    results = results.round(4)
    if method not in ['tsi', 'zscore', 'spm', 'js_specificity']:
        results.to_csv(output_file_path, sep='\t', header=[method])
    else:
        results.to_csv(output_file_path, sep='\t', header=True)
