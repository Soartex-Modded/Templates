## Graphics Management
Utilities to update and maintain repositories of mod resource pack patches.

## Entry Points
This package adds a terminal entry point called `resource_manage`. 
The entry point runs pipelines of tasks.
A list of preset pipelines is available in `configs/pipelines.toml`.
Additional pipelines may be added or prior pipelines may be modified.

## Tasks

### Run Pipeline
A task that runs another pipeline by name.

### Extract Default
Unzip resources from a list of folder paths containing mod jars.

### Merge Patches
Merge mod patches (soartex, invictus, default, etc.) into a single resource pack.

### Link Resources
Create the symbolic links described in the resource `links_dirs` to the `pack_dir`.

### Watch Changes
Script to live-maintain multiple resource packs built from mod patches, from multiple repositories of mod patches.  

### Port Patches
Use MD5 hashes to detect identical files between two different resources.
Then port textures from one resource to the other, based on the discovered mapping.

### Prune Files
Delete files from a directory of mod patches that are not present in a merged default pack.
This task does not delete files from a patch if no textures from the patch are detected in the merged default pack.
This task moves files into a temporary directory, instead of deleting them.

### Download Mods
Uses the CurseForge api to download the top k most downloaded mods for each specified minecraft version into a mods folder.

### Download Resource
Clones or downloads the necessary assets from a git repository or CurseForge.
The default resources.toml contains all the necessary info for automatically collecting all of the resources.


## Installation
1. python 3.6 or greater
2. pip3 install -e .

## How to use
Type `resource_manage [pipeline_name]` from the terminal to invoke the specified pipeline.

For example, a useful pipeline is `resource_manage 1.7_dev`, which starts a watcher to maintain a resource pack with edits to patches.
F3+T from any linked game instances.
You may want to edit the links in the `resources.toml` to symlink the maintained pack into your minecraft instance.


Keep in mind, the developer python package install (`-e .`) allows you to edit the package source or default configs without needing to reinstall.

Author: Shoeboxam