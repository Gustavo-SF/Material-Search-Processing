from typing import final
import pandas as pd
import numpy as np
import logging
import os
from multiprocessing import cpu_count, Pool, sharedctypes
from sklearn.neighbors import NearestNeighbors

from connections.db_connection import DB_Connection
from text_processing.cleaner import clean_text
from text_processing.distance_calculator import dist_sentence

BASE_DIR = os.path.dirname(os.path.realpath(__file__))
logging.basicConfig(filename=f"{BASE_DIR}/logs/logger.log", filemode='a', level=logging.INFO)

# Get data from SQL DB
dbcon = DB_Connection()
sqlfile = os.path.join("sql", "materials.sql")
dataframe = dbcon.get_data(sql_file=sqlfile)

logging.info("Dataframe loaded")

# Transformations
dataframe.replace("\s{2,}", "", regex=True, inplace=True)
dataframe.replace({np.nan: None}, inplace=True)
dataframe = dataframe[dataframe.MaterialType == "ZMAT"].copy()
dataframe.drop(columns=["MaterialType"], inplace=True)

logging.info("Transformation done")

# Clean text
dataframe["description_clean"] = dataframe["MaterialDescription"].apply(
    lambda x: clean_text(x) if x is not None else ""
)
dataframe.loc[
    dataframe.description_clean.str.contains("^\s*$"), "description_clean"
] = "undefined"
data_unique = dataframe.drop_duplicates(subset="description_clean", keep="first").copy()

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


X = np.asarray(data_unique["description_clean"])
final_output = np.zeros((len(X), len(X)), dtype=np.int8)
c_type_output = np.ctypeslib.as_ctypes(final_output)
SHARED_ARRAY = sharedctypes.RawArray(c_type_output._type_, c_type_output)

logging.info("Starting multiprocessing")

pool = Pool(processes=cpu_count())
args = [(i, X) for i in range(len(X))]
pool.starmap(apply_leven_mp, args)
FINAL_OUTPUT_MP = np.ctypeslib.as_array(SHARED_ARRAY)

del SHARED_ARRAY
del final_output

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
    data_unique.iloc[:, 2:], how="inner", on="description_clean"
)

logging.info("Data is ready!")

createtable_file = os.path.join("sql", "create_table.sql")
dbcon.run_query(createtable_file)

logging.info("Created new table")

dbcon.load_data(dataframe, "MaterialProximity")

logging.info("Loaded data into new table")
