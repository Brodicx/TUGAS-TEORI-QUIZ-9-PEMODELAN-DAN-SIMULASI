import numpy as np

class MonteCarloPredictor:
    """
    Kelas untuk melakukan prediksi menggunakan algoritma Monte Carlo
    Berdasarkan data historis dengan asumsi distribusi normal untuk pertumbuhan
    """
    
    def __init__(self, historical_data, n_simulations=10000):
        """
        Inisialisasi predictor
        
        Parameters:
        -----------
        historical_data : array-like
            Data historis (jumlah kasus per periode)
        n_simulations : int
            Jumlah simulasi Monte Carlo (default: 10000)
        """
        self.historical_data = np.array(historical_data)
        self.n_simulations = n_simulations
        self.mean_growth_rate = 0
        self.std_growth_rate = 0
        
        # Hitung growth rate dari data historis
        self._calculate_growth_rates()
    
    def _calculate_growth_rates(self):
        """Menghitung growth rate dari data historis"""
        if len(self.historical_data) < 2:
            self.mean_growth_rate = 0
            self.std_growth_rate = 0
            return
        
        # Hitung growth rate (persentase perubahan)
        growth_rates = []
        for i in range(1, len(self.historical_data)):
            if self.historical_data[i-1] > 0:
                growth_rate = (self.historical_data[i] - self.historical_data[i-1]) / self.historical_data[i-1]
                growth_rates.append(growth_rate)
        
        if len(growth_rates) > 0:
            self.mean_growth_rate = np.mean(growth_rates)
            self.std_growth_rate = np.std(growth_rates)
        else:
            self.mean_growth_rate = 0
            self.std_growth_rate = 0
    
    def predict(self, n_periods=1):
        """
        Melakukan prediksi untuk n periode ke depan
        
        Parameters:
        -----------
        n_periods : int
            Jumlah periode yang akan diprediksi (default: 1)
        
        Returns:
        --------
        dict : Dictionary berisi statistik prediksi
        """
        if len(self.historical_data) == 0:
            return {
                'mean': np.zeros(n_periods),
                'median': np.zeros(n_periods),
                'std': np.zeros(n_periods),
                'min': np.zeros(n_periods),
                'max': np.zeros(n_periods),
                'p5': np.zeros(n_periods),
                'p25': np.zeros(n_periods),
                'p75': np.zeros(n_periods),
                'p95': np.zeros(n_periods)
            }
        
        last_value = self.historical_data[-1]
        predictions = np.zeros((self.n_simulations, n_periods))
        
        # Simulasi Monte Carlo
        for sim in range(self.n_simulations):
            current_value = last_value
            for period in range(n_periods):
                # Generate random growth rate dari distribusi normal
                if self.std_growth_rate > 0:
                    growth_rate = np.random.normal(self.mean_growth_rate, self.std_growth_rate)
                else:
                    growth_rate = self.mean_growth_rate
                
                # Hitung nilai baru
                new_value = current_value * (1 + growth_rate)
                
                # Pastikan nilai tidak negatif
                new_value = max(0, new_value)
                
                predictions[sim, period] = new_value
                current_value = new_value
        
        # Hitung statistik dari semua simulasi
        result = {
            'mean': np.mean(predictions, axis=0),
            'median': np.median(predictions, axis=0),
            'std': np.std(predictions, axis=0),
            'min': np.min(predictions, axis=0),
            'max': np.max(predictions, axis=0),
            'p5': np.percentile(predictions, 5, axis=0),
            'p25': np.percentile(predictions, 25, axis=0),
            'p75': np.percentile(predictions, 75, axis=0),
            'p95': np.percentile(predictions, 95, axis=0)
        }
        
        return result

