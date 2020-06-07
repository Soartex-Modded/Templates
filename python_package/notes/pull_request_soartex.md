This is a shared note linked from all commits, new repositories, and PRs made under Soartex.

I wrote a python package for managing resource packs that provide mod support via texture patches. 
https://github.com/Soartex-Modded/Templates/tree/master/python_package

The tool does many things-
- It downloads the top mods for minecraft 1.5, 1.7, 1.10, 1.12 and 1.15 from curseforge, along with metadata to build mod.jsons.
- It extracts default textures from game jars and downloaded mods into a set of default patches, containing mod.jsons with data merged from Curseforge and mcmod.info files, when available.
- It logs downloaded mod versions in a sqlite database, and can be re-run with the database to incrementally update the default patch set with any new mod updates uploaded to CurseForge
- It downloads texture patch and vanilla repositories from github.
- It merges default and resource-pack patch sets into resource packs.
- It can live-maintain merged resource packs when you make edits to patch sets (via filesystem watchers).
- It can also extract default textures from modpack mods dirs and include them in default resource packs. This is so that file locations from multiple versions of the same mod may be included in the same default texture pack.
- _It uses md5 hashes of image files to detect identical images among two default resource packs._
- It ports the respective resource pack images based on the detected mappings. These ports are applied within minecraft versions (1.7.x to 1.7.x, for when mods update their paths), to newer minecraft versions (porting from 1.7.x to 1.10.x, or 1.12.x to 1.15.x), and back (1.12.x contributions may be automatically ported back to 1.10.x).
- It updates or creates resource-pack mod.json files with information pulled from CurseForge and extracted mcmod.info files
- It ports any .mcmeta files accompanying ported .png files
- It has the capability of pruning files in the patches covered by the default resource pack, that are not present in the default resource pack (where the default resource pack includes any file in the latest mod version pulled from Curseforge, or any of the linked modpacks). Pruned files are moved to a new root folder "~unused".
- _Pruning is not enabled in these PRs._ Pruning ignores ~alts and ~unused folders and ~untextured.txt files, case insensitive. It also ignores .ctx and .mcmeta files that have accompanying .png files.


In this PR, the default packs were constructed from the top 1000 mods for each minecraft version from CurseForge, as well as the mods folders from the following modpacks. Linking with modpacks protects and ports to/from the textures present in the older versions of mods used in these packs.
- 1.5.x: FTB Unleashed
- 1.7.x: FTB Infinity, Gregtech New Horizons, Gregtech Beyond Reality
- 1.10.x: FTB Beyond
- 1.12.x: FTB Revelation, SevTech Ages

I can re-run with additional linked modpacks, specific mod versions, or different/more minecraft versions if desired.

This script is not perfect: 
- if you have multiple versions of a mod patch, the textures will likely be jumbled
- there is no context- if a block uses multiple textures, and only one texture is md5-matched, then the block will only be partially textured
- if both the mod patch and texture domain is changed between versions, a new patch with name and mod.json will be created with information from CurseForge, even if you already have a patch
- model files are ignored. If custom models are added that change the path of a texture to a different location, then the automatic port will introduce unused files, and the pruning will treat custom model files as dead
- other things, I don't know


I also added some general rules to improve the quality of ports.
The patch name for the destination directory is:
1. Adopted from whatever patch contains the same texture domain
2. Else, adopted from whatever default patch contains the same texture domain  
The patch name that the texture originally came from is not used. This is too buggy.

Textures are not ported if they are empty and existing textures are not overwritten.

I have been tuning the tooling to improve the quality of ports based on my logging output, but I don't have the time to do deep testing for everything this script affects. Feel free to push changes to the `auto_port` branches to fix individual bugs.

Linked PRs:
- https://github.com/Soartex-Modded/Modded-1.15.x/pull/1
- https://github.com/Soartex-Modded/Modded-1.12.x/pull/42
- https://github.com/Soartex-Modded/Modded-1.10.x/pull/58
- https://github.com/Soartex-Modded/Modded-1.7.x/pull/186
- https://github.com/Soartex-Modded/Modded-1.5.x/pull/1

I have also saved the script output here:  
https://github.com/Soartex-Modded/Templates/blob/Soartex_port_log/python_package/notes/port_log_soartex.txt
