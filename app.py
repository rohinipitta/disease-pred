from flask import Flask, render_template, request, send_file, url_for
import pandas as pd
from fpdf import FPDF
from flask import Flask, request, jsonify
import os

app = Flask(__name__)

# Load datasets
df = pd.read_csv("datasets/diseases.csv")
hospital_data = pd.read_csv("datasets/maps-links.csv")

# Get unique symptoms
symptoms = set(df['Symptom1']).union(set(df['Symptom2'])).union(set(df['Symptom3']))

@app.route('/', methods=['GET', 'POST'])
def index():
    disease = None
    details = None
    if request.method == 'POST':
        symptom1 = request.form.get('symptom1')
        symptom2 = request.form.get('symptom2')
        symptom3 = request.form.get('symptom3')
        
        # Find disease based on symptoms
        match = df[
            (df['Symptom1'] == symptom1) | (df['Symptom2'] == symptom1) | (df['Symptom3'] == symptom1)
        ]
        match = match[
            (match['Symptom1'] == symptom2) | (match['Symptom2'] == symptom2) | (match['Symptom3'] == symptom2)
        ]
        match = match[
            (match['Symptom1'] == symptom3) | (match['Symptom2'] == symptom3) | (match['Symptom3'] == symptom3)
        ]
        
        if not match.empty:
            disease = match.iloc[0]['Disease']
            details = {
                'Precautions': match.iloc[0]['Precautions'],
                'Medications': match.iloc[0]['Medications'],
                'Tests': match.iloc[0]['Tests'],
                'Causes': match.iloc[0]['Causes']
            }
    
    return render_template('index.html', symptoms_list=sorted(symptoms), disease=disease, details=details)

@app.route("/download_report")
def download_report():
    disease = request.args.get("disease", "Unknown Disease")
    details = {
        'Precautions': request.args.get("precautions", "N/A"),
        'Medications': request.args.get("medications", "N/A"),
        'Tests': request.args.get("tests", "N/A"),
        'Causes': request.args.get("causes", "N/A")
    }

    filename = generate_pdf_report(disease, details)
    return send_file(filename, as_attachment=True)

def generate_pdf_report(disease, details):
    filename = "medical_report.pdf"
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, "Medical Report", ln=True, align="C")

    pdf.set_font("Arial", "B", 12)
    pdf.cell(200, 10, f"Disease: {disease.capitalize()}", ln=True, align="L")

    pdf.set_font("Arial", "", 12)
    for key, value in details.items():
        pdf.multi_cell(0, 10, f"{key}: {value}")

    pdf.output(filename)
    return filename
@app.route('/find_hospitals/<disease>', methods=['GET', 'POST'])
def find_hospitals(disease):
    df = pd.read_csv('datasets/maps-links.csv')  # Load the dataset

    # Ensure 'Disease' column exists and filter based on the disease
    if 'Disease' in df.columns:
        disease_df = df[df['Disease'].str.lower() == disease.lower()]
    else:
        return "Error: 'Disease' column not found in CSV file", 500

    # Get unique states related to the disease
    states = disease_df['State'].dropna().unique().tolist()

    districts = []
    hospitals = []

    selected_state = request.form.get('state')
    selected_district = request.form.get('district')

    if selected_state:
        # Get districts in the selected state
        districts = disease_df[disease_df['State'] == selected_state]['District'].dropna().unique().tolist()

    if selected_district:
        # Filter hospitals in the selected district
        filtered_df = disease_df[(disease_df['State'] == selected_state) & (disease_df['District'] == selected_district)]
        hospitals = [
        {
            "Hospital Name": f"Hospital {i+1}",
            "Google Maps Links": [row['map1'], row['map2'], row['map3']]
        }
        for i, row in filtered_df.iterrows()
    ]

    return render_template(
        '/find_hospitals.html',
        states=states,
        districts=districts,
        hospitals=hospitals,
        disease=disease
    )


tokens={}
@app.route("/register", methods=["POST"])
def register():
    name = request.form.get("name")
    phone = request.form.get("phone")

    if not name or not phone:
        return jsonify({"error": "Missing details"}), 400

    token_number = len(tokens) + 1
    tokens[token_number] = {"name": name, "phone": phone}

    return jsonify({"token": token_number})

if __name__ == "__main__":
    app.run(debug=True)
