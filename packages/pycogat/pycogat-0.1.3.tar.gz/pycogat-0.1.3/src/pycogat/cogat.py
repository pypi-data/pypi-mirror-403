import pdfplumber as pdfp
import pypdf
from pypdf import PdfReader,PdfWriter
import string as str
import pandas as pd
import numpy as np

# CogAT Split 
def cogat_split(pdf_object, id_char):
    """
    Splits CogAT Score reports based on a students id

    Parameters
    ----------
    pdf_object: string
        The file path of the CogAT Score Report
    id_char: int
        The number of characters in the local id of the student
    """
    reader = PdfReader(pdf_object)
    writer = PdfWriter() #--> instantiating PDF Writer
    page_len = len(reader.pages) #--> returning number of pages

    # variables
    search_text = 'Student ID: ' #--> substring search
    search_text_len = len(search_text) #--> len object of the substring
    student_id_len = id_char  #--> len object of local student id
    student_id = [] #--> creating an empty list
    
    # opening pdf with pdfplumber and searching for text using a for loop
    with pdfp.open(pdf_object) as pdf:
        for pages in pdf.pages:
            text = pages.extract_text_simple() #--> creating string object
            start = text.find(search_text) #--> assigning the index of the search text to start variable
            end = start +  search_text_len + student_id_len #--> assigning the index to stop extracting text to the end variable
            # indexing string object to extract text, splitting on ':', returning numeric part of text, and removing empty spaces
            student_id.append(text[start:end].split(':')[1].strip()) #--> appening extracted text from the PDF to list

    list_len = len(student_id)

    count = 0 #--> creating count object with a value of 0, each iteration through the for loop increases by 1 from the previous value
    qa = page_len == list_len #--> QA check to ensure that if there is an error, the for loop does not run
    if qa == True: #--> conditional statement
    
            for page_num in range(len(reader.pages)): #--> range of page numbers
                writer = PdfWriter() #--> resets the writer object in each iteration of the loop
                page_name = student_id[page_num] #--> returns other id based on indexing of the student_id list
                writer.add_page(reader.pages[page_num]) #--> adding pages to writer based on page number
                with open(f'{page_name}.pdf','wb') as f: #--> file writing
                    writer.write(f)
                
                count += 1 
    
            print(f'{count} PDF documents were successfully created')  #--> print statement to confirm that documents were created        