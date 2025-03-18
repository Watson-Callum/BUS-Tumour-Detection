import json
import subprocess
import os
import csv
import shutil

'''Clears all files from a list of directories and outputs when each is cleared.

Args:
        directories: A list of directories to be cleared
'''
def clearOutputFiles(directories: list):
    for dir in directories:
        fileCount = 0
        try:
            for file in os.listdir(dir):
                filepath = os.path.join(dir, file)

                if os.path.isfile(filepath):
                    os.remove(filepath)
                    fileCount += 1
            print(f"Cleared {fileCount} files from {dir}")
        except FileNotFoundError:
            print("New destination directory defined, no clearing required.")
        
'''For an individual image, takes the width, height and YOLOv11 JSON BBOX coordinates in pixels and converts into YOLOv11 input format

Args:
        imageWidth:     Width of image in pixels
        imageHeight:    Height of image in pixels
        BBOX:           List containing [Xmin, Ymin, Width, Height] in pixels

Returns:
        iXc:    Centre x coordinate of the BBOX from 0-1
        iYc:    Centre y coordinate of the BBOX from 0-1
        iWidth: Width of the BBOX from 0-1
        iHeight:Height of the BBOX from 0-1
'''
def convertBBOX(imageWidth: int, imageHeight: int, BBOX: list):
    Xmin , Ymin = int(BBOX[0]), int(BBOX[1])
    BBOXwidth, BBOXheight = int(BBOX[2]), int(BBOX[3])
    Xc = (Xmin + (BBOXwidth/2))/imageWidth          
    Yc = (Ymin + (BBOXheight/2))/imageHeight
    BBOXwidth /= imageWidth
    BBOXheight /= imageHeight 
    return round(Xc, 6), round(Yc, 6), round(BBOXwidth, 6), round(BBOXheight, 6)

'''Reads the BUSBRA CSV focussing on returning the size of the images, since they vary

Args:
        sourceDir:      Location of bus_data.csv

Returns:
        ids:        BUSBRA image ids
        widths:     BUSBRA image size widths in pixels
        heights:    BUSBRA image size heights in pixels
'''
def readCSV(sourceDir: str):
    ids = []
    widths = []
    heights = []
    line_count = 0
    busCSV = open(f"{sourceDir}\\bus_data.csv", 'r')
    csvReader = csv.DictReader(busCSV, delimiter=',')
    for row in csvReader:
        if line_count == 0:
            line_count += 1
        ids.append(str(row["ID"]))
        widths.append(int(row["Width"]))
        heights.append(int(row['Height']))
        line_count += 1
    print(f'Read {line_count} BUSBRA csv lines')
    return ids, widths, heights

''' Only used to create the assisting files that allow for uploading the annotations onto CVAT.com to manually check BBOX placement
    Creates files:  obj.names, obj.data, train.txt

Args:
    pathology:      String which specifies which classification of cancer should be included.
                    Specifiying "none" annotates them as 'tumour's
                    "none" | "benign" | "malignant" | "both"
    idsValidation:  List of ids for the validation images      example "bus_0006-s"
    destinationDir: Directory the CVAT files are to be created
'''
def createCVATFiles(pathology: str, idsValidation: list, destinationDir: str):
    if pathology == "none":
        classPathology = "tumour\npredTumour"
    elif pathology == "benign":
        classPathology = "benign\npredBenign"
    elif pathology == "malignant":
        classPathology = "malignant\npredMalignant"
    elif pathology == "both":
        classPathology = "benign\nmalignant\npredBenign\npredMalignant"             
    f = open(f"{destinationDir}\\obj.names", 'w')
    f.write(f"{classPathology}")
    f.close()

    classNumber = "2"
    if pathology == "both":
        classNumber = "4"
    f = open(f"{destinationDir}\\obj.data", "w")
    f.write(f"classes = {classNumber}\ntrain = data/train.txt\nnames = data/obj.names\nbackup = backup/")
    f.close()    

    f = open(f"{destinationDir}\\train.txt", "w")
    for id in idsValidation:
        id = id[0:len(id)-4]
        if id[0:2] == "IM":
            f.write(f"data/obj_train_data/{id}.jpg\n")
        else:
            f.write(f"data/obj_train_data/{id}.png\n")
    f.close()   

''' Takes a list of filePaths and copies them into the desired location. Used to copy validation annotations

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


def main():
    DestinationDirectory = 'Output'
    LabelsDirectory = '\\obj_train_data'
    SourceDirectory = 'Input'
    ClassPathology = "both"
    
    print("################################################################\n Clearing Output Files\n")
    clearOutputFiles([DestinationDirectory, DestinationDirectory+LabelsDirectory])

    print("################################################################\n Reading CSV & JSON Files\n")
    # BUSBRA images vary in size, whereas BUDaCaD has a consistent size (in pixels)
    idsBUS, widthsBUS, heightsBUS = readCSV(SourceDirectory)

    # Open and read the JSON file
    jsonFile = open(f"{SourceDirectory}\\predictions.json")
    predictions = json.load(jsonFile)

    print("################################################################\n Copying Annotation Files\n")
    fileNames = subprocess.run(f'dir ".\\{SourceDirectory}\\validation" /b', shell=True, capture_output=True, text=True)
    fileNames = fileNames.stdout
    fileNames = fileNames.split("\n")
    fileNames = fileNames[0:len(fileNames)-1]
    filePaths = []
    for file in fileNames:
        filePaths.append(f"{SourceDirectory}\\validation\\{file}")
    copyFiles(filePaths, DestinationDirectory+LabelsDirectory)

    print("################################################################\n Visualising Predicted Annotations\n")
    # Scans through 
    for pred in predictions:
        if pred["image_id"][0:2] == "IM":                   #BUDaCaD images are the same size
            imageHeight = 600
            imageWidth = 700
        else:
            busImageIndex = idsBUS.index(pred["image_id"])  #BUSBRA images vary in size
            imageWidth = widthsBUS[busImageIndex]
            imageHeight = heightsBUS[busImageIndex]
        BBOX = pred["bbox"] # Format x, y (top left, x is small, y high) 
        # predictions.json is one-indexed wheras the class labels are zero-indexed
        if ClassPathology == "both":
            iClass = pred["category_id"] - 1 + 2
        else:
            iClass = pred["category_id"] - 1 + 1

        iXc, iYc, iWidth, iHeight = convertBBOX(imageWidth, imageHeight, BBOX)
        annotationFile = open(f"{DestinationDirectory}{LabelsDirectory}\\{pred["image_id"]}.txt", "a")
        annotationFile.write(f"\n{iClass} {iXc} {iYc} {iWidth} {iHeight}\n")
        annotationFile.close()        

    print("################################################################\n Creating CVAT Files\n")
    createCVATFiles(ClassPathology, fileNames, DestinationDirectory)

print("Start")
main()
print("End")
'''
JSON Annotation Outputs
{
SINGLE 
    "image_id": "bus_0680-s",   # IMG id
    "category_id": 1,           # 1 = benign(0), 2 = malignant(1)
    "bbox": [
        234.062,            # x top left corner
        140.077,            # y top left corner
        160.971,            # width
        78.016              # height
    ],
    "score": 0.86259        # Confidence
},

image_id = image name   category_id = config.yaml class number + 1 
x_y coordinates:    x1, y1, x2, y2
'''



