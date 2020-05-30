Script to create and live-maintain a resource pack of mod patches, from a repository of mod patches.  

This script...  
- builds a mod resource pack from a repository of mod patches
- creates symlinks from your game instances to the generated resource pack
- watches for changes in the patch repository, and automatically modifies the generated resource pack with those changes

## Installation
1. python 3.6 or greater
2. pip3 install watchdog
3. modify config.json to include
    - paths to repository clones
    - the directory to output the generated pack
    - locations in minecraft game instances to symlink the generated resource pack from
    
## How to use
1. set the active_version in the config.json
2. open terminal to the mergePatches directory
3. python3 live_merge.py
4. edit textures in the watched patch repository
5. F3+T from any linked game instances

Vanilla pack should be a separate resource pack layer. 
It is also possible to run multiple instances of this script, if you have multiple simultaneous layers of mod patches. 

Author: Shoeboxam