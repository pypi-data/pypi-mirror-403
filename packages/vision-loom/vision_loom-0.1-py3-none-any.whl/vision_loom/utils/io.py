import os 
from PIL import Image 

# Creating a generator so I can save storage in the RAM 
def load_images(path): #Either single file or folder 
    if os.path.isfile(path):
        image = Image.open(path)
        yield path, image 

    else:
        for file_name in os.listdir(path): #Assuming this is the string of the folder containing images 
            if file_name.lower().endswith((".jpg", ".png", ".jpeg")):
                full_path = os.path.join(path, file_name)
                image = Image.open(full_path)
                yield full_path, image 