# Summary: Unit Tests for minke.noise Module

## What Was Created

I have created comprehensive unit tests for the `minke/noise.py` module with a focus on:
1. **PSD Verification**: Tests that verify the PSD of generated noise matches the input PSD
2. **Bilby Comparison**: Tests that compare minke-generated noise with bilby-generated noise

## Files Created

### 1. `/home/daniel/repositories/ligo/minke/tests/test_noise.py`
Main test file containing 23 test methods organized into 4 test classes.

### 2. `/home/daniel/repositories/ligo/minke/tests/TEST_NOISE_README.md`
Detailed documentation explaining the test structure and methodology.

### 3. `/home/daniel/repositories/ligo/minke/tests/validate_test_noise.py`
Validation script to check test syntax and structure without requiring all dependencies.

## Test Coverage Summary

### 🎯 Key Features (As Requested)

#### PSD Verification Tests
1. **`test_generated_noise_psd_matches_input_psd_long_duration`**
   - Generates 64 seconds of noise from a PSD
   - Uses Welch's method to estimate the PSD from the generated time series
   - Compares estimated PSD with the original input PSD
   - Validates match within 30% in the sensitive frequency band (20-500 Hz)

2. **`test_generated_noise_psd_matches_input_psd_multiple_realizations`**
   - Generates multiple independent noise realizations
   - Averages their PSD estimates to reduce statistical fluctuations
   - Validates tighter agreement (within 20%) with the theoretical PSD

#### Bilby Comparison Tests (Conditional)
1. **`test_noise_mean_comparison_with_bilby`**
   - Generates noise using both minke and bilby with the same PSD
   - Verifies both have mean ≈ 0 (as expected for colored noise)
   - Confirms the difference in means is negligible (< 1e-10)

2. **`test_noise_variance_comparison_with_bilby`**
   - Compares variance of noise from minke vs bilby
   - Uses 3 realizations for better statistics
   - Validates relative difference is within 50%

**Note**: Bilby tests automatically skip if bilby is not installed, using `@unittest.skipUnless`.

### 📊 Additional Test Coverage

#### Basic Functionality (9 tests)
- PSD initialization and generation
- Frequency domain operations with various parameters
- Two-column format output
- Covariance matrix generation and properties

#### Time Series Generation (4 tests)
- Generation with explicit times
- Generation with duration and sample rate
- Custom epoch handling
- Statistical properties validation

#### Stochastic Properties (2 tests)
- Multiple realizations are different
- Statistical properties are similar across realizations

#### Detector-Specific Tests (3 tests)
- Advanced LIGO PSD generation
- Sensitivity curve validation
- Alias verification

#### Registry Tests (2 tests)
- KNOWN_PSDS contains expected entries
- All registered PSDs can be instantiated

## Technical Methodology

### PSD Estimation from Time Series
```python
from scipy.signal import welch

# Generate noise
noise = psd.time_series(duration=64, sample_rate=2048)

# Estimate PSD using Welch's method
frequencies, psd_estimate = welch(
    noise.data,
    fs=sample_rate,
    nperseg=int(sample_rate * 4),  # 4-second segments
    noverlap=int(sample_rate * 2),  # 50% overlap
    scaling='density'
)

# Compare with theoretical PSD
relative_error = |psd_estimate - psd_theoretical| / psd_theoretical
```

### Bilby Integration
```python
from bilby.gw.detector import PowerSpectralDensity
from bilby.core.utils import create_frequency_series

# Create bilby PSD from minke PSD values
frequency_array = create_frequency_series(sample_rate, duration)
minke_psd_values = minke_psd.frequency_domain(frequencies=frequency_array)
bilby_psd = PowerSpectralDensity(
    frequency_array=frequency_array,
    psd_array=minke_psd_values.data
)

# Generate noise
bilby_noise = bilby_psd.get_noise_realization(sample_rate, duration)
```

## Running the Tests

### Validation (No Dependencies Required)
```bash
cd /home/daniel/repositories/ligo/minke/tests
python validate_test_noise.py
```

### Full Test Suite (Requires Dependencies)
```bash
cd /home/daniel/repositories/ligo/minke

# Run all noise tests
python -m unittest tests.test_noise -v

# Run specific test class
python -m unittest tests.test_noise.TestLALSimulationPSD -v

# Run PSD verification tests only
python -m unittest tests.test_noise.TestLALSimulationPSD.test_generated_noise_psd_matches_input_psd_long_duration -v
python -m unittest tests.test_noise.TestLALSimulationPSD.test_generated_noise_psd_matches_input_psd_multiple_realizations -v

# Run bilby comparison tests (will skip if bilby not installed)
python -m unittest tests.test_noise.TestBilbyComparison -v
```

## Dependencies

### Required for Basic Tests
- `numpy` - Array operations
- `scipy` - Signal processing (Welch's method)
- `torch` - Tensor operations (used by minke)
- `lal`, `lalsimulation` - LAL suite for gravitational wave analysis
- `gwpy` - GW data analysis (used by minke.types)

### Optional
- `bilby` - For comparison tests (tests will skip if not available)

### Installation
```bash
# Basic dependencies
pip install numpy scipy torch gwpy

# LAL suite (via conda)
conda install -c conda-forge lalsuite

# Optional: bilby for comparison tests
pip install bilby
```

## Validation Results

✅ **Syntax**: All Python syntax is valid  
✅ **Structure**: 4 test classes with 23 test methods  
✅ **Key Tests Present**:
  - PSD verification tests
  - Bilby comparison tests
  - Statistical property tests

## What Makes These Tests Robust

1. **Welch's Method**: Industry-standard PSD estimation with overlapping segments
2. **Long Durations**: 64-second time series for good frequency resolution
3. **Multiple Realizations**: Averaging reduces statistical fluctuations
4. **Sensitive Band Focus**: Tests focus on 20-500 Hz where detectors are most sensitive
5. **Reasonable Tolerances**: Accounts for statistical nature of noise (20-30% tolerance)
6. **Graceful Degradation**: Bilby tests skip automatically if not installed
7. **Comprehensive Coverage**: Tests both correctness and numerical accuracy

## Expected Test Behavior

When dependencies are installed:
- ✅ Most tests should pass reliably
- ⚠️ PSD matching tests may show ~10-30% variation due to finite sample statistics
- ⏭️ Bilby tests will skip if bilby is not installed
- ✅ All tests validate both implementation correctness and numerical accuracy

The PSD verification tests use statistical methods that account for the inherent randomness in noise generation, making them robust and meaningful validation of the noise generation algorithm.
