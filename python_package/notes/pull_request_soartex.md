This is a shared note linked from all commits, new repositories, and PRs made under Soartex.

I wrote a python package for managing resource packs that provide mod support via texture patches. 
https://github.com/Soartex-Modded/Templates/tree/master/python_package

The tool does many things-
- It downloads the top 1000 mods for minecraft 1.5, 1.7, 1.10, 1.12 and 1.15 from curseforge, along with metadata to build mod.jsons.
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

This script is not perfect- there is no context. If a block uses multiple textures, and only one texture is md5-matched, then the block will only be partially textured


I also added some general rules to improve the quality of ports.
The patch name for the destination directory uses this algorithm:
https://github.com/Soartex-Modded/Templates/blob/d94cf08166ea437237df6ba9c730bc67aacf4086/python_package/resource_manager/tasks/port_patches.py#L167

Textures are not ported if they are empty and existing textures are not overwritten.

Linked PRs:
- https://github.com/Soartex-Modded/Modded-1.15.x/pull/2
- https://github.com/Soartex-Modded/Modded-1.12.x/pull/43
- https://github.com/Soartex-Modded/Modded-1.10.x/pull/59
- https://github.com/Soartex-Modded/Modded-1.7.x/pull/193
- https://github.com/Soartex-Modded/Modded-1.5.x/pull/2
