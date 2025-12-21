import numpy as np


import numpy as np


class AdaptiveMovingAverage:
    def __init__(self, size, alpha_slow=0.01, alpha_fast=0.1):
        """
        Initialize adaptive exponential moving average
        
        Args:
            size: Number of data points in each sample
            alpha_slow: Learning rate when new value > current average (default 0.01)
            alpha_fast: Learning rate when new value < current average (default 0.1)
        """
        self.size = size
        self.alpha_slow = alpha_slow
        self.alpha_fast = alpha_fast
        self.average = np.zeros(size)
        self.initialized = False
    
    def update(self, new_values):
        """
        Update the moving average with new data
        
        Args:
            new_values: numpy array or list of new values (must match size)
        
        Returns:
            Updated average as numpy array
        """
        if len(new_values) != self.size:
            raise ValueError(f"Expected {self.size} values, got {len(new_values)}")
        
        new_array = np.array(new_values)
        
        if not self.initialized:
            # First update - initialize with the first values
            self.average = new_array.copy()
            self.initialized = True
        else:
            # Update each point with adaptive alpha
            for i in range(self.size):
                if new_array[i] < self.average[i]:
                    # Signal below average - use fast alpha
                    alpha = self.alpha_fast
                else:
                    # Signal above average - use slow alpha
                    alpha = self.alpha_slow
                
                # Update exponential moving average
                self.average[i] = alpha * new_array[i] + (1 - alpha) * self.average[i]
        
        return self.average.copy()
    
    def get_average(self):
        """Get current average without updating"""
        return self.average.copy()
    
    def reset(self):
        """Reset the average to zeros"""
        self.average.fill(0)
        self.initialized = False
    
    def set_alphas(self, alpha_slow=None, alpha_fast=None):
        """Update alpha values"""
        if alpha_slow is not None:
            self.alpha_slow = alpha_slow
        if alpha_fast is not None:
            self.alpha_fast = alpha_fast
            
            
            
            
            
            

def compute_fft(samples, sample_interval_us=3):
    """
    Compute FFT of signal samples
    
    Args:
        samples: array-like of signal values
        sample_interval_us: time between samples in microseconds
        
    Returns:
        dict with frequencies and magnitudes (as Python lists)
    """
    n = len(samples)
    
    # Calculate sample rate from interval
    sample_rate = 1e6 / sample_interval_us  # Convert µs to Hz
    
    # Compute FFT
    fft_result = np.fft.fft(samples)
    
    # Get magnitude
    magnitudes = np.abs(fft_result)
    
    # Get frequencies
    frequencies = np.fft.fftfreq(n, d=1/sample_rate)
    
    # Keep only positive frequencies (first half)
    positive_idx = frequencies >= 0
    frequencies = frequencies[positive_idx]
    magnitudes = magnitudes[positive_idx]
    
    # Convert to Python lists for JSON serialization
    return {
        'frequencies': frequencies.tolist(),
        'magnitudes': magnitudes.tolist()
    }
    
 



def normalize_samples(samples, first=0, last=None):
    """
    Extract a subset of samples and normalize to 0-1 range
    
    Args:
        samples: list or array of sample values
        first: first index to include (default 0)
        last: last index to include (default None = end of list)
              Use negative indices to count from end (e.g., -1 = exclude last)
        
    Returns:
        list containing only the extracted subset, normalized to 0-1
    
    Example:
        samples = [100, 200, 500, 1000, 800, 600, 50]  # 7 samples
        normalize_samples(samples, first=1, last=-1)
        # Extracts samples[1:-1] = [200, 500, 1000, 800, 600]
        # Min=200, Max=1000, Range=800
        # Returns [0.0, 0.375, 1.0, 0.75, 0.5]  (5 samples)
    """
    if last is None:
        last = len(samples)
    
    # Extract the subset
    subset = samples[first:last]
    
    if len(subset) == 0:
        return []
    
    # Find min and max
    min_val = min(subset)
    max_val = max(subset)
    val_range = max_val - min_val
    
    # Normalize the subset
    if val_range > 0:
        normalized = [(s - min_val) / val_range for s in subset]
    else:
        # All values are the same
        normalized = [0.5] * len(subset)
    
    return normalized
    
    
    
# Global features dict accessible to all modules
current_features = {
    'total_sum': 0,
    'first_half_sum': 0,
    'second_half_sum': 0,
    'diff': 0,
    'cumulative_total': 0,
    'peak': 0,
    'timestamp': 0,
    'ratio': 0
}
    
def extract_signal_features(samples, start_index=4, end_trim=1):
    """
    Extract shape and strength features from a sample set.
    Updates the global current_features dict directly.
    
    Args:
        samples: list of sample values (typically 25 samples)
        start_index: first index to include (default 6 = skip first 6)
        end_trim: number of samples to trim from end (default 1)
        
    Updates global current_features with:
        - total_sum: sum of all samples in subset
        - first_half_sum: sum of first half of subset
        - second_half_sum: sum of second half of subset
        - diff: first_half_sum - second_half_sum
        
    Example:
        samples = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        extract_signal_features(samples, start_index=2, end_trim=1)
        # Updates current_features with:
        #   'total_sum': 420,
        #   'first_half_sum': 120,
        #   'second_half_sum': 300,
        #   'diff': -180
    """
    global current_features
    
    # Extract subset
    if end_trim > 0:
        subset = samples[start_index:-end_trim]
    else:
        subset = samples[start_index:]
    
    if len(subset) == 0:
        current_features.update({
            'total_sum': 0,
            'first_half_sum': 0,
            'second_half_sum': 0,
            'diff': 0
        })
        return
    
    # Calculate total sum
    total_sum = sum(subset)
    
    # Split into halves
    mid_point = len(subset) // 2
    first_half = subset[:10]
    second_half = subset[-6:]
    
    # Calculate half sums
    first_half_sum = sum(first_half) / 10
    second_half_sum = sum(second_half) / 6
    diff1 = first_half_sum - second_half_sum
    
    # Update global features dict directly
    current_features.update({
        'total_sum': total_sum,
        'first_half_sum': first_half_sum,
        'second_half_sum': second_half_sum,
        'diff': diff1
    })
    

def force_two_digit(value):
    """Force any value to 2-digit string '00'-'99'."""
    try:
        # Convert to int, clamp to 0-99, pad with zero
        num = int(float(value))
        num = max(0, min(99, num))
        return f"{num:02d}"  # Same as str(num).zfill(2)
    except (ValueError, TypeError):
        return "00"  # Default on error
        
        
    
def update_peak_tracker(key='diff'):
    """Updates cumulative_total and peak directly in current_features."""
    global current_features
    current = current_features[key]
    
    play_conductivity = False
    getratio = 0;
    
    # Reset condition: diff fell below zero
    if current < 0:
        if(current_features['peak'] > 10):
            play_conductivity = True
            getratio = current_features['ratio'] 
            getratio *= 100
            
        current_features['cumulative_total'] = 0
        current_features['peak'] = max(current, 0)  # or just 0
        
        if(play_conductivity):                    
            num = force_two_digit(getratio)           
            return ('play', num)
            
    
    # Positive diff - accumulate
    current_features['cumulative_total'] += current
    
    # Update peak if we have a new maximum
    if current > current_features['peak']:
        current_features['peak'] = current
        
        # update the condutctivity ratio        
        if current_features['first_half_sum'] != 0:
            current_features['ratio'] = current_features['second_half_sum'] / current_features['first_half_sum']
        else:
            current_features['ratio'] = 0
    
    return False  # No reset/trigger
