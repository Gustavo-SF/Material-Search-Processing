import os
import logging
from multiprocessing import cpu_count, Pool, sharedctypes
import argparse

import pandas as pd
import numpy as np
import nltk

from connections.db_connection import DB_Connection
from text_processing.cleaner import clean_text
from text_processing.distance_calculator import dist_sentence

# Downloads needed for NLTK
nltk.download("stopwords")
nltk.download("averaged_perceptron_tagger")
nltk.download("wordnet")

BASE_DIR = os.path.dirname(os.path.realpath(__file__))
logging.basicConfig(
    filename=f"{BASE_DIR}/logs/logger.log", 
    filemode='a', 
    level=logging.INFO, 
    format="%(levelname)s - %(asctime)s - %(message)s"
    )
parser = argparse.ArgumentParser(description='Process data or load data locally.')
parser.add_argument(
    "--load-csv", action="store_true", help="Load data from current working directory."
)
args = parser.parse_args()
dbcon = DB_Connection()
if not args.load_csv:
    # Get data from SQL DB
    sqlfile = os.path.join("sql", "materials.sql")
    dataframe = dbcon.get_data(sql_file=sqlfile)

    logging.info("Dataframe loaded")

    # Transformations
    dataframe.replace("\s{2,}", "", regex=True, inplace=True)
    dataframe.replace({np.nan: None}, inplace=True)

    logging.info("Transformation done")

    # Clean text
    dataframe["clean_description"] = dataframe["material_description"].apply(
        lambda x: clean_text(x) if x is not None else ""
    )
    dataframe.loc[
        dataframe.clean_description.str.contains("^\s*$"), "clean_description"
    ] = "undefined"
    data_unique = dataframe.drop_duplicates(subset="clean_description", keep="first").copy()

    # Creating distance matrix
    logging.info("Cleaning text done")

    def apply_leven_mp(i, data):
        """Multiprocessing function to apply sentence distance calculation."""
        j_start = i + 1
        s1 = data[i]

        # Get the shared array
        TMP = np.ctypeslib.as_array(SHARED_ARRAY)

        for j, s2 in enumerate(data):
            if j < j_start:
                TMP[i, j] = 0
            else:
                TMP[i, j] = dist_sentence(s1, s2)

    X = np.asarray(data_unique["clean_description"])
    FINAL_OUTPUT_RAW = np.zeros((len(X), len(X)), dtype=np.int8)
    C_TYPE_OUTPUT = np.ctypeslib.as_ctypes(FINAL_OUTPUT_RAW)
    SHARED_ARRAY = sharedctypes.RawArray(C_TYPE_OUTPUT._type_, C_TYPE_OUTPUT)

    logging.info("Starting Multiprocessing")

    pool = Pool(processes=cpu_count())
    args = [(i, X) for i in range(len(X))]
    res = pool.starmap(apply_leven_mp, args)

    FINAL_OUTPUT_MP = np.ctypeslib.as_array(SHARED_ARRAY)

    del SHARED_ARRAY
    del FINAL_OUTPUT_RAW

    # Processing distance matrix

    logging.info("Starting to process with KNN")

    FINAL_OUTPUT_MP += FINAL_OUTPUT_MP.T
    k_neighbors = np.zeros((len(FINAL_OUTPUT_MP), 10), dtype=np.int32)
    for i in range(len(FINAL_OUTPUT_MP)):
        if (np.where((np.sort(FINAL_OUTPUT_MP[i])[0:11]) == 100)[0]).size != 0:
            end = np.where((np.sort(FINAL_OUTPUT_MP[i])[0:11]) == 100)[0][0]
        else:
            end = None

        k_neighbors[i] = np.delete(
            np.argsort(FINAL_OUTPUT_MP[i])[0:11],
            np.where(np.argsort(FINAL_OUTPUT_MP[i])[0:11] == i),
        )
        if end:
            k_neighbors[i, end - 1 :] = -1

    del FINAL_OUTPUT_MP

    for i in range(len(k_neighbors)):
        k_neighbors[i][
            : len(np.delete(k_neighbors[i], np.where(k_neighbors[i] == -1)))
        ] = np.asarray(
            data_unique.iloc[np.delete(k_neighbors[i], np.where(k_neighbors[i] == -1)), 0]
        )

    data_unique = pd.concat(
        [data_unique.reset_index(drop=True), pd.DataFrame(k_neighbors)], axis=1
    )
    dataframe = dataframe.merge(
        data_unique.iloc[:, 2:], how="inner", on="clean_description"
    )

    cols = ["material_id", "material_description", "clean_description",
        "similar_1", "similar_2", "similar_3", "similar_4", "similar_5",
        "similar_6", "similar_7", "similar_8", "similar_9", "similar_10"]

    dataframe.columns = cols
    dataframe.drop(columns=["material_description", "clean_description"], inplace=True)

    dataframe.to_csv("material_proximity_data.csv", index=False)
else:
    dataframe = pd.read_csv("material_proximity_data.csv", dtype=str)

logging.info("Data is ready!")

createtable_file = os.path.join("sql", "create_table.sql")
dbcon.run_query(sql_file=createtable_file)

logging.info("Created new table")

dbcon.load_data(dataframe, "material_proximity", "proc_db")

logging.info("Loaded data into new table")
