Script to create and live-maintain a resource pack of mod patches, from a repository of mod patches.  

This script...  
- builds a mod resource pack from a repository of mod patches
- creates symlinks from your game instances to the generated resource pack
- watches for changes in the patch repository, and automatically modifies the generated resource pack with those changes

How to use:
1. modify config.json to include
    - paths to repository clones
    - the directory to output the generated pack
    - locations to put symlinks to generated resource packs under game instances
2. set the active_version in the config.json
3. install python 3.6 or greater
4. open terminal and cd into the mergePacks directory
5. pip3 install watchdog
6. python3 live_merge.py


Vanilla pack should be a separate resource pack layer. 
It is also possible to run multiple instances of this script, if you have multiple simultaneous layers of mod patches. 

Author: Shoeboxam