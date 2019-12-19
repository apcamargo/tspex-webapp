import os
import uuid

import pandas as pd
from flask import Flask, flash, redirect, render_template, request, send_from_directory, url_for
from werkzeug.utils import secure_filename
from worker import celery


# Define global variables
TITLE = 'tspex: Tissue-specificity calculator'
BASE_PATH = '/tspex-app'
UPLOAD_FOLDER = os.path.join(BASE_PATH, 'uploads')
ALLOWED_EXTENSIONS = ['tsv', 'csv', 'xls', 'xlsx']

# Disable pandas max_colwidth
pd.set_option('display.max_colwidth', -1)

# Create Flask app
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = os.environ['FLASK_SECRET_KEY']


@app.route('/', methods=['GET', 'POST'])
def index():
    methodlist = {
        'Counts': 'counts',
        'Tau': 'tau',
        'Gini coefficient': 'gini',
        'Simpson index': 'simpson',
        'Shannon entropy specificity': 'shannon_specificity',
        'ROKU specificity': 'roku_specificity',
        'TSI': 'tsi',
        'Z-score': 'zscore',
        'SPM': 'spm',
        'SPM DPM': 'spm_dpm',
        'Jensen-Shannon distance specificity': 'js_specificity',
        'Jensen-Shannon distance specificity DPM': 'js_specificity_dpm',
    }
    if request.method == 'POST':
        # Get the "method" and "log" parameters
        method = methodlist[request.form.get('selector')]
        log = request.form.getlist('checklog')
        # Check input file extension
        input_file = request.files['file']
        if not allowed_file(input_file.filename):
            flash('Only TSV, CSV and Excel files are allowed.', 'danger')
            return redirect(request.url)
        if input_file and allowed_file(input_file.filename):
            filename = secure_filename(input_file.filename)
            # Add 5 random characters to the file name and save it to the uploads directory
            filename = '{}_{}{}'.format(
                os.path.splitext(filename)[0], uuid.uuid4().hex[0:5], os.path.splitext(filename)[1]
            )
            input_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            input_file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            # Get the file extension and open it in pandas
            input_extension = input_file_path.rsplit('.', 1)[1].lower()
            if input_extension == 'tsv':
                data = pd.read_csv(input_file_path, sep='\t', thousands=',', index_col=0)
            elif input_extension == 'csv':
                data = pd.read_csv(input_file_path, thousands=',', index_col=0)
            elif input_extension in ['xls', 'xlsx']:
                data = pd.read_excel(input_file_path, thousands=',', index_col=0)
            # Check if there are duplicated gene names
            if data.index.duplicated().any():
                flash(
                    'We detected duplicated gene names in your file. Ensure all names in the first column are different.',
                    'danger',
                )
                return redirect(request.url)
            # Convert data to a JSON string
            data_json = data.to_json()
            # Delete input file
            os.remove(input_file_path)
            # Create a name for the output
            output_file = '{}_{}.tsv'.format(os.path.splitext(filename)[0], method)
            output_file_path = os.path.join(app.config['UPLOAD_FOLDER'], output_file)
            # Start a Celery task and send user to the results page
            celery.send_task(
                'tasks.start_tspex', args=[data_json, output_file_path, method, log], kwargs={}
            )
            return submission_complete(output_file)
    return render_template('index.html', methodlist=methodlist, title=TITLE)


@app.route('/')
def submission_complete(output_file):
    output_file_base = os.path.splitext(output_file)[0]
    download_url = request.base_url + output_file_base
    return render_template('submission.html', download_url=download_url, title=TITLE)


@app.route('/<output_file_base>')
def results_page(output_file_base):
    output_file = output_file_base + '.tsv'
    output_file_path = os.path.join(app.config['UPLOAD_FOLDER'], output_file)
    if os.path.exists(output_file_path):
        dataframe = pd.read_csv(output_file_path, sep='\t', index_col=None)
        columns = list(dataframe.columns)
        columns[0] = 'ID'
        dataframe.columns = columns
        dataframe_html = dataframe.to_html(
            index=False,
            justify='left',
            table_id='dataframe-id',
            border=0,
            classes=['table', 'table-striped', 'table-hover', 'nowrap'],
        )
        return render_template(
            'results.html', output_file=output_file, dataframe_html=dataframe_html, title=TITLE
        )
    else:
        return render_template('missing.html', title=TITLE)


@app.route('/uploads/<output_file>')
def uploaded_file(output_file):
    output_file_path = os.path.join(app.config['UPLOAD_FOLDER'], output_file)
    if os.path.exists(output_file_path):
        return send_from_directory(app.config['UPLOAD_FOLDER'], output_file)
    else:
        return render_template('missing.html', title=TITLE)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


if __name__ == '__main__':
    app.run(debug=False)
