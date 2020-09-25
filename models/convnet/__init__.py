from keras.models import Sequential
from keras.layers.core import Dense, Dropout, Activation, Flatten
from keras.layers.convolutional import Convolution2D, MaxPooling2D
from keras.utils import np_utils
from keras.preprocessing.image import img_to_array

import numpy as np

#image manipulation
import os
from PIL import Image
import theano
theano.config.optimizer = "None"

#sklearn to modify data
from sklearn.cross_validation import train_test_split


class ImageClassifier(object):
    def __init__(self, catagory):
        pass

data_path = r"C:\Marumo\Applications\FileAlchemy\Training Data\Images\animal"
os.chdir(data_path)

m, n = 50, 50

path1 = "input"
path2 = "data"

classes = os.listdir(data_path)
x = []
y = []

for folder in classes:
    print(folder)
    class_path = os.path.join(data_path, folder)
    img_files = os.listdir(class_path)

    for img_file in img_files:
        img_path = os.path.join(class_path, img_file)
        img = Image.open(img_path)
        img = img.convert(mode='RGB')
        img = img.resize((m, n))
        img = img_to_array(img) / 255  # make image pixel values between 0 and 1
        img = img.transpose(2, 0, 1)
        img = img.reshape(3, m, n)

        x.append(img)
        y.append(folder)

x = np.array(x)
y = np.array(y)

batch_size = 32
num_classes = len(classes)
num_epochs = 20
num_filters = 32
num_pool = 2
num_conv = 3

x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2, random_state=4)

#turn string classes into sparse arrays
uniques, id_train = np.unique(y_train, return_inverse=True)
Y_train = np_utils.to_categorical(id_train, num_classes)
uniques, id_test = np.unique(y_test, return_inverse=True)
Y_test = np_utils.to_categorical(id_test, num_classes)

model = Sequential()
model.add(Convolution2D(
    filters=num_filters, kernel_size=num_conv, strides=num_conv, border_mode="same", input_shape=x_train.shape[1:])
)
model.add(Activation('relu'))
model.add(Convolution2D(
    filters=num_filters, kernel_size=num_conv, border_mode="same", strides=num_conv, input_shape=x_train.shape[1:])
)
model.add(Activation('relu'))
model.add(MaxPooling2D(pool_size=(num_pool, num_pool), input_shape=(5, 5)))
model.add(Dropout(0.5))
model.add(Flatten())
model.add(Dense(128))
model.add(Dropout(0.5))
model.add(Dense(num_classes))
model.add(Activation('softmax'))

model.compile(loss="categorical_crossentropy", optimizer="adadelta", metrics=['accuracy'])
model.fit(
    x=x_train,
    y=y_train,
    batch_size=batch_size,
    nb_epoch=num_epochs,
    verbose=1,
    validation_data=(x_test, Y_test)
)


def format_img(path):
    img = Image.open(path)
    img = img.resize((m, n))
    img = img_to_array(img)/255
    img = img.transpose(2, 0, 1)
    img = img.reshape(3, m, n)
    return np.array([img])

predictions = model.predict(format_img(r"C:\Marumo\Applications\FileAlchemy\t.jpg"))
