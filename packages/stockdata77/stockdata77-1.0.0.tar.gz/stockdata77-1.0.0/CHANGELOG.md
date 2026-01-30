# Change Log
All notable changes to this project are documented in this file starting with version 0.0.5.

## [1.0.0] - 2026-01-17
 
This is the first stable release of `stockdata77`.

### Added
- ETF @ MOEX support
- getAPIKey method
- Simple sample code
- Comprehensive Excel file manipulation sample code
 
### Changed
- The main class is now called `Securities` as the wrapper provides access to shares, ETFs and bonds pricing data
- Removed exception handling in the API wrapper. The calling code should be aware of and handle exceptions such as connectivity errors, etc.
 
### Fixed
- Nothing


## [0.0.5] - 2025-12-15
 
 
### Added
- MOEXBONDS API support.
- Building and installing `stockdata77` module to a Python venv
 
### Changed
- Removed Yahoo Finance API support as the provider has closed access to it
- Formatting of `str` output (`__str__` cast function)
 
### Fixed
- Nothing
