import os, shutil

directory = r"../Images/"
filesLocation = r"F:\Anime"

for subdir, dirs, files in os.walk(directory):
    for filenameJpg in files:
        # if filenameJpg == "Arifureta Shokugyou de Sekai Saikyou_Season 2.jpg":
        fileName = filenameJpg.replace(".jpg","")
        name = fileName.split("_")[0]
        seasonName = fileName.split("_")[1]
        dirPath = u"\\".join((filesLocation, name, seasonName))
        dirExists = os.path.isdir(dirPath)

        if dirExists:
            old_name = os.path.join(os.path.abspath(subdir), filenameJpg)
            base, extension = os.path.splitext(name)
            new_name = os.path.join(filesLocation, base, seasonName, seasonName.lower().replace(" ", "") + ".jpg")
            fileExists = os.path.isfile(new_name)
            if not fileExists:
                print(old_name, new_name)
                # shutil.copy(old_name, new_name)