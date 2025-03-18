import json
import subprocess
import os
import csv

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

'''Reads the BUSBRA CSV focussing on returning the size of the images, since they vary

Args:
        sourceDir:      Location of bus_data.csv

Returns:
        ids:        BUSBRA image ids
        widths:     BUSBRA image size widths in pixels
        heights:    BUSBRA image size heights in pixels
        BBOXes:     BUSBRA image BBOXes [xmin, ymin, width, height] in pixels
'''
def readCSV(sourceDir: str):
    ids = []
    BBOXes = []
    pathologies = []
    line_count = 0
    busCSV = open(f"{sourceDir}\\bus_data.csv", 'r')
    csvReader = csv.DictReader(busCSV, delimiter=',')
    for row in csvReader:
        if line_count == 0:
            line_count += 1
        ids.append(str(row["ID"]))
        pathologies.append(str(row["Pathology"]))
        BBOX = row["BBOX"]
        BBOX = BBOX[1:len(BBOX)-1]
        BBOX = BBOX.split(",")
        BBOXes.append(BBOX)
        line_count += 1
    print(f'Read {line_count} BUSBRA csv lines')
    return ids, pathologies, BBOXes

def calcMetrics(gtBBOX: list, predBBOX: list):
    gtXmin, gtYmin = int(gtBBOX[0]), int(gtBBOX[1])
    gtWidth, gtHeight = int(gtBBOX[2]), int(gtBBOX[3])
    gtXmax, gtYmax = gtXmin + gtWidth, gtYmin + gtHeight
    predXmin, predYmin = predBBOX[0], predBBOX[1]
    predWidth, predHeight = predBBOX[2], predBBOX[3]
    predXmax, predYmax = predXmin + predWidth, predYmin + predHeight

    interXmin = max(gtXmin, predXmin)
    interYmin = max(gtYmin, predYmin)
    interXmax = min(gtXmax, predXmax)
    interYmax = min(gtYmax, predYmax)
    
    predArea = predWidth * predHeight
    gtArea = gtWidth * gtHeight
    interArea = (interXmax - interXmin) * (interYmax - interYmin) 
    unionArea = gtArea + predArea - interArea

    APR = interArea / predArea
    ARR = interArea / gtArea
    IoU = interArea / unionArea
    return round(APR, 3), round(ARR, 3), round(IoU, 3)

def toString(confusionMatrix: list, classPathology: str, metricsFile):
    classNull = "normal"
    classA = "tumour"
    classB = ""
    if classPathology == "both":
        classA = "benign"
        classB = "malignant"
    elif classPathology != "none":
        classA = classPathology

    confusionLabel = [classNull + "   ", classA + "   ", classB]
    for row in range(0, len(confusionMatrix[0])):
        rowLabel = confusionLabel[row]
        metricsFile.write(f"GT: {rowLabel} {confusionMatrix[row]}\n")

    metricsFile.write(f"Pred:        {classNull},{classA},{classB}\n")

def main():
    DestinationDirectory = 'Output\\metrics'
    SourceDirectory = 'Input'
    ClassPathology = "both"
    
    print("################################################################\n Clearing Output Files\n")
    clearOutputFiles([DestinationDirectory])

    print("################################################################\n Reading CSV & JSON Files\n")
    # BUSBRA images vary in size, whereas BUDaCaD has a consistent size (in pixels)
    idsBUS, pathologiesBUS, bboxesBUS = readCSV(SourceDirectory)

    # Open and read the JSON file
    jsonFile = open(f"{SourceDirectory}\\predictions.json")
    predictions = json.load(jsonFile)

    metricsFile = open(f"{DestinationDirectory}\\metrics.txt", "w")
    print("################################################################\n Calculating Metrics\n")
    metricsFile.write("Detection Performance Metrics:\n")

    fileNames = subprocess.run(f'dir ".\\{SourceDirectory}\\validation" /b', shell=True, capture_output=True, text=True)
    fileNames = fileNames.stdout
    fileNames = fileNames.split("\n")
    fileNames = fileNames[0:len(fileNames)-1]

    meanCount = 0
    APR = 0
    ARR = 0
    IoU = 0
    F1 = 0



    '''
    APR = [Intersection / Prediction]  
    ARR = [Intersection / GT]
    F1 = 2xAPRxARR/APR+ARR
    '''

    for file in fileNames:
        if file[0:2] != "IM":
            for pred in predictions:
                if file[0:len(file)-4] == pred["image_id"]:
                    busImageIndex = idsBUS.index(pred["image_id"])  #BUSBRA images vary in size
                    gtBBOX = bboxesBUS[busImageIndex]               # [xmin, ymin, width, height]
                    predBBOX = pred["bbox"]                         # [xmin, ymin, width, height]
                    iAPR, iARR, iIoU = calcMetrics(gtBBOX, predBBOX)
                    APR += iAPR
                    ARR += iARR
                    IoU += iIoU
                    meanCount += 1
                    break
    
    meanAPR = APR/meanCount
    meanARR = ARR/meanCount
    meanIoU = IoU/meanCount
    F1 = (2 * meanAPR * meanARR) / (meanAPR + meanARR)
    metricsFile.write(f"Average APR: {meanAPR}\nAverage ARR: {meanARR}\nF1: {F1}\nAverage IoU: {meanIoU}\n")


    metricsFile.write("\n\nConfusion Matrix:\n")
    classDictionary = {"id": [], "gtClass": [], "predClass": []}

    for file in fileNames:
        classDictionary["id"].append(file[0:len(file)-4])
        # Ground Truth
        if file[0:2] != "IM":
            busImageIndex = idsBUS.index(file[0:len(file)-4])
            if ClassPathology != "both" or pathologiesBUS[busImageIndex] == "benign": 
                classDictionary["gtClass"].append(1)
            else: 
                classDictionary["gtClass"].append(2)
        else: 
            classDictionary["gtClass"].append(0)
        
        # Predicition
        foundPrediction = False
        for pred in predictions:
            if file[0:len(file)-4] == pred["image_id"]:
                classDictionary["predClass"].append((pred["category_id"]))
                foundPrediction = True
                break
        
        if not foundPrediction:
            classDictionary["predClass"].append(0)

    if not (len(classDictionary["id"]) == len(classDictionary["gtClass"]) == len(classDictionary["predClass"])):
        print("WARN: Possible error with confusion matrix, predicted and GT classes count are not equal")

    if ClassPathology == "both":    #3x3 matrix, groundTruth-Prediction 
        confusionMatrix = [[0,0,0], #normal-normal, normal-benign, normal-malign
                           [0,0,0], #benign-normal, benign-benign, benign-malign
                           [0,0,0]] #malign-normal, malign-benign, malign-malign
        for id in range(0, len(classDictionary["id"])):
            gtClass = classDictionary["gtClass"][id]
            predClass = classDictionary["predClass"][id]
            confusionMatrix[gtClass][predClass] += 1
    else:
        confusionMatrix = [[0,0],   #2x2 matrix, groundTruth-Prediction 
                           [0,0]]
        for id in range(0, len(classDictionary["id"])):
            gtClass = classDictionary["gtClass"][id]
            predClass = classDictionary["predClass"][id]
            confusionMatrix[gtClass][predClass] += 1

    toString(confusionMatrix, ClassPathology, metricsFile)
    metricsFile.close()
    print("Metrics calculated & Confusion Matrix built")
    '''
    TO DO:
    



    '''   


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



