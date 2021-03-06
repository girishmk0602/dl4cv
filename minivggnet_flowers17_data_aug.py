# import necessary packages
from sklearn.preprocessing import LabelBinarizer
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from pyimagesearch.preprocessing import ImageToArrayPreprocessor
from pyimagesearch.preprocessing import AspectAwarePreprocessor
from pyimagesearch.datasets import SimpleDatasetLoader
from pyimagesearch.nn.conv import MiniVGGNet
from keras.preprocessing.image import ImageDataGenerator
from keras.optimizers import SGD
from imutils import paths
import matplotlib.pyplot as plt
import numpy as np
import argparse
import os

ap = argparse.ArgumentParser()
ap.add_argument("-d","--dataset", required=True,
    help="path to input dataset")
args = vars(ap.parse_args())

# grab the list of images and then extract the class labels
# from image paths
imagePaths = list(paths.list_images(args["dataset"])) # get all pathnames of files in an array

classNames = [pt.split(os.path.sep)[-2] for pt in imagePaths] # [-2] is sub-dir under images - our classname
classNames = [str(x) for x in np.unique(classNames)] # create an list of unique classnames

# initialise image preprocessors
aap = AspectAwarePreprocessor(64,64)
iap = ImageToArrayPreprocessor()

# load the dataset from disk then scale the raw pixel intensities
# to the range[0,1]
sdl = SimpleDatasetLoader(preprocessors=[aap,iap]) # create loader
(data,labels) = sdl.load(imagePaths,verbose=500)   # loads images into memory
data=data.astype("float")/255.0


# partion the data into training and test sets 75:25
(trainX,testX,trainY,testY)=train_test_split(data,labels,
    test_size=0.25, random_state=42)

# convert the integers to lables
trainY = LabelBinarizer().fit_transform(trainY) #- create one-hot vectors for classnames
testY= LabelBinarizer().fit_transform(testY)


#construct the image generator for data augmentation
aug = ImageDataGenerator(rotation_range=30, width_shift_range=0.1,
        height_shift_range=0.1, shear_range=0.2, zoom_range=0.2,
        horizontal_flip=True, fill_mode="nearest")

# initialise the optimiser and model
print("[INFO] compiling model...")
opt = SGD(lr=0.05)
model = MiniVGGNet.build(width=64, height=64, depth=3,
    classes=len(classNames))
model.compile(loss="categorical_crossentropy", optimizer=opt,
    metrics=["accuracy"])

# train the network
print("[INFO] training network...")
# aug.flow - return (x,y)  x.shape = (32,64,64,3) y.shape = (32,17)
H = model.fit_generator(aug.flow(trainX,trainY,batch_size=32),
    validation_data = (testX,testY),
    steps_per_epoch=len(trainX)//32,
    epochs=100, verbose=1)

# evaluate the network
print("[INFO] evaluating netork...")
predictions = model.predict(testX, batch_size=32)
print(classification_report(testY.argmax(axis=1),
    predictions.argmax(axis=1), target_names=classNames))

plt.style.use("ggplot")
plt.figure()
plt.plot(np.arange(0,100), H.history["loss"], label="train_loss")
plt.plot(np.arange(0,100), H.history["val_loss"], label="val_loss")
plt.plot(np.arange(0,100), H.history["acc"], label="train_acc")
plt.plot(np.arange(0,100), H.history["val_acc"], label="val_acc")
plt.title("Training Loss and Accuracy - Data Aug")
plt.xlabel("Epoch #")
plt.ylabel("Loss/Accuracy")
plt.legend()
plt.show()

# runtime 25s per epoch
# see VGGNET flower17_fig_2.png
