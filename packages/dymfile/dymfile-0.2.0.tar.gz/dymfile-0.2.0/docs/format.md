# DYM Format Specification

The DYM format is a binary file format used by the SEAPODYM project to store oceanographic data.

## File Structure

A DYM file consists of:

1. **Header** (36 bytes)
   - Unknown fields (16 bytes)
   - nlon: number of longitude points (4 bytes, int32)
   - nlat: number of latitude points (4 bytes, int32)
   - nlevel: number of time levels (4 bytes, int32)
   - t0: start time in SEAPODYM format (4 bytes, float32)
   - tfin: end time in SEAPODYM format (4 bytes, float32)

2. **Longitude grid** (nlat × nlon × 4 bytes)
   - 2D array of float32 values

3. **Latitude grid** (nlat × nlon × 4 bytes)
   - 2D array of float32 values

4. **Time vector** (nlevel × 4 bytes)
   - 1D array of float32 values in SEAPODYM format

5. **Mask** (nlat × nlon × 4 bytes)
   - 2D array of int32 values
   - 0 = land, 1 = 1st layer, 2 = 2nd layer, 3 = 3rd layer

6. **Data** (nlevel × nlat × nlon × 4 bytes)
   - 3D array of float32 values
   - Invalid value: -999 (replaced by NaN on read)

## SEAPODYM Date Format

Time is encoded as: `year + day_of_year / 365`

Examples:
- 2020.0 = January 1, 2020
- 2020.5 ≈ July 2, 2020 (day 183)
- 2021.0 = January 1, 2021

For monthly data (default), times are centered on the 15th of each month.

## Notes

- All multi-byte values are in little-endian format
- Coordinates form a regular grid (though stored as 2D arrays)
- The mask is mandatory in the file format
- Data values of -999 are treated as missing/invalid
