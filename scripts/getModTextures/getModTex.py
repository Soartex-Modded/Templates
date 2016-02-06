
import argparse, os, zipfile, json, shutil

mods = []
modInfo = {}

def getContent(src, fType, sPath=0):
  try:
    for d, sd, f in os.walk(src):
      for n in f:
        if sPath:
          if n.endswith(fType):
            fPath = os.path.join(d,n)
            mods.append(fPath)
        elif n.endswith(fType):
          return 1
        else:
          pass
  except:
    return 0

def unpackMod(mPath):
  if os.path.isdir(tmpPath):
    shutil.rmtree(tmpPath)
  modZip = zipfile.ZipFile(mPath, 'r')
  for name in modZip.namelist():
    # Only extract the needed files
    if name.endswith(('.info', '.mcmeta', '.png', '.properties')):
      if not os.path.exists(tmpPath):
        os.makedirs(tmpPath)
      modZip.extract(name, tmpPath)

def parseInfo():
  modInfo.clear()
  # Read raw file data and remove linebreaks from mcmod.info
  with open (tmpPath + '/' + 'mcmod.info', "r") as text:
    mcmodDataPre = text.read().replace('\n', '')
  try:
    # Parse JSON and save values to my own dictionary
    mcmodData = json.loads(mcmodDataPre)
    # Version 1 of mcmod.info
    if type(mcmodData) is list:
      modInfo['Name'] = mcmodData[0]['name']
      modInfo['Id'] = mcmodData[0]['modid']
      modInfo['Version'] = mcmodData[0]['version']
      getFileName(mod)
    # Version 2 of mcmod.info
    elif type(mcmodData) is dict:
      modInfo['Name'] = mcmodData['modList'][0]['name']
      modInfo['Id'] = mcmodData['modList'][0]['modid']
      modInfo['Version'] = mcmodData['modList'][0]['version']
      getFileName(mod)
    # Can't read the file something is up
    else:
      print('Something happened! Let me know..')
  except:
    getFileName(mod)
    print('Invalid data in mcmod.info file. Contact the author of: ' + modInfo['FileName'])
  return modInfo

def getFileName(modPath):
  file = os.path.basename(modPath)
  modInfo['FileName'] = os.path.splitext(file)[0]
  # print(modInfo)
  return modInfo

def cleanText(messy):
  messy = messy.replace(' ', '_')
  messy = messy.replace('\'', '')
  messy = messy.replace(':', '')
  return messy

def moveContent(src, dest):
  os.makedirs(dest)
  for sourceDir, dirs, files in os.walk(src):
    destDir = sourceDir.replace(src, dest + '/')
    if not os.path.exists(destDir):
      os.mkdir(destDir)
    for file in files:
      srcFile = os.path.join(sourceDir, file)
      destFile = os.path.join(destDir, file)
      if os.path.exists(destFile):
        os.remove(destFile)
      shutil.move(srcFile, destFile)

if __name__ == '__main__':
  # Get input and output folders
  parser = argparse.ArgumentParser(description = 'Get textures from mods.')
  parser.add_argument('-i','--input', help = 'Input folder', required = True)
  parser.add_argument('-o','--output', help = 'Output folder', required = True)
  args = vars(parser.parse_args())
  # Save args to variables
  inPath = os.path.abspath(args['input'])
  outPath = os.path.abspath(args['output'] + '/Texture_Tool/')
  if os.path.isdir(outPath):
    shutil.rmtree(outPath)
  tmpPath = outPath + '/workingFolder/'
  # Create the list 'mods' of mods with directory
  getContent(inPath, ('.jar', '.zip'), 1)
  # Start process for each mod found in inPath
  for mod in mods:
    unpackMod(mod)
    # Test if it actualy has images
    if getContent(tmpPath, '.png'):
      # Does it have a mcmod.info file
      if os.path.isfile(tmpPath + 'mcmod.info'):
        # Has mcmod.info file
        parseInfo()
        try:
          if len(modInfo['FileName']) == 0:
            pass
          elif len(modInfo['Name']) == 0:
            getFileName(mod)
            print('mcmod.info has empty values. Contact author of: '  + cleanText(modInfo['FileName']))
            dest = outPath + '/Invalid/' + cleanText(modInfo['FileName'])
            moveContent(tmpPath, dest)
          else:
            dest = outPath + '/Named/' + cleanText(modInfo['Name'])
            moveContent(tmpPath, dest)
        except:
          pass
      # Does not have mcmod.info file
      else:
        getFileName(mod)
        print('No mcmod.info file found. Contact author of: '  + cleanText(modInfo['FileName']))
        dest = outPath + '/Invalid/' + cleanText(modInfo['FileName'])
        moveContent(tmpPath, dest)
    else:
      getFileName(mod)
      print('No Images skipping mod: ' + modInfo['FileName'])
    if os.path.isdir(tmpPath):
      shutil.rmtree(tmpPath)
  print('All done....')
