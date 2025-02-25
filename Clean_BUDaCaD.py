import subprocess
import shutil

'''Takes a number and desired length, converts that number into a string and backfills with zeroes to achieve desired length

Args:
    intNumber: The input number in integer form or otherwise
    desiredLength: Desired length of the returned string

Returns:
    String, intNumber backfilled with 0s till the desired length
'''
def backfillZeros(intNumber, desiredLength):    #Backfills a number 
    strNumber = str(intNumber)
    for backfill in range(0, (desiredLength-len(strNumber))):
        strNumber = "0" + strNumber
    return strNumber

'''Cleans the 'Normal' classification subset of the BUDaCaD dataset.
   Renames all files to uniquely named files based on IM-{patientNumber}-{imageNumber}.jpg
   Filters out patient files that are empty or contain annotations 'A_' files implying cancerous Ultrasound
   Copies all suitable images to one directory to be copied into the machine learning model
'''
destinationDirectory = 'Output\\'
sourceDirectory = 'Input\\'
discardPatients = []
manuallyInvalidFiles = [(88, 2), (118, 2), (168, 2), (168, 3), (168, 4), (180, 2)] # (patientNum, imageNum)

for patientNum in range (1, 183): # Length of 'Normal' classified patients in database (BUDaCaD)
    fileNames = subprocess.run(f'dir ".\\Input\\Patient {patientNum}\\Ultrasound" /b', shell=True, capture_output=True, text=True)
    fileNames = fileNames.stdout

    if fileNames[0:2] != "IM":              # Discard any patient files that are empty or contain annotated files prefixed with A_ 
        discardPatients.append(patientNum)        
    else:                                   # Copy and rename any files from a valid Patient
        fileNames = fileNames.split("\n")
        fileNames = fileNames[0:len(fileNames)-1]
        imgNumber = 1
        for file in fileNames: 
            if not (patientNum, imgNumber) in manuallyInvalidFiles:
                shutil.copy(sourceDirectory+f'Patient {patientNum}\\Ultrasound\\{file}', destinationDirectory+f'IM-{backfillZeros(patientNum,4)}-{backfillZeros(imgNumber,4)}.jpg')
            imgNumber += 1

# Output Message
print("Successfully renamed and collated all valid 'Normal' classfied UltraSound data.")
if len(discardPatients) > 0:
    print(f"The following patients were incorrectly classifed or had no image:\n{discardPatients}")

'''
Manual cleaning made to the input data: 
* Files named 'PAtient x' were changed to be correctly capitalised (~6 total changes)
* 'Patient Z' file was removed, which had A_ annotation file

Manually flagged invalid files:
* Patient 88  - Img2, Patient 118 - Img2 = Mammography not UltraSound, deleted from the inputs
* Patient 168 - Img2, Img3, Img4         = Completely black images, deleted from the inputs
* Patient 180 - Img2                     = Contains two side by side US images, incorrect format, deleted from inputs 
'''