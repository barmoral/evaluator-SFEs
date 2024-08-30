"""
Evaluator workflow to Load and Filter Data Sets, Estimate Data Sets
Applied to calculations of SFE of Water.
"""

# Core Imports & Setup

import os
from pathlib import Path

import warnings
warnings.filterwarnings("ignore")

import logging
logging.getLogger("openff.toolkit").setLevel(logging.ERROR)

from openff import toolkit, evaluator

from openff.units import unit

import json

# 1) Loading data sets

## Extracting Data from ThermoML or json file 
from openff.evaluator.datasets import PhysicalProperty, PropertyPhase, PhysicalPropertyDataSet
from openff.evaluator.datasets.thermoml import thermoml_property, ThermoMLDataSet

data_set_initial = PhysicalPropertyDataSet.from_json("freesolv.json")

# np_s=open('nonp_freesolv.json')
# np_list=json.loads(np_s.read())
# np_list_p1=np_list[:30]
# np_list_p2=np_list[30:60]
# np_list_p3=np_list[60:]
# np_list_p1.insert(0,'O')
# np_list_p2.insert(0,'O')
# np_list_p3.insert(0,'O')

## Filtering data sets
from openff.evaluator.datasets.curation.components.filtering import FilterBySmiles, FilterBySmilesSchema

data_set_sfe= FilterBySmiles.apply(
    data_set_initial, FilterBySmilesSchema(smiles_to_include=['CC(C)C','O']))

## Saving filtered data set to json file
data_set_path = Path('filtered_dataset_sfe_np1.json')
data_set_sfe.json(data_set_path, format=True)

# 2) Estimating data sets

## Loading data set and applying FF parameters
from openff.toolkit.typing.engines.smirnoff import forcefield, ForceField
from openff.evaluator.forcefield import SmirnoffForceFieldSource

### load data
data_set_path = Path('filtered_dataset_sfe_np1.json')
data_set = PhysicalPropertyDataSet.from_json(data_set_path)

### load FF
ffpath=str(forcefield._get_installed_offxml_dir_paths()[1])

OFF_=os.getenv('OFF')
WATERFF_=os.getenv('WATERFF')

off=ffpath+'/'+OFF_
waterff=ffpath+'/'+WATERFF_

### load FF
force_field = ForceField(off, waterff)
with open("force-field.json", "w") as file:
    file.write(SmirnoffForceFieldSource.from_object(force_field).json())

force_field_source = SmirnoffForceFieldSource.from_json("force-field.json")

## Defining calculation Schemas
from openff.evaluator.properties import Density, EnthalpyOfMixing, SolvationFreeEnergy
from openff.evaluator.client import RequestOptions

sfe_schema = SolvationFreeEnergy.default_simulation_schema(n_molecules=1000)

### Create an options object which defines how the data set should be estimated.
estimation_options = RequestOptions()

### Specify that we only wish to use molecular simulation to estimate the data set.
estimation_options.calculation_layers = ["SimulationLayer"]

### Add our custom schemas, specifying that the should be used by the 'SimulationLayer' estimation_options.add_schema("SimulationLayer", "Density", density_schema)
estimation_options.add_schema("SimulationLayer", "SolvationFreeEnergy", sfe_schema)

## Launching a Server and Client
from openff.evaluator.backends import ComputeResources
from openff.evaluator.backends.dask import DaskLocalCluster
from openff.evaluator.server import EvaluatorServer
from openff.evaluator.client import EvaluatorClient
from openff.evaluator.client import ConnectionOptions

### define client to submit queries
port = 8121
evaluator_client = EvaluatorClient(ConnectionOptions(server_port=port))

### define available / preferred resources
os.environ["CUDA_VISIBLE_DEVICES"] = "0"
resources = ComputeResources(
    number_of_threads=1,
    number_of_gpus=1,
    preferred_gpu_toolkit=ComputeResources.GPUToolkit.CUDA,
)

with DaskLocalCluster(number_of_workers=1, resources_per_worker=resources) as calculation_backend:
    ### spin up server
    evaluator_server = EvaluatorServer(calculation_backend=calculation_backend, delete_working_files=False, port=port)
    evaluator_server.start(asynchronous=True)

    ### estimate data set by submitting calculation schemas to newly-created server
    request, exception = evaluator_client.request_estimate(
        property_set=data_set,
        force_field_source=force_field_source,
        options=estimation_options,
    )

    ### Wait for the results.
    results, exception = request.results(synchronous=True, polling_interval=30)
    assert exception is None

    a = results.estimated_properties.json("estimated_dataset_sfe.json", format=True)
    print(a)

import shutil
original_file = "estimated_dataset_sfe.json"
destination_dir = "/projects/bamo6610/ResearchMS/blanca-evaluator-cluster/evaluator-SFEs/scratch_outputs"
os.makedirs(destination_dir, exist_ok=True)
destination_file = os.path.join(destination_dir, "estimated_dataset_sfe.json")
shutil.copyfile(original_file, destination_file)