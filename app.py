from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd
import numpy as np
import io
import json

app = Flask(__name__)

df_store = {}

def audit_dataset(df):
    issues = []
    for col in df.columns:
        null_count = int(df[col].isna().sum())
        null_pct = null_count / len(df) * 100
        if null_pct > 0:
            severity = "critical" if null_pct > 40 else "warning"
            if pd.api.types.is_numeric_dtype(df[col]):
                skew = float(df[col].skew())
                if null_pct > 60:
                    strategy = "drop column"
                    reason = "More than 60% nulls — too sparse to impute reliably."
                elif abs(skew) > 1:
                    strategy = "fill with median"
                    reason = f"Skew = {skew:.2f} — data is skewed, median is more robust than mean."
                else:
                    strategy = "fill with mean"
                    reason = f"Skew = {skew:.2f} — data is symmetric, mean is appropriate."
            else:
                strategy = "drop column" if null_pct > 60 else "fill with mode"
                reason = "More than 60% nulls — too sparse." if null_pct > 60 else "Categorical column — mode is correct fill strategy."
            issues.append({"col": col, "type": "null", "severity": severity,
                           "detail": f"{null_count} nulls ({null_pct:.1f}%)",
                           "strategy": strategy, "reason": reason})

    dup_count = int(df.duplicated().sum())
    if dup_count > 0:
        issues.append({"col": "ALL ROWS", "type": "duplicate", "severity": "warning",
                       "detail": f"{dup_count} duplicate rows",
                       "strategy": "drop duplicates",
                       "reason": "Duplicate rows bias model training — always remove."})

    for col in df.select_dtypes(include='number').columns:
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        if IQR == 0:
            continue
        lower = Q1 - 1.5 * IQR
        upper = Q3 + 1.5 * IQR
        outlier_count = int(((df[col] < lower) | (df[col] > upper)).sum())
        outlier_pct = outlier_count / len(df) * 100
        if outlier_count > 0:
            severity = "critical" if outlier_pct > 10 else "warning"
            strategy = "cap outliers (IQR)" if outlier_pct > 10 else "remove outliers"
            reason = f"{outlier_pct:.1f}% outliers — {'capping preserves more data' if outlier_pct > 10 else 'low rate, safe to remove'}."
            issues.append({"col": col, "type": "outlier", "severity": severity,
                           "detail": f"{outlier_count} outliers ({outlier_pct:.1f}%)",
                           "strategy": strategy, "reason": reason})

    for col in df.columns:
        if df[col].nunique() <= 1:
            issues.append({"col": col, "type": "constant", "severity": "warning",
                           "detail": "Only 1 unique value — zero variance",
                           "strategy": "drop column",
                           "reason": "Constant columns provide no signal to any model."})
    return issues


def apply_fixes(df, issues, selected_cols):
    df = df.copy()
    applied = []
    for issue in issues:
        col = issue["col"]
        key = "ALL ROWS" if issue["type"] == "duplicate" else col
        if key not in selected_cols:
            continue
        strategy = issue["strategy"]
        if issue["type"] == "null":
            if col not in df.columns:
                continue
            if strategy == "fill with mean":
                val = round(float(df[col].mean()), 4)
                df[col] = df[col].fillna(val)
                applied.append(f"'{col}': filled nulls with mean ({val})")
            elif strategy == "fill with median":
                val = round(float(df[col].median()), 4)
                df[col] = df[col].fillna(val)
                applied.append(f"'{col}': filled nulls with median ({val})")
            elif strategy == "fill with mode":
                val = df[col].mode()[0]
                df[col] = df[col].fillna(val)
                applied.append(f"'{col}': filled nulls with mode ({val})")
            elif strategy == "drop column":
                df.drop(columns=[col], inplace=True)
                applied.append(f"'{col}': dropped — {issue['detail']}")
        elif issue["type"] == "duplicate":
            before = len(df)
            df.drop_duplicates(inplace=True)
            applied.append(f"Removed {before - len(df)} duplicate rows")
        elif issue["type"] == "outlier":
            if col not in df.columns:
                continue
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            lower = Q1 - 1.5 * IQR
            upper = Q3 + 1.5 * IQR
            if strategy == "cap outliers (IQR)":
                df[col] = df[col].clip(lower, upper)
                applied.append(f"'{col}': capped outliers to [{lower:.2f}, {upper:.2f}]")
            else:
                before = len(df)
                df = df[(df[col] >= lower) & (df[col] <= upper)]
                applied.append(f"'{col}': removed {before - len(df)} outlier rows")
        elif issue["type"] == "constant":
            if col in df.columns:
                df.drop(columns=[col], inplace=True)
                applied.append(f"'{col}': dropped — zero variance column")
    return df, applied


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload():
    file = request.files.get('file')
    if not file:
        return jsonify({'error': 'No file uploaded'}), 400
    try:
        df = pd.read_csv(file)
        df_store['original'] = df.copy()
        df_store['clean'] = df.copy()
        df_store['applied'] = []

        issues = audit_dataset(df)
        preview = df.head(10).fillna('').to_dict(orient='records')
        columns = list(df.columns)

        numeric_cols = df.select_dtypes(include='number').columns.tolist()
        distributions = {}
        for col in numeric_cols[:6]:
            data = df[col].dropna()
            hist, edges = np.histogram(data, bins=20)
            distributions[col] = {
                'hist': hist.tolist(),
                'edges': [round(float(e), 2) for e in edges.tolist()],
                'skew': round(float(data.skew()), 2),
                'mean': round(float(data.mean()), 2),
                'median': round(float(data.median()), 2)
            }

        corr = {}
        if len(numeric_cols) >= 2:
            corr_matrix = df[numeric_cols].corr().round(2)
            corr = {
                'cols': numeric_cols,
                'matrix': corr_matrix.fillna(0).values.tolist()
            }

        return jsonify({
            'rows': len(df), 'cols': len(df.columns),
            'nulls': int(df.isnull().sum().sum()),
            'null_rate': round(df.isnull().sum().sum() / (len(df) * len(df.columns)) * 100, 1),
            'preview': preview, 'columns': columns,
            'issues': issues, 'distributions': distributions, 'corr': corr
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/apply', methods=['POST'])
def apply():
    selected = request.json.get('selected', [])
    df = df_store.get('original', pd.DataFrame()).copy()
    issues = audit_dataset(df)
    df_fixed, applied = apply_fixes(df, issues, selected)
    df_store['clean'] = df_fixed
    df_store['applied'] = applied

    orig = df_store['original']
    return jsonify({
        'applied': applied,
        'before': {'rows': len(orig), 'cols': len(orig.columns), 'nulls': int(orig.isnull().sum().sum())},
        'after': {'rows': len(df_fixed), 'cols': len(df_fixed.columns), 'nulls': int(df_fixed.isnull().sum().sum())}
    })


@app.route('/download')
def download():
    df = df_store.get('clean', pd.DataFrame())
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    buf.seek(0)
    return send_file(
        io.BytesIO(buf.getvalue().encode()),
        mimetype='text/csv',
        as_attachment=True,
        download_name='dataready_cleaned.csv'
    )


if __name__ == '__main__':
    app.run(debug=True)
