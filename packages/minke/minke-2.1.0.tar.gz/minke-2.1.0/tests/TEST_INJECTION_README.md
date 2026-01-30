# Injection Module Tests

This file contains comprehensive tests for the SNR-based injection functionality in `minke.injection`.

## Test Overview

The test suite is organized into three main test classes:

### 1. TestSNRCalculations

Tests for the network SNR calculation and distance-finding functions.

**Tests included:**
- `test_calculate_network_snr_for_distance`: Verifies that network SNR calculation returns positive values
- `test_network_snr_decreases_with_distance`: Ensures SNR decreases as distance increases
- `test_network_snr_scales_inversely_with_distance`: Validates that SNR ≈ 1/distance relationship
- `test_find_distance_for_network_snr`: Tests finding the correct distance for a target SNR
- `test_find_distance_for_high_snr`: Verifies that high SNR requires close distances
- `test_find_distance_for_low_snr`: Verifies that low SNR allows larger distances

**Key functionality tested:**
- `calculate_network_snr_for_distance()`: Calculates network SNR across multiple detectors
- `find_distance_for_network_snr()`: Uses root-finding to determine luminosity distance for target SNR

### 2. TestMakeInjection

Tests for the main injection creation function with both distance-based and SNR-based modes.

**Tests included:**
- `test_make_injection_with_distance`: Creates injection with specified luminosity distance
- `test_make_injection_with_snr`: Creates injection with target network SNR (automatically finds distance)
- `test_make_injection_with_custom_times`: Tests injection creation with custom time arrays
- `test_make_injection_single_detector`: Verifies single-detector injection creation

**Key functionality tested:**
- SNR-based injection mode (via `snr` parameter)
- Traditional distance-based injection mode
- Multi-detector injection creation
- Proper frame lengths and data structure

### 3. TestInjectionParametersAddUnits

Tests for the unit handling utility function.

**Tests included:**
- `test_add_units_to_masses`: Adds solar mass units to m1, m2
- `test_add_units_to_distance`: Adds megaparsec units to luminosity_distance
- `test_preserve_existing_units`: Ensures pre-existing units are not modified
- `test_parameters_without_units`: Verifies dimensionless parameters remain unchanged
- `test_mixed_parameters`: Tests handling of mixed parameter sets

**Key functionality tested:**
- `injection_parameters_add_units()`: Automatically adds astropy units to physical parameters

## Running the Tests

### Using unittest

```bash
cd /home/daniel/repositories/ligo/minke
python -m unittest tests.test_injection -v
```

### Running specific test classes

```bash
# Test only SNR calculations
python -m unittest tests.test_injection.TestSNRCalculations -v

# Test only injection creation
python -m unittest tests.test_injection.TestMakeInjection -v

# Test only parameter unit handling
python -m unittest tests.test_injection.TestInjectionParametersAddUnits -v
```

### Running specific tests

```bash
python -m unittest tests.test_injection.TestSNRCalculations.test_find_distance_for_network_snr -v
```

## Test Configuration

The tests use realistic LIGO detector configurations:
- **Detectors**: H1 (Hanford), L1 (Livingston)
- **PSD Model**: aLIGOZeroDetHighPower (Advanced LIGO design sensitivity)
- **Waveform**: IMRPhenomXPHM (phenomenological BBH waveform)
- **Sample Rate**: 4096 Hz
- **Duration**: 4 seconds
- **Masses**: 30 + 30 solar masses (default test case)

## Dependency Handling

The tests are wrapped in `@unittest.skipIf` decorators to gracefully handle missing dependencies (e.g., torch, LALSuite). If required modules are not available, tests will be skipped rather than failing.

## What the Tests Validate

### Physics Validation
1. **SNR scales inversely with distance**: SNR ∝ 1/distance
2. **Network SNR is quadrature sum**: SNR_net = √(SNR_H1² + SNR_L1²)
3. **Root finding converges**: The distance finder reliably finds the correct distance within tolerance

### Software Validation
1. **Correct data structures**: Generated injections have proper lengths and channel names
2. **Unit handling**: Physical parameters correctly carry astropy units
3. **Multi-detector support**: Injections can be created for multiple detectors simultaneously
4. **Flexible input**: Supports both distance-based and SNR-based injection modes

## Example: How the SNR Mode Works

When a user specifies `snr: 20` in the parameters instead of `luminosity_distance: 100`:

1. `make_injection()` detects the `snr` parameter
2. Calls `find_distance_for_network_snr()` with target SNR = 20
3. Root finder searches between 10-10000 Mpc using Brent's method
4. For each trial distance, `calculate_network_snr_for_distance()`:
   - Generates the waveform at that distance
   - Projects onto each detector
   - Calculates SNR for each detector
   - Returns network SNR = √(ΣSNRᵢ²)
5. Finds distance where network SNR = 20 (within tolerance)
6. Uses that distance for all subsequent injections

This ensures consistent network SNR across different source orientations and detector configurations.
