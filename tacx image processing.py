import matplotlib.pyplot as plt
import urllib.request
import numpy as np
import itertools
import cv2
import ssl
import os
import re
ssl._create_default_https_context = ssl._create_unverified_context

def process_bar(img, max_power, duration):
    def round_time(time):
        if time/60 >= 1:
            return float(round(time/60))
        else:
            return round(time/60, 2)
    def myround(x, base=5):
        return base * round(x/base)
    # Erosion for deleting all the noise
    kernel = np.ones((7,7),np.uint8)
    erosion = cv2.erode(img,kernel,iterations = 1)
    img_dilation = cv2.dilate(erosion, np.ones((6,6),np.uint8), iterations=1) 
    # plt.imshow(img_dilation)
    # plt.show()
    # Converting image to B&W
    (thresh, blackAndWhiteImage) = cv2.threshold(img_dilation, 127, 255, cv2.THRESH_BINARY)
    # Mask to map all 0
    mask = np.uint8(np.where(blackAndWhiteImage == 0, 0, 1))
    # Sum of all zeros per column
    col_counts = cv2.reduce(mask, 0, cv2.REDUCE_SUM, dtype=cv2.CV_32SC1)
    col_counts_list = col_counts.flatten().tolist()
    # Disregard the 0 power noise
    col_counts_list = [myround(item) for item in col_counts_list if item > 0]
    # Map to (power, length_on_x)
    Y = [(x, len(list(y))) for x, y in itertools.groupby(col_counts_list)]
    # print("Y:", Y)
    maxY = max(Y,key=lambda item:item[0])[0]
    # print("maxY:", maxY)
    power_scale = maxY/max_power
    # print("power_scale:", power_scale)
    maxX = len(col_counts_list)
    # print("maxX:", maxX)
    time_scale = maxX/duration
    # print("time_scale:", time_scale)
    Y_new = [(round_time(y/time_scale), round(x/power_scale)) for x, y in Y]
    Y_nn = [item for item in Y_new if item[1] > 0]
    return Y_nn 

def reformat_tuples(py_hist):
    reformated_tuples = []
    reformated_tuples.append((0, py_hist[0][1]))
    # reformated_tuples.append((py_hist[0][0], py_hist[0][1]))
    # reformated_tuples.append((py_hist[0][0], py_hist[1][1]))
    time_sum = 0
    for k in range(0,len(py_hist)-1):
        time_sum = round(time_sum + py_hist[k][0],2)
        reformated_tuples.append((time_sum, py_hist[k][1]))
        reformated_tuples.append((time_sum, py_hist[k+1][1]))
    reformated_tuples.append((time_sum + py_hist[len(py_hist)-1][0], py_hist[len(py_hist)-1][1]))
    return reformated_tuples


def image_from_url(diction):
    for item in diction:
        resp = urllib.request.urlopen(item["url"])
        image = np.asarray(bytearray(resp.read()), dtype="uint8")
        image = cv2.imdecode(image, cv2.IMREAD_COLOR)
        item["image"] = image
    return diction

def images_from_directory(directory_in_str):
    # directory_in_str = "/Users/elenatoshevska/Downloads/tacx/ew"
    diction = []
    directory = os.fsencode(directory_in_str)
    for file in os.listdir(directory):
        try: 
            filename = os.fsdecode(file)
            # base = os.path.basename(path)
            base_filename = os.path.splitext(filename)[0]
            # print("filename",filename)
            parameters = filename.split(" - ")
            # print(parameters)
            parameters = parameters[len(parameters)-1]
            parameters = parameters.replace(":", " ")
            parameters = parameters.replace("/", " ")
            parameters = re.findall(r'\d+', parameters)
            # print ("Parameters is: ", parameters)
            duration_seconds = int(parameters[0]) * 60
            max_power = int(parameters[1])
            print("Filename is: " + filename)
            print("Time duration is: " + str(parameters[0]) + ", and max power is: " + str(parameters[1]))
            path = directory_in_str + "/" + filename
            img = cv2.imread(path,0) # reads image 'opencv-logo.png' as grayscale
            temp = {
                "path": filename,
                "max_power": max_power,
                "duration_seconds": duration_seconds,
                "base_filename": base_filename,
                "image": img
            }
            diction.append(temp)
        except:
            print("There was a problem at ", os.fsdecode(file))
            continue
    return diction

def process_and_save(diction, directory_in_str = ""):
    text_files = []
    for item in diction:
        try: 
            YE = process_bar(item["image"], item["max_power"], item["duration_seconds"])
            # print(YE)
            YE_reformat = reformat_tuples(YE)
            tuple_strings = ['%.2f	%s' % tuple for tuple in YE_reformat]
            result = '\n'.join(tuple_strings)
            beginning = """[COURSE HEADER]
            VERSION = 2
            UNITS = ENGLISH
            DESCRIPTION = 
            FILE NAME = """ + item["base_filename"] +  """
            FTP = 100
            MINUTES WATTS
            [END COURSE HEADER]
            [COURSE DATA]"""
            whole_text = beginning + "\n" + result + "\n[END COURSE DATA]"
            if directory_in_str:
                text_file = open(directory_in_str + "/" + item["base_filename"] + ".txt", "w")
                n = text_file.write(whole_text)
                text_file.close()
            text_files.append(whole_text)
        except:
            print("There was a problem at ", item["base_filename"])
            continue
    return text_files

def main():
    # Local directory to store output
    directory_imgs_for_output = "/Users/elenatoshevska/Downloads/tacx/new"


    # If you want to process a list of urls
    to_process_from_urls = [{
        "url": "https://tacx.com/wp-content/uploads/2018/01/erg-trainingII-1-600x339.png",
        "max_power": 3,
        "duration_seconds": 90,
        "base_filename": "blabla"
    }]
    to_process_from_urls = image_from_url(to_process_from_urls)
    converted_text_files = process_and_save(to_process_from_urls, directory_imgs_for_output)  # If you want to store locally
    converted_text_files = process_and_save(to_process_from_urls)


    # If you want to process a whole local directory
    # All files whould be stored with the name in format "blablabla - 70/85.png", where 70 is the duration in minutes and 85 is the max power
    directory_imgs_for_input = "/Users/elenatoshevska/Downloads/tacx/new"
    to_process_from_directory = images_from_directory(directory_imgs_for_input)
    converted_text_files = process_and_save(to_process_from_directory, directory_imgs_for_output) # If you want to store locally
    converted_text_files = process_and_save(to_process_from_directory)

if __name__ == "__main__":
    main()