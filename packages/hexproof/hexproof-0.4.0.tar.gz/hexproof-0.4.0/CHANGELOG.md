## 0.4.0 (2026-01-23)

### Feat

- **cli**: Modularized CLI tooling, new Pydantic validation approach for better readability pending full rewrite
- **utils**: Introduced utils module for general utilities, added `validation` submodule

### Fix

- **scryfall**: Add some currently undocumented fields to Card schema
- **mtgjson**: Provider `mtgjson` updated for new providers module, introduced MTGJsonSchema base class, aligned types with current MTGJSON data

### Refactor

- **workflow**: Minor tweaks to account for uv locking
- **workflows**: Simplify publish workflow
- **workflows**: Enable workflow dispatch
- **scryfall**: Provider `scryfall` updated for new providers module, introduced ScryfallSchema base class, aligned types with current Scryfall data
- **vectors**: Provider `vectors` updated for new providers module
- **pyproject.toml**: Add py.typed, ensure changelog uses utf-8 encoding

## 0.3.7 (2024-10-10)

### Fix

- **mtgpics**: Rework scraping to bring in line with new schemas

## 0.3.6 (2024-10-10)

### Refactor

- **mtgpics/schemas**: Add more fields to preliminary MTGPics schemas
- **mtgjson/fetch**: Convert URL to str

## 0.3.5 (2024-09-08)

### Refactor

- **cli**: Move to class-based command groups, implement better testing and logging
- **hexapi**: Add URL enums

## 0.3.4 (2024-08-24)

### Refactor

- **pyproject.toml**: Update project information

## 0.3.3 (2024-08-22)

### Refactor

- **CardLayout**: Add "case" as a recognized Scryfall card layout

## 0.3.2 (2024-08-16)

### Fix

- **scryfall/schema**: card_back_id can be missing from Card schema, some ManaColor fields can include C (colorless) mana value

## 0.3.1 (2024-08-15)

### Fix

- **mtgjson/schema**: Update SealedProductCard field "uuid" to Optional

### Refactor

- **project**: Update deps and LICENSe
- **vectors**: Rework vectors schema, enums, and funcs to utilize GitHub's release system to pull new mtg-vectors packages
- **scryfall/fetch**: New endpoint: `get_catalog`

## 0.3.0 (2024-07-10)

### Feat

- **scryfall**: Add utils for processing Scryfall URLs

## 0.2.2 (2024-05-30)

### Refactor

- **scryfall/fetch**: Implement new request funcs

## 0.2.1 (2024-05-29)

### Fix

- **mtgjson/enums**: Change incorrect MTGJSON url

### Refactor

- **vectors/fetch**: Separate caching and request funcs, remove deprecated `update_vectors_manifest`
- **scryfall**: Small schema changes, remove deprecated type "SetTypes", add core imports to __init__
- **scryfall/fetch**: Use "cache_" naming for download funcs, "get_" for JSON data loading funcs. Add new request funcs
- **schema**: Treat missing lists as an empty list
- **mtgjson/fetch**: Use "cache_" for saving JSON files locally, use "get_" for loading as JSON object. Implement new request functions

## 0.2.0 (2024-05-17)

### Feat

- **mtgpics**: Introduce new data source: MTGPics.com
- **mtgjson**: Implement full schema spec from MTGJSON docs

### Refactor

- **mtg-vectors**: Make adjustments to MTG Vectors data source
- **scryfall**: Finish base schema definitions and enums for Scryfall data source
- **hexapi**: Integrate "unified" hexproof.io API source as hexapi module
- **scryfall**: Implement new enums, update fetch funcs, update Set schema
- **pyproject.toml**: Add commitizen config

## 0.1.0 (2024-05-02)

### Refactor

- **hexproof**: Import core functionality from the `hexproof.io` repository
