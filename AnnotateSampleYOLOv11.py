import csv, shutil, random, os

'''Clears all files from a list of directories and outputs when each is cleared.

Args:
        directories: A list of directories to be cleared
'''
def clearOutputFiles(directories: list):
        for dir in directories:
                fileCount = 0
                for file in os.listdir(dir):
                        filepath = os.path.join(dir, file)

                        if os.path.isfile(filepath):
                                os.remove(filepath)
                                fileCount += 1
                print(f"Cleared {fileCount} files from {dir}")

'''Creates annotation (.txt) files in temporary location Output/obj_train_data

Args:
        filterByPathology:      String which specifies which classification of cancer should be included.
                                Specifiying "none" includes all images, but annotates them as 'tumour's
                                "none" | "benign" | "malignant" | "both"
        filterBySide:   Boolean which specifies if multiple images pertaining to a patient should be used (false) or filtered out
                        to only include one image per patient (true).  
        includeBUDaCaD: Boolean which specifies whether the BUDaCaD dataset (US images classified as "Normal")
        sampleSize:     Specifies the max number of images taken from BUSBRA
Returns:
        idsBUSBRA:      List of ids for the selected BUSBRA images      example "bus_0006-s"
        idsBUDaCaD:     List of ids for the selected BUDaCaD images     example "IM-0016-0001"
'''
def createAnnotations(filterByPathology: str, filterBySide: bool, includeBUDaCaD: bool, sampleSize: int):
        line_count = 0
        type_count = 0
        side_count = 0
        idBUSBRA = []
        pathologies = []
        widths = []
        heights = []
        sides = [] 
        BBOXes = []

        # Reads BUSBRA CSV, filtering from set filters
        busCSV = open("Input\\bus_data.csv", 'r')
        csvReader = csv.DictReader(busCSV, delimiter=',')
        for row in csvReader:
                if (line_count - type_count - side_count) < sampleSize or sampleSize == 0:
                        if line_count == 0:
                                line_count += 1
                        if (filterByPathology == "benign" or filterByPathology == "malignant") and row["Pathology"] != filterByPathology:
                                type_count += 1
                        elif (filterBySide == True) and row["Side"] == "right":
                                side_count += 1
                        else:
                                idBUSBRA.append(str(row["ID"]))
                                pathologies.append(str(row["Pathology"]))
                                widths.append(int(row["Width"]))
                                heights.append(int(row['Height']))
                                sides.append(str(row["Side"]))
                                BBOX = row["BBOX"]
                                BBOX = BBOX[1:len(BBOX)-1]
                                BBOX = BBOX.split(",")
                                BBOXes.append(BBOX)
                        line_count += 1
        print(f'Read {line_count} BUSBRA csv lines')

        # Reporting images being filtered out if applicable
        if filterByPathology == "benign" or filterByPathology == "malignant":
                print(f'Filtered out {type_count} images that were not {filterByPathology}')
        if filterBySide:
                print(f'Filtered out {side_count} images that were taken from the right side')

        # Creates BBOX Annotations, saved to temporary location pre-sampling
        percentComplete = 0
        for i in range(0, len(idBUSBRA)):
                f = open(f"Output\\obj_train_data\\{idBUSBRA[i]}.txt", 'w')
                iXc, iYc, iWidth, iHeight = convertBBOX(widths[i], heights[i], BBOXes[i])
                if filterByPathology == "both" and pathologies[i] == "malignant":
                        f.write(f"1 {iXc} {iYc} {iWidth} {iHeight}")          
                else:
                        f.write(f"0 {iXc} {iYc} {iWidth} {iHeight}")
                f.close()

                # Progress update to user
                if (i-1) % round(len(idBUSBRA)/10, 0) == 0:
                        print(f"Creating BUSBRA annotations: {percentComplete}% complete!")
                        percentComplete += 10
        print(f"Creating BUSBRA annotations: {percentComplete}% complete!")

        # Creates empty annotation files in a temporary location for "Normal" US images, gathers ids
        idBUDaCaD = []
        if includeBUDaCaD:
                f = open(f"Input\\fileNamesBUDaCaD.txt", "r")
                idBUDaCaD = (f.read()).split('\n')
                idBUDaCaD = idBUDaCaD[0:len(idBUDaCaD)-1]

                for id in idBUDaCaD:
                        f = open(f"Output\\obj_train_data\\{id}.txt", 'w')
                        f.close()       # No annotations are possible, so no Bounding Boxes are added

        
        createAssistingFiles(filterByPathology, idBUSBRA, idBUDaCaD)        
        print(f'Created annotation files for all {len(idBUSBRA) + len(idBUDaCaD)} images.')

        return idBUSBRA, idBUDaCaD

'''For an individual image, takes the width, height and BUSBRA BBOX coordinates in pixels and converts into YOLOv11 format

Args:
        imageWidth: Width of image in pixels
        imageHeight:    Height of image in pixels
        BBOX:   List containing [Xmin, Ymin, Width, Height] in pixels

Returns:
        iXc:    Centre x coordinate of the BBOX from 0-1
        iYc:    Centre y coordinate of the BBOX from 0-1
        iWidth: Width of the BBOX from 0-1
        iHeight:Height of the BBOX from 0-1
'''
def convertBBOX(imageWidth: int, imageHeight: int, BBOX: list):         
        Xmin, Ymin = int(BBOX[0]), int(BBOX[1])
        BBOXwidth, BBOXheight = int(BBOX[2]), int(BBOX[3])
        Xc = (Xmin + (BBOXwidth/2))/imageWidth          
        Yc = (Ymin + (BBOXheight/2))/imageHeight
        BBOXwidth /= imageWidth
        BBOXheight /= imageHeight                      
        return round(Xc, 6), round(Yc, 6), round(BBOXwidth, 6), round(BBOXheight, 6)

''' Only used to create the assisting files that allow for uploading the annotations onto CVAT.com to manually check BBOX placement
        Creates files:  obj.names, obj.data, train.txt

Args:
        filterByPathology:      String which specifies which classification of cancer should be included.
                                Specifiying "none" includes all images, but annotates them as 'tumour's
                                "none" | "benign" | "malignant" | "both"
        idsBUSBRA:      List of ids for the selected BUSBRA images      example "bus_0006-s"
        idsBUDaCaD:     List of ids for the selected BUDaCaD images     example "IM-0016-0001"
'''
def createAssistingFiles(filterByPathology: str, idsBUSBRA: list, idsBUDaCaD: list):
        classPathology = filterByPathology
        if filterByPathology == "none":
                classPathology = "tumour"
        elif filterByPathology == "both":
                classPathology = "benign\nmalignant"             
        f = open("Output\\obj.names", 'w')
        f.write(f"{classPathology}")
        f.close()

        classNumber = "1"
        if filterByPathology == "both":
                classNumber = "2"
        f = open("Output\\obj.data", "w")
        f.write(f"classes = {classNumber}\ntrain = data/train.txt\nnames = data/obj.names\nbackup = backup/")
        f.close()    

        f = open("Output\\train.txt", "w")
        for id in idsBUSBRA:
                f.write(f"data/obj_train_data/{id}.png\n")
        for id in idsBUDaCaD:
                f.write(f"data/obj_train_data/{id}.jpg\n")      
        f.close()   


''' Converts a list of files to a list of file paths for the purposes of copying/deleting files. 
        Concatinates: sourcePath + id + fileExtension

Args:
        sourcePath:     source Directory for instance \Input\BUSBRA
        files:          List of fileNames (without their file extensions)
        fileExtension:  fileExtension to be appended to the end of each file

Returns:
        paths:          List of filepaths
'''
def convertToPaths(sourcePath: str, files: list, fileExtension: str):
        paths = []
        for file in files:
                paths.append(f"{sourcePath}\\{file}{fileExtension}")
        return paths

''' Takes a list of filePaths and copies them into the desired location. Used to copy sampled data into thier training/validation sets

Args:
        filePaths:       List of file paths to be copied
        destinationPath: String denoting the desired location of the source files.
'''
def copyFiles(filePaths: list, destinationPath: str):
        # Use Shutil to copy the file into the correct folder
        fileCount = 0
        for path in filePaths:
                splitPath = path.split("\\")
                fileName = splitPath[len(splitPath)-1]
                shutil.copy(path, f"{destinationPath}\\{fileName}")
                fileCount += 1
        print(f"Copied {fileCount} files into {destinationPath}")

''' Using the set sampling type, takes the selected BUSBRA & BUDaCaD set and samples them into a 80% training and 20% validation set. Then copies over the input images into the output

Args:
        samplingType: String which specifies which sampling type to use. Options: "stratified" | "off"
        pathsBUSBRA:            List of filepaths to access the BUSBRA images
        pathsLabelBUSBRA:       List of filepaths to access the BUSBRA annotations
        pathsBUDaCaD:           List of filepaths to access the BUDaCaD images
        pathsLabelBUDaCaD:      List of filepaths to access the BUDaCaD labels
        destinationImages:      Desired destination directory for the sampled images
        destinationLabels:      Desired destination directory for the sampled labels
'''
def createTrainValSet(samplingType: str, pathsBUSBRA: list, pathsLabelBUSBRA: list, pathsBUDaCaD: list, pathsLabelBUDaCaD: list, destinationImages: str, destinationLabels: str):
        trainImages = []
        trainLabels = []
        valImages = []
        valLabels = []

        if samplingType == "stratified":
                for i in range(0, max(len(pathsBUSBRA), len(pathsBUDaCaD))):
                        if pathsBUSBRA:
                                randBUSBRA = random.randint(0, len(pathsBUSBRA)-1)
                                if (i % 5) == 0:       #20% of the time will pick to add to the validation set 
                                        valImages.append(pathsBUSBRA.pop(randBUSBRA))
                                        valLabels.append(pathsLabelBUSBRA.pop(randBUSBRA))
                                else:
                                        trainImages.append(pathsBUSBRA.pop(randBUSBRA))
                                        trainLabels.append(pathsLabelBUSBRA.pop(randBUSBRA))      
                        if pathsBUDaCaD:
                                randBUDaCaD = random.randint(0, len(pathsBUDaCaD)-1)
                                if (i % 5) == 0:       #20% of the time will pick to add to the validation set 
                                        valImages.append(pathsBUDaCaD.pop(randBUDaCaD))
                                        valLabels.append(pathsLabelBUDaCaD.pop(randBUDaCaD))
                                else:
                                        trainImages.append(pathsBUDaCaD.pop(randBUDaCaD))
                                        trainLabels.append(pathsLabelBUDaCaD.pop(randBUDaCaD))

        copyFiles(trainImages, f"{destinationImages}\\train")
        copyFiles(trainLabels, f"{destinationLabels}\\train")
        copyFiles(valImages, f"{destinationImages}\\validation")
        copyFiles(valLabels, f"{destinationLabels}\\validation")

''' Overall algorithm aims to:
        Clearing Output Files:
        Clean the existing output directories in order to recreate a train/val set without overwriting files
        
        Creating Annotations:
        Read the BUSBRA.csv file and filter out images based on Pathology, Side, where specified
        Opt in or Out for the BUDaCaD dataset ('Normal' images only) to be included
        Create YOLOv11 annotation files denoting the Bounding Boxes (BBOX) or lack there of

        Creating Training & Validation Sets:
        Use the selected sampling type to sample the BUSBRA and/or BUDaCaD dataset
        Once a 80% train, 20% val sample has been achieved, copy the image and annotation files into the desired location

        Overall, generates a YOLOv11 compatible Train & Val dataset to be easily fed into the YOLOv11 Machine Learning model
'''
def main():
        PathologyFilter = "none"                # "none" | "benign" | "malignant" | "both"
        SideFilter = False                      # False | True (produces one image per patient)
        IncludeBUDaCaD = True                   # False | True (BUDaCaD dataset included)
        SampleSizeBUSBRA = 0                    # 0 (no set size) | x (x images taken from BUSBRA)
        SamplingType = "stratified"             # "stratified" | "off"
        PathBUSBRA  = "Input\\BUSBRA"
        PathBUDaCaD = "Input\\BUDaCaD"
        TemporaryLabels         = "Output\\obj_train_data"            # HARDCODED to satisfy CVAT viewing
        DestinationLabels 	= "Output\\labels"
        DestinationImages       = "Output\\images"

        print("################################################################\n Clearing Output Files\n")
        toClearDir = [TemporaryLabels, f"{DestinationImages}\\train", f"{DestinationImages}\\validation", f"{DestinationLabels}\\train", f"{DestinationLabels}\\validation"]
        clearOutputFiles(toClearDir)

        print("################################################################\n Creating Image Annotation Files\n")
        idsBUSBRA, idsBUDaCaD = createAnnotations(PathologyFilter, SideFilter, IncludeBUDaCaD, SampleSizeBUSBRA)

        if not SamplingType == "off":
                print("################################################################\n Creating Training & Validation Set\n")
                pathsBUSBRA 	  = convertToPaths(PathBUSBRA, idsBUSBRA, ".png")
                pathsLabelBUSBRA  = convertToPaths(TemporaryLabels, idsBUSBRA, ".txt")
                pathsBUDaCaD 	  = convertToPaths(PathBUDaCaD, idsBUDaCaD, ".jpg")
                pathsLabelBUDaCaD = convertToPaths(TemporaryLabels, idsBUDaCaD, ".txt") 
                createTrainValSet(SamplingType, pathsBUSBRA, pathsLabelBUSBRA, pathsBUDaCaD, pathsLabelBUDaCaD, DestinationImages, DestinationLabels)

print("Start")
main()
print("End")

''' Improvements:

* Unit Testing 

'''
