[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/TkkthH7J)

Name: Pranav Rao<br>
Roll: DA25M022

# MLFlow Sprint

This assignment was a 48-hour sprint for training a Image Classifier between Cats vs Dogs vs Digits

## Dataset used
1. MNIST Dataset for Digits
2. [Cats vs Dogs](https://www.kaggle.com/datasets/bhavikjikadara/dog-and-cat-classification-dataset)

No of classes - 12

## Model Used
ResNet-50 (Default weights)

## Metrics
1. F1
2. Precision
3. Recall
4. Accuracy

## How to run the repo

### To run an experiment
1. Modify the ```MLProject``` file for the hyperparams
2. Run:
```
mlflow run . --experiment-name=<exp_name>
```

## To view the runs:
```
mlflow ui
```

## To run the application:
```
./run.sh
```

## Directory structure
```
.
├── A7.pdf
├── conda.yaml
├── config.yaml
├── mlflow.db
├── MLProject
├── mlruns
├── model
│   ├── v1
│   │   └── resnet50_v1_best.pt
│   └── v2
│       └── resnet50_v2_best.pt
├── output
│   ├── v1
│   │   ├── confusion_matrix0.png
│   │   ├── confusion_matrix1.png
│   │   ├── confusion_matrix2.png
│   │   ├── confusion_matrix3.png
│   │   ├── confusion_matrix4.png
│   │   ├── confusion_matrix5.png
│   │   ├── confusion_matrix6.png
│   │   ├── confusion_matrix7.png
│   │   ├── confusion_matrix8.png
│   │   ├── confusion_matrix9.png
│   │   ├── confusion_matrix.png
│   │   └── test_confusion_matrix.png
│   └── v2
│       ├── confusion_matrix0.png
│       └── confusion_matrix.png
├── Procfile
├── prog_log.log
├── progress.md
├── README.md
├── requirements.txt
├── run.sh
├── src
│   ├── app.py
│   ├── inference.py
│   ├── train.py
│   └── utils
│       ├── load.py
│       ├── mail.py
├── test.ipynb
└── tree.md

74 directories, 107 files
```
74 directories, 107 files
