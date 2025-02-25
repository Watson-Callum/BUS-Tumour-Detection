import csv

def convertBBOX(imageWidth, imageHeight, BBOX):         # BBOX
        Xmin, Ymin = int(BBOX[0]), int(BBOX[1])
        BBOXwidth, BBOXheight = int(BBOX[2]), int(BBOX[3])
        Xc = (Xmin + (BBOXwidth/2))/imageWidth          # Finds centre points of BBoxes, scale 0-1
        Yc = (Ymin + (BBOXheight/2))/imageHeight
        BBOXwidth /= imageWidth
        BBOXheight /= imageHeight                       # Converts size of BBOX into scale 0-1 from number of pixels
        return round(Xc, 6), round(Yc, 6), round(BBOXwidth, 6), round(BBOXheight, 6)

# Create assisting files to check against CVAT to visualise the auto annotations
def createAssistingFiles(filterByType, imageNames):
        classType = filterByType
        if filterByType == "none":
                classType = "tumour"
        elif filterByType == "both":
                classType = "benign\nmalignant"             
        f = open("Output\\obj.names", 'w')
        f.write(f"{classType}")
        f.close()

        classNumber = "1"
        if filterByType == "both":
                classNumber = "2"
        f = open("Output\\obj.data", "w")
        f.write(f"classes = {classNumber}\ntrain = data/train.txt\nnames = data/obj.names\nbackup = backup/")
        f.close()    

        f = open("Output\\train.txt", "w")
        for imageName in imageNames:
                f.write(f"data/obj_train_data/{imageName}.png\n")
        f.close()   

def createAnnotations(filterByType, filterBySide, sampleSize):
        busCSV = open("Input\\bus_data.csv", 'r')
        csvReader = csv.DictReader(busCSV, delimiter=',')
        line_count = 0
        type_count = 0
        side_count = 0
        imageNames = []
        tumourTypes = []
        widths = []
        heights = []
        sides = []
        BBOXes = []
        for row in csvReader:
                if line_count < sampleSize and sampleSize > 0:
                        if line_count == 0:
                                print(f'Column names are {", ".join(row)}')
                                line_count += 1
                        if (filterByType == "benign" or filterByType == "malignant") and row["Pathology"] != filterByType:
                                type_count += 1
                        elif (filterBySide == True) and row["Side"] == "right":
                                side_count += 1
                        else:
                                imageNames.append(str(row["ID"]))
                                tumourTypes.append(str(row["Pathology"]))
                                widths.append(int(row["Width"]))
                                heights.append(int(row['Height']))
                                sides.append(str(row["Side"]))
                                BBOX = row["BBOX"]
                                BBOX = BBOX[1:len(BBOX)-1]
                                BBOX = BBOX.split(",")
                                BBOXes.append(BBOX)
                        line_count += 1
        print(f'Read {line_count} csv lines')

        if filterByType == "benign" or filterByType == "malignant":
                print(f'Filtered out {type_count} images that were not {filterByType}')
        if filterBySide:
                print(f'Filtered out {side_count} images that were taken from the right side')

        percentComplete = 0
        for i in range(0, len(imageNames)):
                f = open(f"Output\\obj_train_data\\{imageNames[i]}.txt", 'w')
                iXc, iYc, iWidth, iHeight = convertBBOX(widths[i], heights[i], BBOXes[i])
                if filterByType == "both" and tumourTypes[i] == "malignant":
                        f.write(f"1 {iXc} {iYc} {iWidth} {iHeight}")          
                else:
                        f.write(f"0 {iXc} {iYc} {iWidth} {iHeight}")
                f.close()
                if (i-1) % round(len(imageNames)/10, 0) == 0:
                        print(f"Creating Image Annotations: {percentComplete}% complete!")
                        percentComplete += 10
        print(f'Processed {line_count} lines.')

        createAssistingFiles(filterByType, imageNames)

print("Start")
TypeFilter = "both"             # "none" | "benign" | "malignant" | "both"
SideFilter = False              # False | True (produces one inage per patient)
SampleSize = 88                 # 0 | x (86)
createAnnotations(TypeFilter, SideFilter, SampleSize)
print("End")

''' Improvements:

* Remove Output folder contents
* Unit Testing 

'''