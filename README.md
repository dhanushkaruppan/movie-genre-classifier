# 🎬 Movie Genre Classifier

[![TensorFlow](https://img.shields.io/badge/TensorFlow-%23FF6F00.svg?style=for-the-badge&logo=TensorFlow&logoColor=white)](https://www.tensorflow.org/)
[![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)](https://www.python.org/)

A robust, production-grade Deep Learning pipeline for classifying movie posters into 6 genres: Action, Comedy, Drama, Horror, Romance, and Sci-Fi. 

This project leverages a transfer-learning approach using **EfficientNetV2S** combined with a custom classification head. It also features a custom data collection script using Selenium to scrape high-resolution posters directly from IMDb.

## ✨ Features

- **Automated Data Scraping:** Includes a robust Selenium script to extract high-resolution posters from IMDb without duplicates.
- **State-of-the-Art Architecture:** Utilizes **EfficientNetV2S** (pre-trained on ImageNet) to extract high-level visual features efficiently.
- **Robust Training Pipeline:** Features mixed precision training, automatic class weighting for imbalanced datasets, and a custom WarmUpCosineDecay Learning Rate schedule.
- **Test-Time Augmentation (TTA):** Employs TTA during inference for highly robust and accurate predictions.
- **Interpretability:** Built-in **Grad-CAM** visualizations to understand which parts of the poster the model looks at when making decisions.

## 📂 Project Structure

```text
├── notebooks/
│   ├── 01_train.ipynb              # Full training pipeline (EfficientNetV2S)
│   └── 02_predict.ipynb            # Prediction and evaluation with TTA
├── scripts/
│   └── scrape_imdb.py              # IMDb scraper for dataset collection
├── tests/
│   ├── test_auth.py                # Tests for authentication
│   └── test_upload.py              # Upload tests
├── requirements.txt                # Python dependencies
└── README.md                       # Project documentation
```

## 🚀 Setup & Installation

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/movie-genre-classifier.git
cd movie-genre-classifier
```

### 2. Install Dependencies
Make sure you have Python 3.8+ installed. It is recommended to use a virtual environment.
```bash
pip install -r requirements.txt
```

*(Note: The Selenium scraper requires you to have Microsoft Edge installed, or you can modify the script to use Chrome).*

## 🧠 Usage

### 1. Collect Data (Optional)
If you want to build your own dataset from scratch, run the scraper:
```bash
python scripts/scrape_imdb.py
```
This will automatically download posters into a `Movie_Posters_IMDb` directory.

### 2. Train the Model
Open `notebooks/01_train.ipynb` in Google Colab or Jupyter Notebook.
The notebook will guide you through:
1. Loading and preprocessing the dataset
2. Training the custom head
3. Fine-tuning the EfficientNetV2S backbone
4. Generating Grad-CAM heatmaps

### 3. Predict on New Posters
Open `notebooks/02_predict.ipynb` to evaluate the model on the test set, or use the interactive prediction cell with **Test-Time Augmentation (TTA)** to test the model on your own uploaded images.

## 📈 Performance
- **Metrics Evaluated:** Accuracy, Top-3 Accuracy, Loss.
- Model gracefully handles class imbalances through adaptive class weights.
- Test-Time Augmentation ensures confident predictions even with cropped or poorly-lit posters.

## 📝 License
This project is for educational and research purposes. Data scraped via IMDb belongs to its respective owners.
