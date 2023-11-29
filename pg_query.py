import psycopg2
import numpy as np
import pandas as pd
from calculation.percent_collagen import percent_collagen_mean

def query_biopsyresult(experiment_id):
    # connect to db
    connection = psycopg2.connect(
    host="34.134.210.165",
    database="vitrolabs",
    user="postgres",
    password="Vitrolabs2023!",
    port=5432)

    cur = connection.cursor()
    cur.execute("""SELECT * 
                from analytical_db.biopsy_result
                Left join tracker.analytical_tracker using(experiment_id)
                LEFT join biomaterial_scaffold.biomaterial using(biomaterial_id)
                """
                )  
    result_table = cur.fetchall()

    colnames = [desc[0] for desc in cur.description]

    data = pd.DataFrame(result_table,columns=colnames)

    data = percent_collagen_mean(data)

    if not experiment_id:
        all_experiment = data['experiment_id'].unique()
        all_experiment = all_experiment.tolist()
        filter = data[(data['experiment_id'].isin(all_experiment)) & (data['experiment_id'] is not None)]
    else:
        filter = data[(data['experiment_id'].isin(experiment_id)) & (data['experiment_id'] is not None)]

    return filter


def query_hp_raw(experiment_id):
    # connect to db
    connection = psycopg2.connect(
    host="34.134.210.165",
    database="vitrolabs",
    user="postgres",
    password="Vitrolabs2023!",
    port=5432)

    cur = connection.cursor()
    cur.execute("""SELECT * 
                from analytical_db.hydroxyproline
                Left join tracker.analytical_tracker using(experiment_id)
                LEFT join biomaterial_scaffold.biomaterial using(biomaterial_id)
                """
                )  
    result_table = cur.fetchall()

    colnames = [desc[0] for desc in cur.description]

    data = pd.DataFrame(result_table,columns=colnames)

    if not experiment_id:
        all_experiment = data['experiment_id'].unique()
        all_experiment = all_experiment.tolist()
        filter = data[(data['experiment_id'].isin(all_experiment)) & (data['experiment_id'] is not None)]
    else:
        filter = data[(data['experiment_id'].isin(experiment_id)) & (data['experiment_id'] is not None)]

    return filter