# GeneralsGamePatch2

Community Patch (2) to fix and improve original Generals 1.08 and Zero Hour 1.04

EA has not endorsed and does not support this product.

## Build

The project is built with the [Generals Mod Builder](https://github.com/TheSuperHackers/GeneralsModBuilder), which is a git submodule, so clone recursively:

```
git clone --recursive https://github.com/TheSuperHackers/GeneralsGamePatch2
```

If the repository is already cloned, fetch the submodule with:

```
git submodule update --init --recursive
```

Nothing else needs to be installed. The Mod Builder launcher installs [uv](https://docs.astral.sh/uv/) on first use, and uv then downloads a suitable Python and the required packages by itself.

Run any of the scripts in [Tools/ModBuilder/Scripts](Tools/ModBuilder/Scripts):

| Script | What it does |
| --- | --- |
| `BuildInstall.bat` | Builds the patch and installs it into the game folder |
| `BuildInstallRun.bat` | Builds, installs, runs the game, then uninstalls when the game closes |
| `BuildInstallRunWithGui.bat` | The same, with the graphical interface |
| `BuildRelease.bat` | Builds the patch and packs the release archives |
| `Uninstall.bat` | Removes the patch from the game folder |

The submodule commit decides which Mod Builder version is used. Upgrade it with:

```
git submodule update --remote Tools/GeneralsModBuilder
git add Tools/GeneralsModBuilder
git commit -m "Upgrade the Mod Builder"
```
