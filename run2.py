import os
import pandas as pd
import numpy as np
import multiprocessing
import mlflow
import mlflow.sklearn
from copy import copy

MIN_BATCH_SIZE = 32
EPOCHS = 1500
VALIDATION_STEPS = 50
N_ITERATIONS = 6


from argparse import ArgumentParser

parser = ArgumentParser()
parser.add_argument("--experiment_name", default="default", type=str)
parser.add_argument("--run_name", default="default", type=str)
args = parser.parse_args()


vec_model_name = 'fasttext' # fasttext / endr-bert
os.environ["vec_model_name"] = vec_model_name
experiment_name = args.experiment_name

from src.purpose_models.close__synonims_model import *
from src.data.sentence_vectorizer import SentenceVectorizer



def main():
    # configure mlflow
    mlflow.set_experiment(experiment_name)
    client = mlflow.tracking.MlflowClient()
    experiment_id = client.get_experiment_by_name(experiment_name).experiment_id
    notes = """
        SMM4H17: 67.2, 87-90, 91.73
        SMM4H21(20): 36-37, 42-44, 43-45
        CADEC: 63.23, 70-83. 86.94
        PsyTar: 60.15, 77-82, 85.76
    """
    client.set_experiment_tag(experiment_id, "mlflow.note.content", notes)

    # ['smm4h21','smm4h17','cadec','psytar']
    courpuses = ['smm4h21', 'smm4h17', 'cadec']
    courpuses = np.random.choice(courpuses, size=1)
    for corp in courpuses:
        print(f'loading datasets {corp}')

        terms_train_dataset = [
            'train_pure.csv',
            'train_aug.csv',
            'train_aug_wdnt.csv',
            #'train_aug_ppdb.csv'
        ]
        for terms_train_name in terms_train_dataset:
            #terms_train = pd.read_csv(f'data/interim/{corp}/{terms_train_name}')
            terms_train = pd.read_csv(f'data/interim/combined/{terms_train_name}')
            terms_test = pd.read_csv(f'data/interim/{corp}/test.csv')
            concepts = pd.read_csv('data/interim/used_codes_big.csv')[['code', 'STR', 'SNMS']]

            print('preparing and creating generators')
            terms_vecs_train, terms_codes_train, terms_vecs_test,  terms_codes_test, concepts_vecs, codes \
                = prepare_data(concepts, terms_train, terms_test)
            n_concepts = len(codes)
            assert terms_vecs_train.shape[1]==concepts_vecs.shape[1]
            embedding_size = terms_vecs_train.shape[1]

            print('start fitting')
            for iter in tqdm(range(N_ITERATIONS)):
                batch_size = MIN_BATCH_SIZE*(iter+1)
                steps_per_epoch = terms_train.shape[0]//batch_size * 10
                for dn_layers in [1, 2, 3]:
                    for patience in [160, 320, 600]:
                        learning_rate = np.random.choice([1e-2, 1e-3, 5e-4, 1e-4], size=1)
                        layer_size = np.random.choice([256, 512, 1024], size=1)
                        with mlflow.start_run(run_name=f"run{iter}") as run:
                            print(f"INFO: terms:{terms_train_name}, corpus:{corp}")
                            train_gen, test_gen = get_data_gens(terms_vecs_train,
                                              terms_codes_train,
                                              terms_vecs_test,
                                              terms_codes_test,
                                              concepts_vecs, batch_size=batch_size)
                            mlflow.log_param('terms_train', terms_train_name)
                            mlflow.log_param('corpus', corp)
                            mlflow.log_param('batch_size', batch_size)
                            mlflow.log_param('epochs', EPOCHS)
                            mlflow.log_param('steps_per_epoch', steps_per_epoch)
                            mlflow.log_param('validation_steps', VALIDATION_STEPS)
                            mlflow.log_param('dn_layers', dn_layers)
                            mlflow.log_param('patience', patience)
                            mlflow.log_param('learning_rate', learning_rate)
                            mlflow.log_param('layer_size', layer_size)
                            max_train, max_val = fit_synonimer(
                                train_gen, test_gen, n_concepts, embedding_size,
                                epochs=EPOCHS,
                                patience=patience,
                                steps_per_epoch=steps_per_epoch,
                                validation_steps=VALIDATION_STEPS,
                                dn_layers=dn_layers,
                                learning_rate=learning_rate,
                                layer_size=layer_size)
                            print(max_train, max_val)
                            mlflow.log_metric(f"max_train", max_train)
                            mlflow.log_metric(f"max_val", max_val)
                            try:
                                mlflow.log_artifact('reports/run2_plot.pdf')
                            except Exception as e:
                                print(e)

if __name__ == "__main__":
    main()
