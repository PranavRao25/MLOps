import logging
import argparse
from pathlib import Path
import matplotlib.pyplot as plt
import mlflow
from tqdm import tqdm
import mlflow.pytorch as mpt
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
import torchvision
from mlflow.models.signature import infer_signature
import torchvision.transforms as T
import yaml
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from torch.utils.data import ConcatDataset, DataLoader
from torchvision.models import ResNet50_Weights, resnet50

from utils.load import *
from utils.mail import send_mail

mpt.autolog(
    log_models=True,
    log_datasets=True,
    log_model_signatures=True,
)
mlflow.enable_system_metrics_logging()

parent = Path(__file__).resolve().parent.parent

logging.basicConfig(
    filename=parent / "prog_log.log",
    format="%(levelname)s: %(message)s", filemode="a"
)
logger = logging.getLogger()
logger.setLevel(logging.WARNING)
logger.info("DATA PREP")

with open(parent / "config.yaml", "r") as f:
    configs = yaml.full_load(f)

def successful_mail(run_name, exp_name, model_id, results):
    subject = f"MODEL_ID : {model_id} successfully trained"
    body = f"""
        Experiment {exp_name} Run {run_name} complete\n
        Validation results:\n
        {results}
    """
    # send_mail(subject, body)

def failure_mail(run_name, exp_name, model_id, e):
    subject = f"MODEL_ID : {model_id} training failed"
    body = f"""
        Experiment {exp_name} Run {run_name} failed\n
        Exception: {e}
    """
    # send_mail(subject, body)

## DATASET LOADING

def load_dataset():
    """
        Load the MNIST and Cats & Dogs Dataset and merge them
    """

    print("MNIST DATA LOADING")
    logger.info("MNIST DATA LOADING")
    mnist_dir = parent / configs["data"]["mnist"]["folder"]
    mnist_data = torchvision.datasets.MNIST(
        root=mnist_dir,
        train=True,
        download=True,
        transform=MNISTTransform(
            target_size=configs["data"]["size"],
            digit_size=configs["data"]["mnist"]["size"],
        ),
    )

    print("CATS AND DOGS DATA LOADING")
    logger.info("CATS AND DOGS DATA LOADING")
    annotations_file = parent / configs["data"]["cats_dogs"]["annotations"]
    img_dir = parent / configs["data"]["cats_dogs"]["folder"]
    cats_dogs_data = CatsAndDogsImageDataset(
        annotations_file,
        img_dir,
        transform=cat_dog_image_transform,
        target_transform=cat_dog_target_transform,
    )

    print("COMBINING DATA")
    logger.info("COMBINING DATA")
    final_len = configs["data"]["len"]
    mnist_subset = get_balanced_subset(mnist_data, samples_per_class=int(final_len/10))
    cats_dogs_subset = get_balanced_subset(cats_dogs_data, samples_per_class=final_len)
    unified_dataset = ConcatDataset([mnist_subset, cats_dogs_subset])

    ## DATASET SPLIT

    train_data, val_data, test_data = split(unified_dataset)
    train_loader = DataLoader(
        train_data, batch_size=64, shuffle=True, num_workers=4, pin_memory=True
    )
    val_loader = DataLoader(
        val_data, batch_size=64, shuffle=False, num_workers=4, pin_memory=True
    )
    test_loader = DataLoader(
        test_data, batch_size=64, shuffle=False, num_workers=4, pin_memory=True
    )

    return train_loader, val_loader, test_loader, len(train_data), len(val_data), len(test_data)

## MODEL SETUP

def train(train_loader, val_loader, train_size, val_size, exp_name, run_name, hyperparams, device):
    model_id = configs["model"]["name"]
    run = mlflow.start_run(
        run_name=run_name,
        description=f"{model_id} Training",
        nested=True
    )
    mlflow.set_tag("Model_id", model_id)
    mlflow.log_params(hyperparams)

    ## LOAD MODEL

    weights = ResNet50_Weights.IMAGENET1K_V2
    total_classes = configs["model"]["total_classes"]
    model = resnet50(weights)
    num_features = model.fc.in_features
    model.fc = nn.Linear(num_features, total_classes)

    criterion = nn.CrossEntropyLoss()  # CLASSIFICATION
    optimizer = optim.AdamW(
        model.parameters(), lr=float(hyperparams["lr"]), weight_decay=float(hyperparams["wgt_decay"])
    )
    model = model.to(device)

    is_signature = False

    try:
        num_epochs = hyperparams["epochs"]
        best_val_acc = 0.0
        total_train_results, total_val_results = {}, {}
        for epoch in tqdm(range(num_epochs), desc="Model Training", total=num_epochs,
                          bar_format='[{elapsed}<{remaining}] {n_fmt}/{total_fmt} | {l_bar}{bar} {rate_fmt}{postfix}'):
            model.train()

            ## TRAINING LOOP
            train_loss = 0.0
            train_y_true, train_y_pred = [], []
            for i, (inputs, labels) in enumerate(train_loader):
                inputs = inputs.to(device)
                labels = labels.to(device)

                optimizer.zero_grad()

                outputs = model(inputs)
                loss = criterion(outputs, labels)
                loss.backward()
                optimizer.step()

                train_loss += loss.item() * inputs.size(0)
                _, preds = torch.max(outputs, 1)
                train_y_pred.extend(preds.cpu().numpy())
                train_y_true.extend(labels.cpu().numpy())

            train_y_pred = torch.tensor(train_y_pred)
            train_y_true = torch.tensor(train_y_true)
            train_loss /= train_size
            train_results = {
                "loss": float(train_loss),
                "accuracy": accuracy_score(train_y_true, train_y_pred),
                "macro_recall": recall_score(train_y_true, train_y_pred, average="macro"),
                "macro_precision": precision_score(train_y_true, train_y_pred, average="macro"),
                "macro_f1": f1_score(train_y_true, train_y_pred, average="macro"),
                "micro_recall": recall_score(train_y_true, train_y_pred, average="micro"),
                "micro_precision": precision_score(train_y_true, train_y_pred, average="micro"),
                "micro_f1": f1_score(train_y_true, train_y_pred, average="micro")
            }

            model.eval()
            
            ## VALIDATION LOOP
            val_loss = 0.0
            val_y_true, val_y_pred = [], []
            with torch.no_grad():
                for i, (inputs, labels) in enumerate(val_loader):
                    inputs = inputs.to(device)
                    labels = labels.to(device)

                    outputs = model(inputs)
                    loss = criterion(outputs, labels)

                    val_loss += loss.item() * inputs.size(0)
                    _, preds = torch.max(outputs, 1)
                    val_y_pred.extend(preds.cpu().numpy())
                    val_y_true.extend(labels.cpu().numpy())

            val_y_pred = torch.tensor(val_y_pred)
            val_y_true = torch.tensor(val_y_true)

            val_loss /= val_size
            val_results = {
                "loss": float(val_loss),
                "accuracy": accuracy_score(val_y_true, val_y_pred),
                "macro_recall": recall_score(val_y_true, val_y_pred, average="macro"),
                "macro_precision": precision_score(val_y_true, val_y_pred, average="macro"),
                "macro_f1": f1_score(val_y_true, val_y_pred, average="macro"),
                "micro_recall": recall_score(val_y_true, val_y_pred, average="micro"),
                "micro_precision": precision_score(val_y_true, val_y_pred, average="micro"),
                "micro_f1": f1_score(val_y_true, val_y_pred, average="micro")
            }

            print(f"""
                Epoch [{epoch + 1} / {num_epochs}]
                Train Loss : {train_results["loss"]}
                Train Macro Precision : {train_results["macro_precision"]}
                Train Macro Recall : {train_results["macro_recall"]}
                Train Macro F1 : {train_results["macro_f1"]}
                Train Micro Precision : {train_results["micro_precision"]}
                Train Micro Recall : {train_results["micro_recall"]}
                Train Micro F1 : {train_results["micro_f1"]}
                Train Accuracy : {train_results["accuracy"]}

                Valid Loss : {val_results["loss"]}
                Valid Macro Precision : {val_results["macro_precision"]}
                Valid Macro Recall : {val_results["macro_recall"]}
                Valid Macro F1 : {val_results["macro_f1"]}
                Valid Micro Precision : {val_results["micro_precision"]}
                Valid Micro Recall : {val_results["micro_recall"]}
                Valid Micro F1 : {val_results["micro_f1"]}
                Valid Accuracy : {val_results["accuracy"]}
                """)

            mlflow.log_metric("train_loss", train_results["loss"], step=epoch) # type: ignore
            mlflow.log_metric("val_loss", val_results["loss"], step=epoch) # type: ignore

            mlflow.log_metric("train_accuracy", train_results["accuracy"], step=epoch)  # type: ignore
            mlflow.log_metric("val_accuracy", val_results["accuracy"], step=epoch)  # type: ignore

            mlflow.log_metric("train_macro_precision", train_results["macro_precision"], step=epoch)  # type: ignore
            mlflow.log_metric("val_macro_precision", val_results["macro_precision"], step=epoch)  # type: ignore

            mlflow.log_metric("train_micro_precision", train_results["micro_precision"], step=epoch)  # type: ignore
            mlflow.log_metric("val_micro_precision", val_results["micro_precision"], step=epoch)  # type: ignore

            mlflow.log_metric("train_macro_recall", train_results["macro_recall"], step=epoch)  # type: ignore
            mlflow.log_metric("val_macro_recall", val_results["macro_recall"], step=epoch)  # type: ignore

            mlflow.log_metric("train_micro_recall", train_results["micro_recall"], step=epoch)  # type: ignore
            mlflow.log_metric("val_micro_recall", val_results["micro_recall"], step=epoch)  # type: ignore

            mlflow.log_metric("train_macro_f1", train_results["macro_f1"], step=epoch)  # type: ignore
            mlflow.log_metric("val_macro_f1", val_results["macro_f1"], step=epoch)  # type: ignore

            mlflow.log_metric("train_micro_f1", train_results["micro_f1"], step=epoch)  # type: ignore
            mlflow.log_metric("val_micro_f1", val_results["micro_f1"], step=epoch)  # type: ignore

            mlflow.log_metrics(train_results) # type: ignore
            mlflow.log_metrics(val_results) # type: ignore

            ## CONFUSION MATRIX
            cm = confusion_matrix(val_y_true, val_y_pred)
            cm_path = parent / configs["model"]["output"] / f"confusion_matrix{epoch}.png"
            plt.imsave(cm_path, cm)
            mlflow.log_artifact(local_path=cm_path, artifact_path="confusion_matrices")

            if val_results["accuracy"] > best_val_acc:  # CURRENT BEST EPOCH
                best_val_acc = val_results["accuracy"]
                torch.save(model, parent / configs["model"]["path"])
                mlflow.log_metric("best_accuracy", best_val_acc) # type: ignore

                if not is_signature:  # MODEL SIGNATURE NOT PRESENT
                    sample_inputs, _ = next(iter(train_loader))
                    sample_inputs = sample_inputs.to(device)
                    sample_outputs = model(sample_inputs)
                    signature = infer_signature(
                        sample_inputs.cpu().numpy(), 
                        sample_outputs.cpu().detach().numpy()
                    )
                    is_signature = True

                mpt.log_model(model, artifact_path="model", signature=signature)

                total_train_results = train_results
                total_val_results = val_results

        results = {"train": total_train_results, "valid": total_val_results}
        successful_mail(run.info.run_name, exp_name, model_id, results)
        print("TRAINING DONE")
        return model
    except Exception as e:
        failure_mail(run.info.run_name, exp_name, model_id, e)
        raise e
    finally:
        print("TRAINING DONE - MLFLOW ENDING")
        mlflow.end_run()

def inference(test_loader, test_size, model, exp_name, run_name, hyperparams, device):
    """
        MODEL PERFORMANCE ON TEST DATA
    """

    model_id = configs["model"]["name"]
    run = mlflow.start_run(
        run_name=run_name,
        description=f"{model_id} Test",
        nested=True
    )
    mlflow.set_tag("Model_id", model_id)
    mlflow.log_params(hyperparams)
    
    criterion = nn.CrossEntropyLoss()
    model = model.to(device)

    try:
        model.eval()

        test_loss = 0.0
        test_y_true, test_y_pred = [], []
        with torch.no_grad():
            for i, (inputs, labels) in enumerate(test_loader):
                inputs = inputs.to(device)
                labels = labels.to(device)

                outputs = model(inputs)
                loss = criterion(outputs, labels)

                test_loss += loss.item() * inputs.size(0)
                _, preds = torch.max(outputs, 1)
                test_y_pred.extend(preds.cpu().numpy())
                test_y_true.extend(labels.cpu().numpy())

        test_y_pred = torch.tensor(test_y_pred)
        test_y_true = torch.tensor(test_y_true)

        eval_df = pd.DataFrame({
            "targets": test_y_true.numpy(),
            "predictions": test_y_pred.numpy()
        })

        results = mlflow.evaluate(
            data=eval_df,
            targets="targets",
            predictions="predictions",
            model_type="classifier",
            evaluator_config={
                "log_model_explainability": False
            }
        )
        test_results = results.metrics

        # Print the training and test loss and accuracy
        test_loss /= test_size

        test_results["loss"] = test_loss

        print(f"""
            Test Loss : {test_results["loss"]}
            Test Precision : {test_results["precision_score"]}
            Test Micro Recall : {test_results["recall_score"]}
            Test Micro F1 : {test_results["f1_score"]}
            Test Accuracy : {test_results["accuracy_score"]}
            """)

        cm = confusion_matrix(test_y_true, test_y_pred)
        cm_path = parent / configs["model"]["output"] / f"confusion_matrix.png"
        plt.imsave(cm_path, cm)
        mlflow.log_artifact(local_path=cm_path, artifact_path="confusion_matrices")

        successful_mail(run.info.run_name, exp_name, model_id, test_results)
        print("INFERENCE DONE")
        return model
    except Exception as e:
        failure_mail(run.info.run_name, exp_name, model_id, e)
        raise e
    finally:
        print("INFERENCE DONE - MLFLOW ENDING")
        mlflow.end_run()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--lr", type=float, default=configs["model"]["hyperparams"]["lr"])
    parser.add_argument("--epochs", type=int, default=configs["model"]["hyperparams"]["epochs"])
    parser.add_argument("--wgt_decay", type=float, default=configs["model"]["hyperparams"]["wgt_decay"])
    args = parser.parse_args()

    hyperparams = {
        "lr": args.lr,
        "epochs": args.epochs,
        "wgt_decay": args.wgt_decay
    }

    train_loader, val_loader, test_loader, tl, vl, sl = (
        load_dataset()
    )

    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

    # experiment = mlflow.get_experiment_by_name("Cats vs Dogs vs Digits")
    # if experiment:
    #     print("Experiment exists")
    #     exp_id = experiment.experiment_id
    # else:
    #     print("Creating new Experiment")
    #     exp_id = mlflow.create_experiment("Cats vs Dogs vs Digits")

    with mlflow.start_run() as parent_run:
        active_experiment = mlflow.get_experiment(mlflow.active_run().info.experiment_id) # type: ignore
        exp_name = active_experiment.name

        try:
            # exp = mlflow.set_experiment(experiment_id=exp_id)

            run_name = f"Train {configs['model']['name']}_{configs['model']['hyperparams']}"
            model = train(
                train_loader,
                val_loader,
                tl,
                vl,
                exp_name,
                run_name,
                hyperparams,
                device,
            )

            run_name = f"Inference {configs['model']['name']}_{configs['model']['hyperparams']}"
            inference(test_loader, sl, model, exp_name, run_name, hyperparams, device)
        except Exception as e:
            print(e)
            raise e
        finally:
            logger.debug("MODEL TRAIN PASS")
