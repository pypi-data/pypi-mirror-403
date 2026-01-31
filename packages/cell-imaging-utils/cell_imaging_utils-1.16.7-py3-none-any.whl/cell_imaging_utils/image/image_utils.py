from os import stat
import numpy as np
import logging
import typing
import imageio as iio


log = logging.getLogger(__name__)

"""
ImageUtils
------------------
Class that contains some static methods to help handle images
Channel= 'C'
MosaicTile= 'M'
Samples= 'S'
SpatialX= 'X'
SpatialY= 'Y'
SpatialZ= 'Z'
Time= 'T'

All functions operate on np.ndarray in "CZYX" format
"""


class ImageUtils:

    @staticmethod
    def imread(image: typing.Union[np.ndarray, str]) -> np.ndarray:
        """Read image from file or return ndarray as-is. Converts ZCYX to CZYX format."""
        if isinstance(image, str):
            # Read image from disk
            try:
                arr = iio.mvolread(image)
            except Exception:
                arr = iio.mimread(image)
                    
            arr = np.asarray(arr)
            if arr.ndim == 2:
                # YX -> C=1, Z=1, Y, X
                arr = arr[np.newaxis, np.newaxis, :, :]
            elif arr.ndim == 3:
                # Assume ZYX -> add C=1
                arr = arr[np.newaxis, :, :, :]
            elif arr.ndim == 4:
                # Transform ZCYX to CZYX by swapping axes 0 and 1
                arr = np.moveaxis(arr, [0, 1], [1, 0])
            else:
                raise ValueError("Unsupported image dimensions for CZYX assumption")
            return arr
        return image

    @staticmethod
    def imsave(image_ndarray: np.ndarray, path: str):
        image_ndarray = np.asarray(image_ndarray)
        # Convert CZYX to ZCYX for saving
        if image_ndarray.ndim == 4:
            # Transform CZYX to ZCYX by swapping axes 0 and 1
            image_ndarray = np.moveaxis(image_ndarray, [0, 1], [1, 0])
            # Save as multi-page TIFF
            iio.mimwrite(path, image_ndarray)
        elif image_ndarray.ndim == 3:
            iio.volwrite(path, image_ndarray)
        else:
            iio.imwrite(path, image_ndarray)

    @staticmethod
    def get_channel(image_ndarray: np.ndarray, channel_index: int) -> np.ndarray:
        return image_ndarray[channel_index:channel_index+1, :, :, :]

    @staticmethod
    def add_channel(image_ndarray: np.ndarray, channel) -> np.ndarray:
        # Ensure channel has the same number of dimensions as image_ndarray
        
        # If channel is 3D (ZYX) and image is 4D (CZYX), add channel dimension
        if channel.ndim < image_ndarray.ndim:
            channel = np.expand_dims(channel, axis=0)
        
        new_image_ndarray = np.append(image_ndarray, channel, axis=0)
        return new_image_ndarray

    @staticmethod
    def image_to_ndarray(image_ndarray: np.ndarray) -> np.ndarray:
        """Identity function - returns the input ndarray as-is"""
        return image_ndarray

    """
    Normalize all values between 0 to max_value
    """
    @staticmethod
    def normalize(image_ndarray,max_value=255,dtype=np.uint8) -> np.ndarray:
        image_ndarray = image_ndarray.astype(np.float64)
        max_var = np.max(image_ndarray!=np.inf)
        image_ndarray = np.where(image_ndarray==np.inf,max_var,image_ndarray)
        temp_image = image_ndarray-np.min(image_ndarray)
        return ((temp_image)/((np.max(temp_image))*max_value)).astype(dtype)
    
    @staticmethod
    def normalize_std(image_ndarray):
        """ 3D image"""
        mean = np.mean(image_ndarray,dtype=np.float64)
        std = np.std(image_ndarray,dtype=np.float64)
        if (np.isnan(mean) or np.isnan(std) or np.isinf(mean) or np.isinf(std)):
            max_var = np.max(image_ndarray!=np.inf)
            image_ndarray = np.where(image_ndarray==np.inf,max_var,image_ndarray)
            mean = np.mean(image_ndarray,dtype=np.float64)
            std = np.std(image_ndarray,dtype=np.float64)                        
        return (image_ndarray-mean)/std
    
    """
    to_shape changes the image shape according to the shape recieved
    """
    @staticmethod
    def to_shape(image_ndarray, shape, rescale_z=None, min_shape=None,modulo=None)  -> np.ndarray:
        new_shape = shape
        if (min_shape is not None):
            new_shape = np.maximum(shape,min_shape)
        if (modulo is not None):
            new_shape = new_shape + (modulo - np.mod(new_shape,modulo))
        c_, z_, y_, x_ = new_shape
        c, z, y, x = image_ndarray.shape
        y_pad = (y_-y)
        x_pad = (x_-x)
        z_pad = (z_-z)
        c_pad = (c_-c)
        if (rescale_z is not None):
            scaled_a = image_ndarray[:,::rescale_z,:,:]
            z_pad = (z_ - scaled_a.shape[1])
        else:
            scaled_a = image_ndarray
        if (c_pad >= 0):        
            scaled_a = np.pad(scaled_a,((c_pad//2, c_pad//2 + c_pad%2),(0,0),(0,0),(0,0)),mode = 'constant')
        else:
            scaled_a = scaled_a[abs(c_pad//2):scaled_a.shape[0]+(c_pad//2 + c_pad%2),:,:,:]
            
        if (z_pad >= 0):        
            scaled_a = np.pad(scaled_a,((0,0),(z_pad//2, z_pad//2 + z_pad%2),(0,0),(0,0)),mode = 'constant')
        else:
            scaled_a = scaled_a[:,abs(z_pad//2):scaled_a.shape[1]+(z_pad//2 + z_pad%2),:,:]
            
        if (y_pad >= 0):        
            scaled_a = np.pad(scaled_a,((0,0),(0,0),(y_pad//2, y_pad//2 + y_pad%2),(0,0)),mode = 'constant')
        else:
            scaled_a = scaled_a[:,:,abs(y_pad//2):scaled_a.shape[2]+(y_pad//2 + y_pad%2),:]
            
        if (x_pad >= 0):        
            scaled_a = np.pad(scaled_a,((0,0),(0,0),(0,0),(x_pad//2, x_pad//2 + x_pad%2)),mode = 'constant')
        else:
            scaled_a = scaled_a[:,:,:,abs(x_pad//2):scaled_a.shape[3]+(x_pad//2 + x_pad%2)]                        
        return scaled_a
    
    @staticmethod
    def slice_image(image_ndarray:np.ndarray, x_idx:tuple,y_idx:tuple,z_idx:tuple)->np.ndarray:
        n_dim = len(image_ndarray.shape)
        slices = [slice(None)] * n_dim
        slices[n_dim - 3] = slice(x_idx[0], x_idx[1])
        slices[n_dim - 2] = slice(y_idx[0], y_idx[1])
        slices[n_dim - 1] = slice(z_idx[0], z_idx[1])
        slices = tuple(slices)
        sliced_image = image_ndarray[slices]
        return sliced_image
    
    @staticmethod
    def slice_image(image_ndarray: np.ndarray, indexes: list) -> np.ndarray:
        n_dim = len(image_ndarray.shape)
        slices = [slice(None)] * n_dim
        for i in range(len(indexes)):
            slices[i] = slice(indexes[i][0], indexes[i][1])
        slices = tuple(slices)
        sliced_image = image_ndarray[slices]
        return sliced_image
    
    """
    mask_image gets image and mask_template it masks the image according to the template and duplicate it accordingly
    """
    @staticmethod
    def mask_image(image_ndarray,mask_template_ndarray) -> np.ndarray:
        mask_ndarray = mask_template_ndarray
        for i in range(int(image_ndarray.shape[0])-1):
            mask_ndarray = ImageUtils.add_channel(mask_ndarray,mask_template_ndarray)
        return np.where(mask_ndarray==1.0,image_ndarray,np.zeros(image_ndarray.shape))
    
    """
    project 3d image into pixelwise maximium in 2d
    """
    @staticmethod
    def project_to_2d(image_ndarray,axis=1) -> np.ndarray:
        projection_ndarray = np.amax(image_ndarray,axis=axis)
        return projection_ndarray
    
    @staticmethod
    def crop_edges(image_ndarray,mask_template):
        # mask_temp = ImageUtils.get_channel(image_ndarray,5)
        min_max_indecies = [(0,image_ndarray.shape[0])]
        indecies= np.where(mask_template)
        for index in indecies[1:]:
            min_index = min(index)
            max_index = max(index)
            min_max_indecies.append((min_index,max_index))
        cropped_image = ImageUtils.slice_image(image_ndarray,min_max_indecies)
        return cropped_image
