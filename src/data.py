# -*- coding: utf-8 -*-
"""
Created on Tue Dec  5 17:45:06 2017

@author: LM
"""
import os
import platform
import numpy as np
from PIL import Image
import torch.utils.data as data
import torch


def isImage(filename):
    """
    a file is a image? via extension
    """
    return any(filename.endswith(extension) for extension in [".png", ".jpg", ".jpeg", ".bmp"])

def numpyRGB2Image(img_np):
    """
    img_np is a RGB mode image, numpy type,dtype = np.uint8
    return a Image.Image type,RGB mode
    """
    img_rgb = Image.fromarray(img_np.transpose(1,2,0))
    return img_rgb
    
    
def numpyYCbCr2Image(img_np):
    """
    img_np is a YCbCr mode image, numpy type,dtype = np.uint8
    return a Image.Image type,RGB mode
    """
    Y  = Image.fromarray(img_np[0])     # 2dim
    Cb = Image.fromarray(img_np[1])
    Cr = Image.fromarray(img_np[2])
    img_YCbCr = Image.merge('YCbCr',(Y,Cb,Cr))
    img_rgb = img_YCbCr.convert('RGB')
    return img_rgb
    

def loadImgRGB2Numpy(filepath,down_scale = None,up_scale =None):
    """
    load a rgb image to numpy(channel * H * W)
    dtype = np.uint8 (make the data easy to Storage)
    down_scale: if is not None,down scale 
    up_scale:   if is not None,up sacle 
    """
    img = Image.open(filepath)  
    if down_scale is not None:
        W,H = img.size
        img = img.resize((int(W*down_scale),int(H*down_scale) ), Image.BICUBIC)
    if up_scale is not None:
        W,H = img.size
        img = img.resize((W*up_scale,H*up_scale),Image.BICUBIC)
    img = np.array(img).transpose(2, 0, 1)  # Image=>numpy.array
    
    return img

def loadImgYCbCr2Numpy(filepath,down_scale = None,up_scale =None):
    """
    load image Y channel to numpy(1 * H * W)
    dtype = np.uint8 (make the data easy to Storage)
    down_scale: if is not None,down scale 
    up_scale:   if is not None,up sacle 
    """
    img = Image.open(filepath)  
    if down_scale is not None:
        W,H = img.size
        img = img.resize((int(W*down_scale),int(H*down_scale)),Image.BICUBIC)
    if up_scale is not None:
        W,H = img.size
        img = img.resize((W*up_scale,H*up_scale),Image.BICUBIC)
    img_YCbCr = img.convert('YCbCr')        # change image mode
    img_YCbCr = np.array(img_YCbCr).transpose(2, 0, 1)  # Image=>numpy.array
        
    return img_YCbCr


def cut2normal(img_np,cut_size = 24):
    """
    cut a numpy(channel * H * W ) to normal size
    """
    shape = img_np.shape
    assert len(shape) == 3,"img_np is not 3 dim"
    nH,nW = shape[-2]//cut_size, shape[-1]//cut_size
    c = shape[0]    # channels
    img = np.empty((nH*nW*c,cut_size,cut_size),dtype=img_np.dtype)
    index = 0
    for i in range(nH):
        for j in range(nW):
            img[index*c:(index+1)*c,:,:] = img_np[:,i*cut_size:(i+1)*cut_size,j*cut_size:(j+1)*cut_size]
            index += 1 
            
    return img

def numpy2Tensor(img_np):
    """
    np.uint8[0,255] => torch.Tensor[0.0,1.0]
    """
    img_np = torch.from_numpy(img_np)
    return img_np.float().div(255)
 

def tensor2Numpy(img_tensor,normalize = True):
    """
    torch.Tensor[0.0,1.0] => np.uint8[0,255]
    """
    img_np = img_tensor.numpy()*255
    if normalize:
        img_np[img_np < 0.0] = 0
        img_np[img_np > 255.0] = 255
    return np.array(img_np,dtype = np.uint8)
 

class img2data(object):
    """
    transform images as numpy(dtype = np.uint8) into data storage in disk
    """
    def __init__(self,hr_dir, lr_dir = None,hr_size = 96,lr_size =24,down_scale = None, up_scale = None,img_num = 800):
        """
        hr_size: hr iamges cut to hr_size*hr_size 
        lr_size: lr iamges cut to lr_size*lr_size
        down_scale: if the lr images need to down scale, if lr_dir is None,
                    we need down sacle the hr image to the lr image
        up_scale:if we need to up the lr image to the same size of hr image, 
                    using up_scale,make lr_size = hr_size.
        """
        self.hr_size    = hr_size
        self.lr_size    = lr_size 
        self.down_scale = down_scale
        self.up_scale   = up_scale
        self.hr_paths   = [os.path.join(hr_dir, x) for x in os.listdir(hr_dir) if isImage(x)]
        self.hr_paths.sort()
        if lr_dir == None:  # downsample the hr iamges to lr images
            self.lr_paths = self.hr_paths
        else:
            self.lr_paths   = [os.path.join(lr_dir, x) for x in os.listdir(lr_dir) if isImage(x)]
            self.lr_paths.sort()
        assert len(self.hr_paths) == len(self.lr_paths),"hr_dir,lr_dir have the image num is not the same"
        # get the first img_num images
        if img_num < len(self.hr_paths):
            self.lr_paths = self.lr_paths[0:img_num]
            self.hr_paths = self.hr_paths[0:img_num]
            self.img_num    = img_num
        else:
            self.img_num = len(self.hr_paths)
        
        # save rgb image, 3 channel every image
        self.lr = np.array([],dtype = np.uint8).reshape(-1,self.lr_size,self.lr_size)
        self.hr = np.array([],dtype = np.uint8).reshape(-1,self.hr_size,self.hr_size)
        
        # save images' Y channel
        self.lrY = np.array([],dtype = np.uint8).reshape(-1,self.lr_size,self.lr_size)
        self.hrY = np.array([],dtype = np.uint8).reshape(-1,self.hr_size,self.hr_size)
        
        self.lrRGBY = np.array([],dtype = np.uint8).reshape(-1,self.lr_size,self.lr_size)
        self.hrRGBY = np.array([],dtype = np.uint8).reshape(-1,self.hr_size,self.hr_size)
    
    def loadImgRGB(self):
        for hr_path in self.hr_paths:
            imgs = cut2normal(loadImgRGB2Numpy(hr_path),cut_size = self.hr_size)
            self.hr = np.concatenate((self.hr,imgs),axis=0) # concat
        for lr_path in self.lr_paths:
            img = loadImgRGB2Numpy(lr_path, down_scale = self.down_scale, up_scale = self.up_scale)
            imgs = cut2normal(img,cut_size = self.lr_size)
            self.lr = np.concatenate((self.lr,imgs),axis=0) 
    
    def saveImgRGB(self,save_path):
        np.savez(save_path,lr = self.lr, hr = self.hr)
        
    def loadImgYChannel(self):
        """
        load images' Y channel
        """
        for hr_path in self.hr_paths:
            y = loadImgYCbCr2Numpy(hr_path)[0:1,:,:]
            ys = cut2normal(y, cut_size = self.hr_size)
            self.hrY = np.concatenate((self.hrY,ys),axis=0) # concat
        for lr_path in self.lr_paths:
            y = loadImgYCbCr2Numpy(lr_path, down_scale = self.down_scale, up_scale = self.up_scale)[0:1,:,:]
            ys = cut2normal(y, cut_size = self.lr_size)
            self.lrY = np.concatenate((self.lrY,ys),axis=0) 
    
    def saveImgYChannel(self,save_path):
        """
        save images' Y channel into disk
        """
        np.savez(save_path,lr = self.lrY, hr = self.hrY)
    
    def loadImgLrRGB_HrY(self):
        """
        load lr images' RGB channel
        load hr images' Y channel
        """
        # load lr rgb mode
        for lr_path in self.lr_paths:
            img = loadImgRGB2Numpy(lr_path, down_scale = self.down_scale, up_scale = self.up_scale)
            imgs = cut2normal(img, cut_size = self.lr_size)
            self.lr = np.concatenate((self.lr,imgs),axis=0) 
        # load hr y mode
        for hr_path in self.hr_paths:
            y = loadImgYCbCr2Numpy(hr_path)[0:1,:,:]
            ys = cut2normal(y, cut_size = self.hr_size)
            self.hrY = np.concatenate((self.hrY,ys),axis=0) # concat
    def saveImgLrRGB_HrY(self,save_path):
        """
        save lr images' RGB channel and hr images' Y channel,to disk
        """
        np.savez(save_path,lr = self.lr, hr = self.hrY)   
        
    
        
    def loadImgLrRGBY_HrRGBY(self):
        """
        load lr images' RGB channel
        load hr images' Y channel
        """
        # load lr rgb mode
        for lr_path in self.lr_paths:
            rgb = loadImgRGB2Numpy(lr_path, down_scale = self.down_scale, up_scale = self.up_scale)
            y = loadImgYCbCr2Numpy(lr_path, down_scale = self.down_scale, up_scale = self.up_scale)[0:1,:,:]
            rgby = np.concatenate((rgb,y),axis = 0) # concat at axis = 0
            imgs = cut2normal(rgby, cut_size = self.lr_size)
            self.lrRGBY = np.concatenate((self.lrRGBY,imgs),axis=0) 
        # load hr y mode
        for hr_path in self.hr_paths:
            rgb = loadImgRGB2Numpy(hr_path)
            y = loadImgYCbCr2Numpy(hr_path)[0:1,:,:]
            rgby = np.concatenate((rgb,y),axis = 0) # concat at axis = 0
            imgs = cut2normal(rgby, cut_size = self.hr_size)
            self.hrRGBY = np.concatenate((self.hrRGBY,imgs),axis=0) 
    
    def saveImgLrRGBY_HrRGBY(self,save_path):
        """
        save lr images' RGB channel and hr images' Y channel,to disk
        """
        np.savez(save_path,lr = self.lrRGBY, hr = self.hrRGBY)    
        

 


class DIV2K(data.Dataset):
    """
    load DIV2K data set to train the SRResNet
    """
    def __init__(self,dataPath,in_channels =3,out_channels = 3):
        super(DIV2K,self).__init__()
        
        dt = np.load(dataPath)
        self.lr = dt['lr']
        self.hr = dt['hr']
        self.in_ch = in_channels
        self.out_ch= out_channels
    
    def __getitem__(self, index):
        """
        get the index item
        """
        # np.uint8(0~255) => folatTensor (0.0~1.0)
        lr = numpy2Tensor(self.lr[index*self.in_ch:(index+1)*self.in_ch,:,:])
        hr = numpy2Tensor(self.hr[index*self.out_ch:(index+1)*self.out_ch,:,:])
        
        return lr,hr
        
    def __len__(self):
        """
        get the data lens
        """
        
        return self.lr.shape[0]//self.in_ch
    

class DiscData(data.Dataset):
    """
    load DIV2K data lr hr,
    """
    def __init__(self,dataPath,channels =3):
        super(DiscData,self).__init__()
        
        dt = np.load(dataPath)
        #self.lr = dt['lr']
        #self.hr = dt['hr']
        self.ch = channels
        self.len = dt['lr'].shape[0]//self.ch
        self.data = np.concatenate((dt['lr'],dt['hr']) )
        self.label = np.concatenate((np.zeros(self.len,dtype=np.float32),
                                     np.ones(self.len,dtype=np.float32)),
                                    axis = 0).reshape(-1,1)
        
    
    def __getitem__(self, index):
        """
        get the index item
        """
        # np.uint8(0~255) => folatTensor (0.0~1.0)
        
       
        data = numpy2Tensor(self.data[index*self.ch:(index+1)*self.ch,:,:])
        #label = np.asarray(self.label[index])       # number => array
        label = torch.from_numpy(self.label[index]).float()      # must be array,if number(asarray)
        return data,label

        
    def __len__(self):
        """
        get the data lens
        """
        
        return 2*self.len
    
        


def main():
    """
    convert images into data
    """
    sysstr = platform.system()
    
    if(sysstr =="Windows"): # Windows
        root_dir = r'E:\Data\DIV2K'
        hr_dir = r'E:\Data\DIV2K\DIV2K_train_HR'
        lr_dir = r'E:\Data\DIV2K\DIV2K_train_LR_bicubic\X4'
    elif(sysstr == "Linux"): # Linux
        root_dir = r'/home/we/devsda1/lm/DIV2K'
        hr_dir = r'/home/we/devsda1/lm/DIV2K/DIV2K_train_HR'
        lr_dir = r'/home/we/devsda1/lm/DIV2K/DIV2K_train_LR_bicubic/X4'
    else:
        print ("don't support the system")
    
    
    #dt = img2data(hr_dir, lr_dir, hr_size = 96,lr_size =96, img_num = 200)
    #dt.loadImgRGB()
    #dt.saveImgRGB(os.path.join(root_dir,'DIV2K_Ch[RGB][RGB]_Size[24][96]_num[200].npz'))
    #dt.loadImgYChannel()
    #dt.saveImgYChannel(os.path.join(root_dir,'DIV2K_Ch[Y][Y]_Size[24][96]_num[200].npz')
    #dt.loadImgLrRGB_HrY()
    #dt.saveImgLrRGB_HrY(os.path.join(root_dir,'DIV2K_Ch[RGB][Y]_Size[24][96]_num[200].npz')
    
    # lr imgae scale *4 (24 => 96),hr image (96)
    dt = img2data(hr_dir, lr_dir,up_scale =4, hr_size = 96,lr_size =96, img_num = 200)
    dt.loadImgRGB()
    dt.saveImgRGB(os.path.join(root_dir,'DIV2K_Ch[RGB][RGB]_Size[96][96]_num[200].npz'))
    
    

if __name__ == "__main__":
    main()