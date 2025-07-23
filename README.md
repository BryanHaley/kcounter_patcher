# Half-Life Kill Counter Patcher

## What

This utility patches valve_WON from either the Half-Life 2005 or GoldSrc package to have the capability to count your kills. Upon exit, the valve_WON folder is restored to its original state. It was created for the purpose of the Half-Life 100% speedrun category.

## How

Download [the latest zip](https://github.com/BryanHaley/kcounter_patcher/releases) and extract to either the `Half-Life 2005 WON` or `GoldSrc Package 2.4` directory. Double click on your preferred batch file to launch the game.

## What are all these base64 blobs?

In order for the kill counter to work, the client/server DLLs and a few maps must be patched. The base64 blobs are the pre-patched files embedded into the script for the convenience of having a single exe file that can do the patching. The base64 blobs are encoded in a pipeline (above) based on the files in this repository.
