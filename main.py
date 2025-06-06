import os
import argparse
import sys
import ast
import json as json
import warnings
import hashlib
import re
import requests
import urllib.request
import traceback
import shutil

# Fairgraph
from fairgraph import KGClient
import fairgraph.openminds.core as omcore
from fairgraph.openminds.core import ModelVersion

from fairgraph.openminds.controlledterms import Technique

from ebrains_validation_framework import ModelCatalog
# from hbp_validation_framework import ModelCatalog

from deepdiff import DeepDiff

import modeldb_repo as modeldb
import github_repo as github
import zenodo_repo as zenodo

import input_output as inputoutput

# Source server from which the ALREADY KG-v3 instances are downloaded
# Default is Official KG-v3 server
SOURCE_SERVER = "core.kg.ebrains.eu"
# SOURCE_SERVER = "https://kg.ebrains.eu/api/instances/"
# SOURCE_SERVER = "core.kg-ppd.ebrains.eu"

file_default_value = {"url": None, "path": None, "filepath": None}

report_default_values = {
    "id": None, # str, ID of the model
    "workdir": "./", # str, path of the working directory
    "workflow": {
        "run": {
            "url": None, # URL of the workflow instruction file to download
            "path": None}, # Absolute path of the workflow instruction file to download
        "data": {
            "url": None, # URL of the workflow data file to download
            "path": None}, # Absolute path of the workflow data file to download
        },
    "run": {
        "code": [], # URL, Filepath and Path of the code to download and execute, IRI, Label and Homepage
        "pre-instruction": [], # array of known instructions: untar, compile, move inputs, ...
        "instruction": None, # str
        "inputs": [], # Should contain "url" and "path" of input files to download
        "outputs": [], # Should contain "url", "path" and "hash" of expected output files to download
        "environment": {
            "pip install": [], # additional PIP packages to install
            "module deps": [], # additional module packages to load
            "profiling configuration": []} # profiling configuration to add for profiling and tracing analysis
    
    },
    "paper": None, # has paper 
    "homepage": None, # has homepage, documentation url, ...
    "documentation": None # full documentation file, URL, paper
    }

# Compare report files for regression tests
def compare_reports (test_report=None, reference_report=None):
    # Test if reports are not None
    if (not test_report and not reference_report):
        print("ERROR: reference test failure: " + str(reference_report))
        exit (1)

    try:
        with open(test_report, 'r') as test_report_file, open (reference_report, 'r') as reference_report_file:
            test_items = json.load(test_report_file)
            reference_items = json.load(reference_report_file)

            diff = DeepDiff (test_items, reference_items)

            # Compare the dictionnaries
            # if (sorted(test_items) == sorted(reference_items)):
            if (not diff):
                print ("Regression test SUCCESS for " + str(test_items["Metadata"]["id"]))
                exit(0)
            else:
                print("\nERROR Test: reports are not equal. Failure\n")
                print ("Differences: " + str(diff))
                exit(1)

    except Exception as e:
        print (str("".join(traceback.format_exception(e))))
        exit (1)
    

# Run requested test
# Download Metadata and compare output report to reference report
def run_test (token=None, username=None, password=None,id=None, run=None, prerun=None, test=None):
    get_cwl_json_kg3(token=token, username=username, password=password,id=id, run=run, prerun=prerun)
    compare_reports(test_report="./metadata-report.json", reference_report=test)



### Parameters ###
#*****************
# id: str
# repos: array of url str
# inputs: array of url str
# outputs: array of url str
# runscript: array of str
def build_json_file (id:str , workdir:str, workflow, repos, inputs, outputs, prerun, runscript, environment, homepage, paper, documentation):
    json_content = { "Metadata": report_default_values}
    
    # Asserts
    assert (id != None)
    assert (repos != None)
    assert (runscript != None)
    
    # Get Model's ID
    json_content["Metadata"]["id"] = id

    # Get Model's Homepage
    json_content["Metadata"]["homepage"] = homepage

    # Get Model's Paper
    json_content["Metadata"]["paper"] = paper

    # Get Model's Documentation
    json_content["Metadata"]["documentation"] = documentation

    # Get Workdir
    json_content["Metadata"]["workdir"] = workdir if workdir else report_default_values["workdir"]
    # json_content["Metadata"]["workdir"] = os.path.abspath( json_content["Metadata"]["workdir"] ) + "/"
    json_content["Metadata"]["workdir"] = os.getenv("WORKDIR", ".") + "/"

    # Get Workflow
    # 1. Run file
    try:
        json_content["Metadata"]["workflow"]["run"]["url"] = workflow["run"]
    
    except:
        json_content["Metadata"]["workflow"]["run"]["url"] = report_default_values["workflow"]["run"]["url"]
    json_content["Metadata"]["workflow"]["run"]["path"] = json_content["Metadata"]["workdir"]

    # 2. Data file
    try:
        json_content["Metadata"]["workflow"]["data"]["url"] = workflow["data"]
    
    except:
        json_content["Metadata"]["workflow"]["data"]["url"] = report_default_values["workflow"]["data"]["url"]
    json_content["Metadata"]["workflow"]["data"]["path"] = json_content["Metadata"]["workdir"]

    # Get run instructions
    # 1. Code URL
    for icode in repos:
        code = {"url": None, "filepath": None, "path": None}
        # ModelDB ?
        if modeldb.is_modeldb_page (icode):
            code = modeldb.get_modeldb_download_link_from_page(icode)
            
        
        # GitHub repo ?
        elif github.is_github_page (icode):

            # GitHub release ?
            if github.is_github_release_page(icode):
                code = github.get_github_download_link_from_release_page(icode)

            # GitHub home page
            else:
                code = github.get_github_download_link_from_homepage(icode)

        # Zenodo repo ?
        elif zenodo.is_zenodo_page (icode):
            code = zenodo.get_zenodo_code_metadata_from_page(icode)

        else:
            code["url"] = icode
            code["filepath"] = os.path.basename(icode)
            code["path"] = os.path.basename(icode).split(".")[0]
        

        code["filepath"] = json_content["Metadata"]["workdir"] + "/code/" + code["filepath"]
        code["path"] = json_content["Metadata"]["workdir"] + "/code/" + code["path"]

        json_content["Metadata"]["run"]["code"].append(code)


    # 3. Pre-instructions
    json_content["Metadata"]["run"]["pre-instruction"] = prerun if prerun else report_default_values["run"]["pre-instruction"]

    # 4. instruction
    json_content["Metadata"]["run"]["instruction"] = runscript if runscript else report_default_values["run"]["instruction"]

    # 5. Inputs
    for iinput in inputs:
        input_from_url = inputoutput.get (iinput)

        if input_from_url:
            json_content["Metadata"]["run"]["inputs"].append(input_from_url)

    # 5.1 Calculates hash of inputs
    for iinput in json_content["Metadata"]["run"]["inputs"]:
        # Calculates hash
        iinput["hash"] = str(hashlib.md5(iinput["url"].encode()).hexdigest()) if iinput["url"] else str(hashlib.md5(iinput["filepath"].encode()).hexdigest())
        # Calculates input path
        iinput["path"] = str(str(json_content["Metadata"]["workdir"]) + "/inputs/" +
        str(iinput["hash"]))
        
    # 6. Expected outputs
    for ioutput in outputs:
        output_from_cli = inputoutput.get (ioutput)

        if output_from_cli:
            output_from_cli["path"] =  str(json_content["Metadata"]["workdir"]) + "/outputs/"
            output_from_cli["filepath"] =  output_from_cli["path"] + output_from_cli["filepath"] if output_from_cli["url"] else str(json_content["Metadata"]["workdir"]) + output_from_cli["filepath"]
            output_from_cli["filename"] =  os.path.basename(output_from_cli["filepath"])
            json_content["Metadata"]["run"]["outputs"].append(output_from_cli)
        
    # 6.1 Calculates hash of outputs
    for ioutput in json_content["Metadata"]["run"]["outputs"]:
        # Calculates hash
        ioutput["hash"] = str(hashlib.md5(ioutput["url"].encode()).hexdigest()) if ioutput["url"] else str(hashlib.md5(ioutput["filepath"].encode()).hexdigest())
        # Calculates output path
        # ioutput["path"] = str(ioutput["filepath"]).split(".")[0]
        
    # 7. Environment configuration
    # 7.1 PIP installs
    try:
        json_content["Metadata"]["run"]["environment"]["pip install"] = environment["pip install"]
    except:
        json_content["Metadata"]["run"]["environment"]["pip install"] = report_default_values["run"]["environment"]["pip install"]

    # 7.2 Module loads
    try:
        json_content["Metadata"]["run"]["environment"]["module deps"] = environment["module deps"]
    except:
        json_content["Metadata"]["run"]["environment"]["module deps"] = report_default_values["run"]["environment"]["module deps"]
    # 7.3 Profiling conf
    try:
        json_content["Metadata"]["run"]["environment"]["profiling configuration"] = environment["profiling configuration"]
    except:
        json_content["Metadata"]["run"]["environment"]["profiling configuration"] = report_default_values["run"]["environment"]["profiling configuration"]

    return json_content
    


def get_cwl_json_kg3 (username=None, password=None, token=None, id=None, run=None, prerun=None):

    client = None
    MCclient = None
    # Fairgraph
    if token:
        client = KGClient(token=token, host=SOURCE_SERVER)
        MCclient = ModelCatalog(token=token)
        # print (MCclient.get_model_instance(instance_id=id))
    elif username and password:
        MCclient = ModelCatalog(username=username, password=password)
        # print (MCclient.get_model_instance(instance_id=id))
        token = MCclient.token
        client = KGClient(token=token, host=SOURCE_SERVER)
    if not client:
        raise Exception ("Client is " + str(type(client)))
    try:
        model_version = ModelVersion.from_id(id, client)
        # model_version.show()

        if not model_version:
            raise Exception ("ModelVersion is None")
    except Exception as e:
        print (e)
        exit (1)
    
    # Get model's code location
    try:
        instance_repo = []
        if not model_version.repository:
            raise Exception ("Instance repository does not exists")
        instance_repo.append (model_version.repository.resolve(client).iri.value)
        # instance_repo.append (model_version.repository.resolve(client).label.value)
        # if model_version.homepage:
            # instance_repo.append (model_version.homepage.resolve(client).url.value)
    except Exception as e:
        print (str("".join(traceback.format_exception(e))))
        exit (1)

    try:
        # Get homepage
        instance_homepage = None
        if model_version.homepage:
            instance_homepage = model_version.homepage.value
        # print ("Homepage: " + str(instance_homepage))
    except Exception as e:
        print (str("".join(traceback.format_exception(e))))
        instance_homepage = None

    try:
        # Get paper
        instance_paper = None
        if model_version.related_publications:
            instance_paper = model_version.related_publications.resolve(client).identifier
        # print ("Paper: " + str(instance_paper))
    except Exception as e:
        print (str("".join(traceback.format_exception(e))))
        instance_paper = None

    try:
        # Get full-documentation
        instance_documentation = None
        if model_version.full_documentation:
            instance_documentation = model_version.full_documentation.value
        print ("Full-documentation: " + str(instance_documentation))
    except Exception as e:
        print (str("".join(traceback.format_exception(e))))
        instance_documentation = None

    # Get inputs
    #       !! No exception raised if no inputs
    #       !! Warning message is shown instead
    try:
        instance_inputs = []
        if model_version.input_data:
            for iinput in model_version.input_data:
                input_from_ebrains_dataset = inputoutput.get_url_from_ebrains_dataset (iinput, client)
                
                if not input_from_ebrains_dataset:
                    instance_inputs.append(iinput)
                else:
                    instance_inputs.append(input_from_ebrains_dataset)

        if not instance_inputs:
            warnings.warn("No input data for this Instance ... Continue")
    except Exception as e:
        print (str("".join(traceback.format_exception(e))))

    # # Get Outputs
    # # TODO Decision: What to do with no output expected ?
    # # ! Exception raised
    # try:
    #     instance_outputs = []
        
    #     for ioutput in outputs:
    #         output_from_ebrains_dataset = inputoutput.get_url_from_ebrains_dataset (ioutput, client)

    #         if not output_from_ebrains_dataset:
    #             instance_outputs.append(ioutput)
    #         else:
    #             instance_outputs.append(output_from_ebrains_dataset)
        
    #     # if outputs:
    #     #     instance_outputs = outputs
    #     # else:
    #     #     instance_outputs = model_version.output_data
    #     # Check if outputs are EBRAINS datasets
    #     # TODO check if outputs are file objet/file bundle objects/ Web object

    #     if not instance_outputs:
    #         warnings.warn("No output data to compare for this Instance ... Continue")
        
    # except Exception as e:
    #     print (str("".join(traceback.format_exception(e))))
    #     exit (1)


    # Get Pre-Run instructions, to prepare simulation run
    instance_prerun = prerun


    # Get Run instructions,
    # by default the run instruction is set according to parameter $run
    # TODO:
    # - Add run instruction Download
    try:
        if not run:
            raise Exception ("No run instruction specified for this Instance")
        instance_run = run
    except Exception as e:
        print (str("".join(traceback.format_exception(e))))
        exit (1)

    try:
        # Build JSON File that contains all important informations
        json_content = build_json_file (id=id, workflow={}, workdir="", repos=instance_repo, inputs = instance_inputs, outputs=instance_outputs,prerun=instance_prerun, runscript=instance_run, environment={}, homepage=instance_homepage, paper=instance_paper, documentation=instance_documentation)

        # os.makedirs(os.path.dirname(json_content["Metadata"]["workdir"] + "/metadata-report.json"), exist_ok=True)
        with open(str("metadata-report.json"), "w") as f:
            json.dump(json_content, f, indent=4)

        if "metadata-report.json" in os.listdir(json_content["Metadata"]["workdir"]):
            print ("Metadata report File created successfully")

    except Exception as e:
        print (str("".join(traceback.format_exception(e))))
        exit (1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download input file for CWL workflow from an HBP Model Instance ID")

    parser.add_argument("--id", type=str, metavar="Model Instance ID", nargs=1, dest="id", default="", help="ID of the Instance to download")

    # Authentification Token
    parser.add_argument("--token", type=str, metavar="Authentification Token", nargs=1, dest="token", default="", help="Authentification Token used to log to EBRAINS")
    # Authentification Username
    parser.add_argument("--username", type=str, metavar="Authentification Username", nargs=1, dest="username", default="", help="Authentification Username used to log to EBRAINS")
    # Authentification Password
    parser.add_argument("--password", type=str, metavar="Authentification password", nargs=1, dest="password", default="", help="Authentification Password used to log to EBRAINS")

    ## Run instruction can be specified in command line
    ## A single instruction (str) is checked as of now
    parser.add_argument("--run", type=str, metavar="Run instruction", nargs=1, dest="run", default="./run", help="Running instruction to run the model instance. JSON file")

    ## Pre-Run instruction can be specified in command line
    ## A single pre-instruction (str) is checked as of now
    parser.add_argument("--pre-run", type=str, metavar="Pre-Run instruction", nargs=1, dest="prerun", default="", help="Pre-Running instructions to run before running the model instance. JSON file")

    ## Reference report location for regressions test
    ## The output report will be compared to this reference report
    parser.add_argument("--test", type=str, metavar="Reference report", nargs=1, dest="test", default="", help="Reference report for regression tests. The output report will be compared to this reference report. JSON file")

    ## Expected results, outputs generated by the authors of the model
    ## TODO this parameter is WIP, routine to get outputs from EBRAINS should be preferred
    # parser.add_argument("--outputs", type=str, metavar="URL to download expected outputs", nargs=1, dest="outputs", default="", help="URL of the results single file produced by the authors of the model.")

    ## Expected local results, outputs generated by the authors of the model already downloaded
    ## TODO this parameter is WIP, routine to get outputs from EBRAINS should be preferred
    # parser.add_argument("--archive", type=str, metavar="URL to download expected outputs", nargs=1, dest="archive", default="", help="Local results single file produced by the authors of the model.")


    parsed, args = parser.parse_known_args()

    token = None
    username = None
    password = None
    test = None
    # outputs = None
    # archive = None

    try:
        test = str(parsed.test[0])
        print ("Regression Tests requested")
    except Exception as e:
        print ("No test requested")
    
    try:
        token = str(parsed.token[0])
    except Exception as e_token:
        token = None
        print ("Authentification Token not provided")
        print (" - Trying to authentificate using username/password")
        try:
            username=str(parsed.username[0])
            password=str(parsed.password[0])
        except Exception as e_usr:
            print ("Authentification usr/password failed")
            print ("token or username/password are required\nExiting")
            exit(1)


    id = str(parsed.id[0])
    run_file = str(parsed.run[0])
    prerun_file = str(parsed.prerun[0]) if parsed.prerun else None
    # outputs = str(parsed.outputs[0]) if parsed.outputs else None
    # archive = str(parsed.archive[0]) if parsed.archive else None

    run = None
    with open(run_file) as f:
        run = json.load(f)["run"]
    prerun = None
    if prerun_file:
        with open(prerun_file) as f:
            prerun = json.load(f)["pre-run"]
    
    if id:
        if token:
            if test:
                run_test (token=token, id=id, run=run, prerun=prerun,test=test)
            else:
                get_cwl_json_kg3(token=token, id=id, run=run, prerun=prerun)
        elif username and password:
            if test:
                run_test (username=username, password=password, id=id, run=run, prerun=prerun,test=test)
            else: 
                get_cwl_json_kg3(username=username, password=password, id=id, run=run, prerun=prerun)
        else:
            print ("Error: Authentification failed")
            exit (1)
    else:
        print ("Error: Instance ID not recognized")
        exit (1)
    
    exit(0)
