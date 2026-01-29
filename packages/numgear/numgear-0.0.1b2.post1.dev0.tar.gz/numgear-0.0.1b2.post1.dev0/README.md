# Numpy Extension

This Python package extends the functionality of numpy by introducing additional methods for data manipulation, and a specialized format for reading and writing numpy arrays.

## Features

- **Read `NDArray` in Need with Keys**: Using a key to load the required array without load all.
- **Array Mapping and Transformation Functions**: Functions to apply operations across arrays, adjust their ranges, and produce linearly spaced values with specific properties.

## Installation
```bash
pip install numgear
```

## Usage

### Transformation Functions

- **apply_from_axis**: Apply a function to slices of an array along a specified axis.
- **map_range**: Transform elements in an array to a specified range.
- **map_ranges**: Transform elements in an array to multiple specified ranges based on conditions.
- **linspace_at**: Generate linearly spaced numbers for given indices.
- **linspace_cumprod_at**: Generate a cumulative product series for linearly spaced values at specific indices.

### Save and Load Utilities

- **savek**: Save multiple numpy arrays to a custom binary format `.npk`.
- **loadk**: Load arrays from a `.npk` file and read in need for easy access.