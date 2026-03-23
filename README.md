# DataReady — Smart Data Preprocessing Tool

> Bad data causes bad models. DataReady audits your dataset, explains every quality issue, recommends the right fix based on your data's actual structure, and shows the before/after impact — so your model gets the best possible input.

**Live Demo:** [Add your Render URL here after deploy]

---

## The Problem

Most people preprocess data blindly:
- Fill every null with mean — even when the column is heavily skewed
- Remove all outliers — even when 15% of data is affected and you lose too much
- Keep constant columns — which add zero signal to any model
- Never check correlation — and wonder why the model underperforms

DataReady makes these decisions based on your data's actual statistical structure, not guesswork.

---

## Features

### Core Cleaning
- **Automated data quality audit** — detects nulls, duplicates, outliers, constant columns
- **Smart fix recommendations** — mean vs median vs drop, based on skew and null rate
- **One-click apply** — select which fixes to apply, see before/after instantly
- **Download** cleaned dataset as CSV

### Analysis
- **Data quality score (0–100)** — single number summarising dataset health
- **Distribution plots** — histogram per numeric column with skew value
- **Correlation matrix** — colour-coded, flags highly correlated pairs (multicollinearity warning)
- **Feature importance** — quick Random Forest run showing which columns matter most

### Why Mean vs Median?

| Situation | Fix | Why |
|---|---|---|
| Skew < 1 (symmetric) | Mean | Unbiased for normal distributions |
| Skew > 1 (skewed) | Median | Robust against outlier pull |
| Null rate > 60% | Drop column | Too sparse to impute reliably |
| Categorical column | Mode | Only sensible option |
| Outlier rate > 10% | Cap (IQR) | Preserves more data than removal |
| Outlier rate < 10% | Remove | Low rate, safe to drop |

---

## Tech Stack

- **Backend:** Python, Flask
- **Data:** Pandas, NumPy, Scikit-learn
- **Frontend:** HTML, CSS, Vanilla JavaScript
- **Deploy:** Render (free tier)

---

## Run Locally

```bash
# Clone the repo
git clone https://github.com/BharadwajVarun/dataready.git
cd dataready

# Install dependencies
pip install -r requirements.txt

# Run
python app.py
```

Open `http://127.0.0.1:5000` in your browser.

---

## Deploy on Render (Free)

1. Push this repo to GitHub
2. Go to [render.com](https://render.com) → New → Web Service
3. Connect your GitHub repo
4. Set these fields:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
   - **Instance Type:** Free
5. Click Deploy — live URL in ~3 minutes

---

## Project Structure

```
dataready/
├── app.py                  # Flask backend — audit, fix, analysis logic
├── requirements.txt        # Dependencies
├── README.md
└── templates/
    └── index.html          # Frontend — single page app
```

---

## Background

Originally built as a desktop Tkinter tool during an IBM-collaborated AI/ML internship at Rooman Technologies — applied on a 3,000+ record genomic dataset where data quality issues were caught before training that would have reduced model precision by 18%.

Rebuilt as a full-stack web application with smart fix recommendations, visual analysis, and feature importance.

---

## Requirements

```
flask
pandas
numpy
scikit-learn
gunicorn
```

---

Built by [Varun Bharadwaj](https://portfolio-pi-swart-tuos89wqp3.vercel.app/) · [GitHub](https://github.com/BharadwajVarun) · [LinkedIn](https://www.linkedin.com/in/varun-bharadwaj-21b163289/)
