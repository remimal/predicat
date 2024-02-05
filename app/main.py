# -*- coding: utf-8 -*-
"""
Main file for the API.
Created on Tue Jan 12 11:58:03 2021
@author: jeremy l'hour, Yves-Laurent Benichou
"""

import csv
from typing import List, Optional

import fasttext
import yaml
from fastapi import FastAPI, Query
from typing_extensions import Literal
from utils_ddc import predict_using_model, preprocess_text


def read_yaml(file):
    with open(file, "r") as stream:
        config = yaml.safe_load(stream)
    return config


def read_dict(file):
    with open(file, mode="r", encoding="utf8") as f_in:
        reader = csv.reader(f_in, delimiter=";")
        dict_from_csv = {rows[0].strip(): rows[1].strip() for rows in reader}
    return dict_from_csv


app = FastAPI(
    title="Predicat",
    description="Predict category from a product description",
    version="1.0.0",
)


@app.on_event("startup")
def startup_event():
    global models, config, full_dict
    config = read_yaml("config.yaml")
    dict_na2008 = read_dict("nomenclatures/nomenclature_NA2008.csv")
    dict_coicop = read_dict("nomenclatures/nomenclature_COICOP10.csv")
    full_dict = {**dict_na2008, **dict_coicop}
    models = {
        model: fasttext.load_model("model/" + config["model_conf"][model]["file"])
        for model in config["models"]
    }


@app.get("/")
async def read_root():
    output = {model: config["model_conf"][model] for model in config["models"]}
    return {"active models": output}


@app.get("/models_list")
async def models_list():
    output = [i for i in config["models"]]
    return {"models": output}


@app.get("/label")
async def predict_label(
    q: List[str] = Query(
        ...,
        title="query string",
        description="Description of the product to be classified",
    ),
    k: int = Query(
        1, title="top-K", description="Specify number of predictions to be displayed"
    ),
    v: Optional[bool] = Query(
        False, title="verbosity", description="If True, add the label of code category"
    ),
    n: Literal["na2008", "coicop", "na2008_old", "all"] = Query(
        "all", title="nomenclature", description="Classification system desired"
    ),
):
    if n == "all":
        n = [i for i in config["models"]]
    if type(n) == str:
        n = [n]
    output = {}

    for nomenclature in n:
        output[nomenclature] = {}
        descriptions = sorted(set(q), key=q.index)
        preprocessed_descriptions = [
            preprocess_text(description) for description in descriptions
        ]
        preds = predict_using_model(
            preprocessed_descriptions, model=models[nomenclature], k=k
        )
        if v:
            for pred in preds:
                for pred_k in pred:
                    pred_k["label"] += " | " + full_dict.get(pred_k["label"], "")
        for description, pred in zip(descriptions, preds):
            output[nomenclature][description] = pred

    return output


@app.get("/process")
async def process(
    q: List[str] = Query(
        ...,
        title="Query string",
        description="Process description with cleaning algorithm",
    )
):
    output = {}
    for item in set(q):
        output[item] = preprocess_text(item)
    return output


@app.get("/label_description")
async def label_description(
    q: List[str] = Query(
        ...,
        title="Query string",
        description="Convert nomenclatures codes to description",
    )
):
    output = {}
    for item in set(q):
        item = item.upper()
        output[item] = full_dict.get(item, None)
    return output
