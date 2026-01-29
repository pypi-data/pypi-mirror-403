"""
Linear Background Subtraction Script for PL Data

This script performs linear background subtraction on photoluminescence (PL) data.
The background is estimated by fitting a line between two energy points (2.3 eV and 1.65 eV)
and subtracting it from the intensity data.

Input CSV format:
- Row 0: Empty cells (columns 0-1) + Energy values (eV)
- Column 0: X coordinates (mapping)
- Column 1: Y coordinates (mapping)
- Data matrix: Intensity values
"""

import numpy as np
import pandas as pd
import os


def load_pl_data(filepath):
    """
    Load PL data from CSV file.

    Returns:
        energies: 1D array of energy values (eV)
        x_coords: 1D array of X coordinates
        y_coords: 1D array of Y coordinates
        intensities: 2D array of intensity values (n_points x n_energies)
    """
    # Read CSV with no header to preserve structure
    df = pd.read_csv(filepath, header=None, sep='\t')

    # Extract energies from first row (starting from column 2)
    energies = df.iloc[0, 2:].values.astype(float)

    # Extract coordinates and intensities from remaining rows
    x_coords = df.iloc[1:, 0].values.astype(float)
    y_coords = df.iloc[1:, 1].values.astype(float)
    intensities = df.iloc[1:, 2:].values.astype(float)

    return energies, x_coords, y_coords, intensities


def find_energy_index(energies, target_energy):
    """
    Find the index of the closest energy value to the target.

    Note: Energy array is typically in descending order (high to low).
    """
    return np.argmin(np.abs(energies - target_energy))


def linear_background_subtraction(energies, intensities, e_high=2.3, e_low=1.65):
    """
    Perform linear background subtraction.

    For each spectrum (row in intensities):
    1. Find intensity values at e_high and e_low
    2. Fit a line between these two points
    3. Subtract the linear background from the entire spectrum

    Args:
        energies: 1D array of energy values
        intensities: 2D array (n_spectra x n_energies)
        e_high: Higher energy point for background estimation (default: 2.3 eV)
        e_low: Lower energy point for background estimation (default: 1.65 eV)

    Returns:
        corrected_intensities: Background-subtracted intensity data
    """
    # Find indices for the energy bounds
    idx_high = find_energy_index(energies, e_high)
    idx_low = find_energy_index(energies, e_low)

    print(f"Background subtraction range:")
    print(f"  High energy: {e_high} eV -> index {idx_high} (actual: {energies[idx_high]:.4f} eV)")
    print(f"  Low energy: {e_low} eV -> index {idx_low} (actual: {energies[idx_low]:.4f} eV)")

    # Create output array
    corrected_intensities = np.zeros_like(intensities)

    # Process each spectrum
    n_spectra = intensities.shape[0]
    for i in range(n_spectra):
        spectrum = intensities[i, :]

        # Get intensity values at the two energy points
        i_high = spectrum[idx_high]
        i_low = spectrum[idx_low]

        # Calculate linear background for all energy points
        # Using point-slope form: I_bg(E) = I_high + (I_low - I_high) * (E - E_high) / (E_low - E_high)
        e_high_actual = energies[idx_high]
        e_low_actual = energies[idx_low]

        slope = (i_low - i_high) / (e_low_actual - e_high_actual)
        background = i_high + slope * (energies - e_high_actual)

        # Subtract background
        corrected_intensities[i, :] = spectrum - background

    return corrected_intensities


def save_pl_data(filepath, energies, x_coords, y_coords, intensities):
    """
    Save PL data to CSV file in the same format as input.
    """
    n_points = len(x_coords)
    n_energies = len(energies)

    # Create output dataframe
    # First row: empty + empty + energies
    header_row = ['', ''] + [str(e) for e in energies]

    # Data rows: x, y, intensities
    data_rows = []
    for i in range(n_points):
        row = [str(x_coords[i]), str(y_coords[i])] + [str(intensities[i, j]) for j in range(n_energies)]
        data_rows.append(row)

    # Write to file
    with open(filepath, 'w') as f:
        f.write('\t'.join(header_row) + '\n')
        for row in data_rows:
            f.write('\t'.join(row) + '\n')

    print(f"Saved corrected data to: {filepath}")


def find_data_files(root_dir):
    """
    Recursively find all data.csv files in subdirectories.
    """
    data_files = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        if 'data.csv' in filenames:
            data_files.append(os.path.join(dirpath, 'data.csv'))
    return sorted(data_files)


def process_single_file(input_file, e_high=2.3, e_low=1.65):
    """
    Process a single data.csv file and save the background-subtracted result.
    """
    output_file = os.path.join(os.path.dirname(input_file), 'data_bg_subtracted.csv')

    # Load data
    energies, x_coords, y_coords, intensities = load_pl_data(input_file)

    print(f"  Energy range: {energies.min():.4f} - {energies.max():.4f} eV ({len(energies)} points)")
    print(f"  Number of spectra: {len(x_coords)}")

    # Perform background subtraction
    corrected_intensities = linear_background_subtraction(
        energies, intensities, e_high=e_high, e_low=e_low
    )

    # Round intensities to 2 decimal places
    corrected_intensities = np.round(corrected_intensities, 2)

    # Save results
    save_pl_data(output_file, energies, x_coords, y_coords, corrected_intensities)


def main():
    # Root directory containing subdirectories with data.csv files
    ROOT_DIR = r"C:\Users\TM273821\Desktop\PL\TEst"

    # Background subtraction parameters
    E_HIGH = 2.3   # Higher energy bound (eV)
    E_LOW = 1.65   # Lower energy bound (eV)

    print("=" * 60)
    print("Linear Background Subtraction for PL Data")
    print("=" * 60)

    # Find all data.csv files
    data_files = find_data_files(ROOT_DIR)
    print(f"\nFound {len(data_files)} data.csv files to process:")
    for f in data_files:
        print(f"  - {f}")

    # Process each file
    for i, input_file in enumerate(data_files, 1):
        print(f"\n[{i}/{len(data_files)}] Processing: {input_file}")
        try:
            process_single_file(input_file, e_high=E_HIGH, e_low=E_LOW)
        except Exception as e:
            print(f"  ERROR: {e}")

    print("\n" + "=" * 60)
    print(f"Background subtraction complete! Processed {len(data_files)} files.")
    print("=" * 60)


if __name__ == "__main__":
    main()
