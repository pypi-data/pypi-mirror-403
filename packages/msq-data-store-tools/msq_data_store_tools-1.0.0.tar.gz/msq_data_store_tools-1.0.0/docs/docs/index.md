# DataStoreTools documentation!

## Description

DataStoreTools contains a series of tools and integrations that allows a user to interact with the DataStore

## Commands

The Makefile contains the central entry points for common tasks related to this project.

### Syncing data to cloud storage

* `make sync_data_up` will use `az storage blob upload-batch -d` to recursively sync files in `data/` up to `datastoretools/data/`.
* `make sync_data_down` will use `az storage blob upload-batch -d` to recursively sync files from `datastoretools/data/` to `data/`.


