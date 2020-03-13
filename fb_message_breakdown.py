import csv
import pandas as pd
import matplotlib.pyplot as plt
import threading
import time
from tkinter import Tk
from tkinter.filedialog import askdirectory
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()
from bs4 import  BeautifulSoup
from os import listdir
from os.path import isfile, join


csvList = []
global_lock = threading.Lock()



def readMessageAndWrite(path,output):
    startTime = time.perf_counter()
    #array for data
    print("starting:" +path)
    rows = []    
    with open(path , encoding="utf-8") as page:
        soup = BeautifulSoup(page, "html.parser")
        #grabs the main div with all ad items
        contents  =soup.find("div", class_="_4t5n")
        
        #grab each ad item. This will contain information and timestamp
        ad_list = contents.find_all("div", class_="uiBoxWhite")
        
        for item in ad_list:
            name = item.find("div", class_="_2lel")
            message = item.find("div", class_="_2let")
            date = item.find("div",class_="_2lem")
            picture = item.find("img", class_="_2yuc")
            if name is not None:
                name_text = item.find("div", class_="_2lel").get_text()
                message_text = item.find("div", class_="_2let").get_text()
                date_text = item.find("div",class_="_2lem").get_text()         
            
                #print(name_text, " | ", message_text, " | ", date_text)
                if picture is not None:
                    picture_src = picture.get("src")
                   # print(picture_src)
                else:
                    picture_src = ""
    
                row = {
                    "user":name_text,
                    "message": message_text,
                    "date": date_text,
                    "picture": picture_src
                }
                rows.append(row)
                
                
        while global_lock.locked():
            time.sleep(1)
            continue
    
        global_lock.acquire()
        for item in rows:
            csvList.append(item)
        global_lock.release()                
                
        print("Done:"+ path)
        endTime = time.perf_counter()
        totalTime = endTime-startTime
        print("**********************")
        print("computation time: "+str(totalTime))        
            

 
 
 
def analyze(path):
    
    dateparse = lambda x: pd.datetime.strptime(x, '%b %d, %Y, %H:%M %p')
    messages = pd.read_csv(path, parse_dates=["date"], date_parser=dateparse)
    messages['message'] = messages.message.apply(str)
    #print(messages.dtypes)
    # show messages every month
    
    #This line is specific to 3 of us need GF
    #messages = messages[messages["date"]>pd.Timestamp(2012,1,1)]
    
    
    messages_over_time = messages.set_index("date")
    messages_tally = messages_over_time.resample("M").count()
    
    print("="*50)
    print("MESSAGE TOTAL") 
    print(messages["message"].count())
    #print("="*50)
    #print("MESSAGE PER MONTH TALLY")
    #print(messages_tally["message"])
    plot1 = plt.figure(1)
    plt.plot(messages_tally["message"])
    plot1.show()
    
    #Show messages per person
    print("="*50)
    print("MESSAGES PER PERSON")    
    print(messages['user'].value_counts())
    
    

     
    #Show Averege/max message length per user
    print("="*50)
    print("AVERAGE MESSAGE LENGTH")
    messages["message_len"] = messages['message'].apply(len)
    print(messages.groupby('user').mean().message_len)
    
    print("="*50)
    print("MAX MESSAGE LEN PER PERSON")      
    print(messages.groupby('user').max().message_len)
    
    
    print("="*50)
    print("Messages Per Day of Week")      
    messages["weekDay"] = messages["date"].dt.dayofweek
    messagesByDay = messages.groupby("weekDay")
    messagesByDay = messages["weekDay"].value_counts(sort=False)
    plot2 = plt.figure(2)
    y_pos = [0,1,2,3,4,5,6]
    objects = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    plt.bar(y_pos, messagesByDay.values,align="center", alpha=0.5)
    plt.xticks(y_pos, objects )
    plt.xticks(rotation=45)
    plt.title("Messages Per Day of the Week")
    plt.ylabel("Messages")
    plot2.show()
    
    
def checkExists(filename):
    
    try:
        open(filename, "x")
        return 0
    except FileExistsError:
        print("file already exists")
        return 1
    except:
        print("other error opening file")
        
def createFileList(path):
    
    onlyfiles = [f for f in listdir(path) if isfile(join(path, f))]
    print(onlyfiles)
    return onlyfiles

def selectMessageFromInbox(path):
    Tk().withdraw() # we don't want a full GUI, so keep the root window from appearing
    filename = askdirectory() # show an "Open" dialog box and return the path to the selected directory
    return filename   
    
def getChatSummary(path):
    splitPath = path.split("/")
    chatname = splitPath[-1]
    chatSummary = chatname.split("_")
    return chatSummary[0]
    

def main():
    startTime = time.perf_counter()
    rootPath = "FacebookData/messages/inbox/"
    fullPath = selectMessageFromInbox(rootPath)
    
    #chatname = "3OfUsAreGettingOldOneOfUsIsActiveForHisAge_0GuHC43b1Q"
    #chatname = "RebeccaThys_dMm5EpevCg"
    #chatnameSummary = "3ofUs" 
    #chatnameSummary = "becs&I"
    chatnameSummary = getChatSummary(fullPath)
    fileNames = createFileList(fullPath)
    output = chatnameSummary+"-messages.csv"
    
    if(not(checkExists(output))):
        with open(output, "w", newline='',encoding="utf-8") as csvfile:
            fieldnames = ["user", "message","date","picture"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()  
        
        
        #Create all the threads    
        threads = []    
        for file in fileNames:
            path = fullPath+"/"+file
            t = threading.Thread(target=readMessageAndWrite, args=(path,output))
            threads.append(t)
            t.start()
            
            #readMessageAndWrite(path,output)
            #print("Done: ",file)

            
        #wait for threads to finish
        for t in threads:
            t.join()
           

    with open(output, "a", newline='',encoding="utf-8") as csvfile:
        fieldnames = ["user", "message","date","picture"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        for item in csvList:
            writer.writerow(item)    
    
    
    analyze(output)
    endTime = time.perf_counter()
    totalTime = endTime-startTime
    print("**********************")
    print("computation time: "+str(totalTime))
    wait = input("Enter to contiue: ")
        
        
main()


