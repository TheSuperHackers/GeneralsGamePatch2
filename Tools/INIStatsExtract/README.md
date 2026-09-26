# INIStatsExtract

Searches all game INI files for fields that match one or more filters. It writes every matching definition to a text file, together with the parent blocks of each match.

Requires Python 3.10 or newer. No extra packages are needed.

## Usage

```
python Tools/INIStatsExtract/INIStatsExtract.py FILTER [FILTER ...] [options]
```

Example:

```
python Tools/INIStatsExtract/INIStatsExtract.py "Conditions = PLAYER_UPGRADE"
```

Output:

```
; Filters: Conditions = PLAYER_UPGRADE
; Root: ...\GeneralsZH\Data\INI
; Definitions: 194, Matching lines: 231

Object AirF_AmericaInfantryColonelBurton
  ArmorSet
    Conditions = PLAYER_UPGRADE

Object AirF_AmericaInfantryMissileDefender
  ArmorSet
    Conditions = PLAYER_UPGRADE
...
```

More examples:

```
python Tools/INIStatsExtract/INIStatsExtract.py BuildTime
python Tools/INIStatsExtract/INIStatsExtract.py BuildCost BuildTime --all -o costs.txt
python Tools/INIStatsExtract/INIStatsExtract.py "ConditionState = MOVING" --show-files
python Tools/INIStatsExtract/INIStatsExtract.py "Object = AirF_*"
python Tools/INIStatsExtract/INIStatsExtract.py "*Time"
```

## Options

| Option | Description |
| --- | --- |
| `FILTER` | One or more field filters, see [Filters](#filters). |
| `-o`, `--output PATH` | Output text file. The default is `Tools/INIStatsExtract/.Generated/<filters>.txt`. |
| `-r`, `--root PATH` | Folder that is searched recursively for `*.ini` files. The default is `GeneralsZH/Data/INI`. |
| `--all` | Only list definitions that match every filter. Without it, a definition is listed if it matches any filter. |
| `--show-files` | Write `; <file>:<line>` above each definition. |

The `.Generated` folder is ignored by git.

## Filters

A filter has the form `KEY` or `KEY = VALUE`. Put quotes around filters that contain spaces.

- **Key only:** `BuildTime` matches every `BuildTime` field, whatever its value.
- **Key and value:** `Conditions = PLAYER_UPGRADE` matches when the words of the filter value appear in the field value, in the same order and next to each other. So it also matches `Conditions = PLAYER_UPGRADE CRATEUPGRADE_ONE`. Only whole words match, so `PLAYER` alone does not match `PLAYER_UPGRADE`.
- **Case:** matching ignores upper and lower case, like the game.
- **Wildcards:** `*` and `?` work in the key and in each value word, for example `*Time` or `Object = AirF_*`.

The key of an INI line is the text before `=`. If there is no `=`, the key is the first word. In that case the remaining words are the value. So these lines can be matched as well:

| INI line | Key | Value |
| --- | --- | --- |
| `BuildTime = 20.0` | `BuildTime` | `20.0` |
| `ArmorSet` | `ArmorSet` | (none) |
| `Object AirF_AmericaInfantryColonelBurton` | `Object` | `AirF_AmericaInfantryColonelBurton` |
| `Draw = W3DModelDraw ModuleTag_01` | `Draw` | `W3DModelDraw ModuleTag_01` |

## Reading the output

- Each block is one top-level definition, such as `Object`, `Weapon` or `CommandButton`, that contains at least one match.
- Only the matching lines are shown, each with the blocks that contain it, in their original order and indentation. A shared parent appears only once.
- Definitions are sorted alphabetically by name.
- The header lists the filters, the searched folder and the number of matching definitions and lines.
- Add `--show-files` to see which file and line each definition comes from.
