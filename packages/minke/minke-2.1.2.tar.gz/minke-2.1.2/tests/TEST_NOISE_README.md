# Test Suite for minke.noise Module

## Overview
Comprehensive unit tests have been created in `/home/daniel/repositories/ligo/minke/tests/test_noise.py` for the `minke.noise` module.

## Test Structure

The test suite is organized into 4 main test classes:

### 1. TestLALSimulationPSD
Tests for the core `LALSimulationPSD` class functionality:

#### Basic Functionality Tests:
- `test_initialization`: Verifies PSD objects can be created
- `test_frequency_domain_default_parameters`: Tests default PSD generation
- `test_frequency_domain_custom_parameters`: Tests custom frequency ranges and spacing
- `test_frequency_domain_custom_frequencies`: Tests with custom frequency arrays
- `test_twocolumn_format`: Validates two-column output format
- `test_covariance_matrix_shape`: Checks covariance matrix dimensions
- `test_covariance_matrix_symmetry`: Verifies matrix symmetry property
- `test_time_domain`: Tests time-domain representation

#### Time Series Generation Tests:
- `test_time_series_with_times`: Tests explicit time array input
- `test_time_series_with_duration_and_sample_rate`: Tests duration/rate parameters
- `test_time_series_epoch`: Validates custom epoch handling
- `test_time_series_data_properties`: Checks statistical properties (real, finite, zero-mean)

#### PSD Verification Tests (Key Feature):
- `test_generated_noise_psd_matches_input_psd_long_duration`:
  * Uses Welch's method to estimate PSD of generated noise
  * Compares with theoretical input PSD
  * Validates match within 30% in sensitive frequency band (20-500 Hz)
  * Uses 64-second duration for good frequency resolution

- `test_generated_noise_psd_matches_input_psd_multiple_realizations`:
  * Generates multiple noise realizations
  * Averages PSD estimates to reduce statistical fluctuations
  * Validates tighter agreement (within 20%) due to averaging

- `test_noise_psd_shape_in_frequency_domain`: 
  * Verifies FFT output dimensions match PSD

- `test_multiple_noise_realizations_different`:
  * Confirms stochastic nature of noise generation
  * Validates similar statistical properties across realizations

### 2. TestAdvancedLIGO
Tests specific to Advanced LIGO detector PSD:
- `test_initialization`: Verifies AdvancedLIGO PSD creation
- `test_frequency_domain_aLIGO`: Validates aLIGO-specific properties (sensitivity curve shape)
- `test_aLIGO_alias`: Confirms AdvancedLIGO and AdvancedLIGODesignSensitivity2018 are equivalent

### 3. TestKnownPSDs
Tests for the PSD registry:
- `test_known_psds_contains_advanced_ligo`: Checks registry contents
- `test_known_psds_can_instantiate`: Validates all registered PSDs can be instantiated

### 4. TestBilbyComparison (Key Feature)
Conditional tests that run only if bilby is installed:

- `test_noise_mean_comparison_with_bilby`:
  * Generates noise using both minke and bilby with same PSD
  * Verifies both have mean ≈ 0
  * Confirms difference in means is negligible

- `test_noise_variance_comparison_with_bilby`:
  * Compares variance of noise from minke vs bilby
  * Uses multiple realizations for better statistics
  * Validates relative difference is within 50%

## Key Testing Methodology

### PSD Verification Approach
1. Generate time-series noise using the minke PSD generator
2. Apply Welch's method (scipy.signal.welch) to estimate PSD from time series
3. Compare estimated PSD with theoretical input PSD
4. Validate match in sensitive frequency bands

### Statistical Validation
- Uses long durations (64s) for good frequency resolution
- Employs multiple realizations to reduce statistical fluctuations
- Focuses on relative differences in sensitive frequency bands
- Allows for reasonable statistical tolerance (20-30%)

### Bilby Comparison
- Creates bilby PSD object from minke PSD values
- Generates noise from both systems with identical PSDs
- Compares first and second moments (mean and variance)
- Ensures consistent noise generation between frameworks

## Running the Tests

```bash
# Run all noise tests
python -m unittest tests.test_noise -v

# Run specific test class
python -m unittest tests.test_noise.TestLALSimulationPSD -v

# Run specific test
python -m unittest tests.test_noise.TestLALSimulationPSD.test_generated_noise_psd_matches_input_psd_long_duration -v
```

## Dependencies Required
- numpy
- scipy (for signal.welch PSD estimation)
- torch
- lal, lalsimulation
- gwpy
- bilby (optional, for comparison tests)

## Test Coverage
The test suite covers:
- ✅ All public methods of LALSimulationPSD
- ✅ PSD generation in frequency domain
- ✅ Time series noise generation
- ✅ Covariance matrix computation
- ✅ PSD verification through Welch's method
- ✅ Statistical properties validation
- ✅ Bilby compatibility (when available)
- ✅ Edge cases (custom epochs, different durations/sample rates)

## Expected Test Results
When all dependencies are installed:
- Most tests should pass
- PSD matching tests may show some statistical variation
- Bilby comparison tests will be skipped if bilby is not installed
- Tests validate both correctness and numerical accuracy
