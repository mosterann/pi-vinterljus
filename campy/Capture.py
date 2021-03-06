#!/usr/bin/python
# -*- coding: utf-8 -*-

import StringIO
import subprocess
import os
import sys
import time
from datetime import datetime
from PIL import Image
from SocketClient import SocketClient
import pygame
import pygame.camera
from cv2 import *


import threading


class Capture(threading.Thread):


    def __init__(self):


        # Threading init
        threading.Thread.__init__(self)
        self.setName = "Capture"
        self.daemon = True
        
        
        # Threshold (Amount of pixel color change)
        self.threshold = 40
        # Sensitivity (Amount of pixels needed to signal motion detected)
        self.sensitivity = 200

        # Init matrix
        self.matrixSize = 20
        self.squareWidth = self.imageWidth/self.matrixSize
        self.squareHeight = self.imageHeight/self.matrixSize
        self.matrix = [[0 for i in range(self.matrixSize)] for j in range(self.matrixSize)]

        # Activate uv4l device:
        os.system("sudo pkill uv4l")
        os.system("sudo uv4l --driver raspicam --auto-video_nr --extension-presence=1 --encoding rgba --width 320 --height 240 --nopreview")

        pygame.init()
        pygame.camera.init()

        self.cam = pygame.camera.Camera("/dev/video0",(320,240))
            
        self.oldSurface = None
        self.newSurface = None

    def run(self):
        self.cam.start()
        self.captureImages()
        # self.matrixDetection()


    def captureImages(self):
        #print "start"
        self.oldSurface = self.cam.get_image()
        #time.sleep(0.5)
        print "First picture taken"
        while True:
            try:
                #time.sleep(1)
                self.newSurface = self.cam.get_image()
                self.detectMotion(0)
                #print "Alive"
                time.sleep(0.01)
                self.oldSurface = self.newSurface
            except KeyboardInterrupt:
                self.cam.stop()
                pygame.quit()
                sys.exit(1)


    # Test
    def detectMotion(self, oldValue):

        changedPixels = 0
        pixdiff = 0
        for x in range(self.newSurface.get_width()):
            for y in range(self.newSurface.get_height()):
                newColor = self.newSurface.get_at((x,y))
                oldColor = self.oldSurface.get_at((x,y))
                # Check pixel diffrence in the green channel
                #print str(newColor) + " - " + str(oldColor)
                pixdiff = abs(newColor[0] - oldColor[0])
                #print str(pixdiff) + " " + str(self.threshold)
                # time.sleep(0.05)
                if pixdiff > self.threshold:
                    changedPixels += 1
                    print changedPixels


                if changedPixels > self.sensitivity:
                    #print "Motion Detected"
                    return 5
        
        print "Motionless"
        if(oldValue > 0):
            oldValue = oldValue - 1
        return oldValue





            
        
    
    # Capture a small test image (for motion detection)
    def captureTestImage(self):
        imageData = StringIO.StringIO()
        #imageData.write(subprocess.check_output(self.command, shell=True))
        imageData.seek(0)
        im = Image.open(imageData)
        buffer = im.load()
        imageData.close()
        return im, buffer


    # Help function for matrixDetection (DETECTS MOTION)
    def motionDetection(self, matrixX, matrixY, oldValue):
        # Count changed pixels
        changedPixels = 0
        for x in xrange(0, self.squareWidth):
            xPos = matrixX*self.squareWidth + x
            # Scan one line of image then check sensitivity for movement
            for y in xrange(0, self.squareHeight):
                yPos = matrixY*self.squareHeight + y
                # Just check green channel as it's the highest quality channel
                pixdiff = abs(self.buffer1[xPos,yPos][1] - self.buffer2[xPos,yPos][1])
                if pixdiff > self.threshold:
                    changedPixels += 1

                # If a motion should be counted as detected
                if changedPixels > self.sensitivity:   
                    # Add motion activity
                    #print "Motion"
                    return 5
        
        # Remove motion activity 
        if(oldValue > 0):
            oldValue = oldValue - 1
        return oldValue
        
    # Check for motion in diffrent parts of the image
    def matrixDetection(self):

        # Get first image
        self.image1, self.buffer1 = self.captureTestImage()

        while (True):
            # Putting thread to sleep so CPU LOAD will decrease
            time.sleep(0.01)
            
            # Get comparison image
            self.image2, self.buffer2 = self.captureTestImage()
            
            # For each position in the matrix check for motion
            for x in xrange(self.matrixSize):
                for y in xrange(self.matrixSize):
                    matrixValue = self.matrix[x][y]
                    self.matrix[x][y] = self.motionDetection(x,y, matrixValue)
 
            # Swap comparison buffers
            self.image1  = self.image2
            self.buffer1 = self.buffer2
            #self.sock.sendMatrix(self.matrix)
            
