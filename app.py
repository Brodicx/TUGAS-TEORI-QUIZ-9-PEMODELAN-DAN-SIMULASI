from flask import Flask, render_template, request, jsonify
import pandas as pd
import numpy as np
from monte_carlo import MonteCarloPredictor
import os

app = Flask(__name__)

# Load dataset
DATASET_PATH = 'dataset_hiv.csv'

def load_data():
    """Load dan prepare data dari CSV"""
    try:
        df = pd.read_csv(DATASET_PATH)
        return df
    except Exception as e:
        print(f"Error loading data: {e}")
        return None

@app.route('/')
def index():
    """Halaman utama"""
    return render_template('index.html')

@app.route('/api/data')
def get_data():
    """API endpoint untuk mendapatkan data historis"""
    df = load_data()
    if df is None:
        return jsonify({'error': 'Data tidak dapat dimuat'}), 500
    
    # Group by tahun untuk mendapatkan total kasus per tahun
    yearly_data = df.groupby('tahun')['jumlah_kasus'].sum().reset_index()
    yearly_data.columns = ['tahun', 'total_kasus']
    
    # Data per kabupaten/kota
    location_data = df.groupby(['nama_kabupaten_kota', 'tahun'])['jumlah_kasus'].sum().reset_index()
    
    return jsonify({
        'yearly': yearly_data.to_dict('records'),
        'locations': location_data.to_dict('records'),
        'locations_list': sorted(df['nama_kabupaten_kota'].unique().tolist())
    })

@app.route('/api/predict', methods=['POST'])
def predict():
    """API endpoint untuk prediksi menggunakan Monte Carlo"""
    try:
        data = request.json
        location = data.get('location', 'all')
        years_ahead = int(data.get('years_ahead', 1))
        simulations = int(data.get('simulations', 10000))
        
        df = load_data()
        if df is None:
            return jsonify({'error': 'Data tidak dapat dimuat'}), 500
        
        # Filter data berdasarkan lokasi
        if location != 'all':
            df_filtered = df[df['nama_kabupaten_kota'] == location].copy()
        else:
            df_filtered = df.groupby('tahun')['jumlah_kasus'].sum().reset_index()
            df_filtered['nama_kabupaten_kota'] = 'SEMUA LOKASI'
        
        # Group by tahun
        if location != 'all':
            yearly_data = df_filtered.groupby('tahun')['jumlah_kasus'].sum().reset_index()
        else:
            yearly_data = df_filtered[['tahun', 'jumlah_kasus']].copy()
        
        yearly_data = yearly_data.sort_values('tahun')
        
        # Siapkan data untuk response
        historical_years = yearly_data['tahun'].tolist()
        historical_values = yearly_data['jumlah_kasus'].tolist()
        
        # Prediksi dimulai dari tahun 2025
        start_year = 2025
        last_year = historical_years[-1]
        
        # Hitung total periode yang perlu diprediksi (dari tahun terakhir ke 2025 + years_ahead)
        years_to_2025 = max(0, start_year - last_year)
        total_periods = years_to_2025 + years_ahead
        
        # Inisialisasi predictor
        predictor = MonteCarloPredictor(yearly_data['jumlah_kasus'].values, simulations)
        
        # Lakukan prediksi untuk semua periode (dari tahun terakhir ke 2025 + years_ahead)
        predictions = predictor.predict(total_periods)
        
        # Ambil hanya prediksi mulai dari tahun 2025
        if years_to_2025 > 0:
            # Jika perlu prediksi ke 2025, ambil prediksi mulai dari index years_to_2025
            predictions_from_2025 = {
                'mean': predictions['mean'][years_to_2025:],
                'median': predictions['median'][years_to_2025:],
                'std': predictions['std'][years_to_2025:],
                'min': predictions['min'][years_to_2025:],
                'max': predictions['max'][years_to_2025:],
                'p5': predictions['p5'][years_to_2025:],
                'p25': predictions['p25'][years_to_2025:],
                'p75': predictions['p75'][years_to_2025:],
                'p95': predictions['p95'][years_to_2025:]
            }
        else:
            # Jika tahun terakhir >= 2025, gunakan semua prediksi
            predictions_from_2025 = predictions
        
        # Generate tahun prediksi mulai dari 2025
        predicted_years = list(range(start_year, start_year + years_ahead))
        
        return jsonify({
            'success': True,
            'location': location,
            'historical': {
                'years': historical_years,
                'values': historical_values
            },
            'predictions': {
                'years': predicted_years,
                'mean': predictions_from_2025['mean'].tolist(),
                'median': predictions_from_2025['median'].tolist(),
                'std': predictions_from_2025['std'].tolist(),
                'min': predictions_from_2025['min'].tolist(),
                'max': predictions_from_2025['max'].tolist(),
                'percentiles': {
                    'p5': predictions_from_2025['p5'].tolist(),
                    'p25': predictions_from_2025['p25'].tolist(),
                    'p75': predictions_from_2025['p75'].tolist(),
                    'p95': predictions_from_2025['p95'].tolist()
                }
            },
            'statistics': {
                'mean_growth_rate': float(predictor.mean_growth_rate),
                'std_growth_rate': float(predictor.std_growth_rate)
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

