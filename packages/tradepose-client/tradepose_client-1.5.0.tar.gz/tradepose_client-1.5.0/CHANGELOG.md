# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.4.0] - 2026-01-23

### Added

- `BatchTester.list_instruments()` method for querying available instruments
- Support for enum types (`AccountSource`, `BrokerType`, `MarketType`) in `list_instruments()`

## [1.3.0] - 2026-01-22

### Added

- `trade_count` parameter to `export_latest_trades` method for limiting exported trades

### Changed

- Updated dependency on `tradepose-models>=1.3.0`

## [1.2.0] - 2026-01-19

### Added

- `TradingSetup` sync wrapper for synchronous API usage
- E2E test suite for Client SDK validation

### Changed

- Replaced `broker_type`/`platform` parameters with unified `account_source`
- Updated dependency on `tradepose-models>=1.2.0`

## [1.1.0] - 2025-12-21

### Changed

- Version bump to align with tradepose-models 1.1.0

## [1.0.0] - 2025-11-29

### Breaking Changes

- First stable release with breaking changes from 0.1.x series (previously 0.1.2)
- API changes incompatible with previous versions

### Added

- Stable API for TradePoseClient and BatchTester

## [0.1.0] - 2025-11-29 (deprecated)

### Added

- Initial release
- TradePoseClient async client with context manager support
- TradePoseConfig for configuration management
- BatchTester for batch backtesting with Period-based date ranges
- BatchResults and PeriodResult for result handling
- StrategyBuilder and BlueprintBuilder for strategy construction
- IndicatorSpecWrapper for indicator configuration
- TradingContext for trading session management
- 18 exception types for comprehensive error handling
- Jupyter notebook support via nest-asyncio
- Low-level API resources: api_keys, billing, strategies, tasks, export, usage
- Full type safety with Pydantic models
- Polars integration for DataFrame operations
