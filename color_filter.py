#!/usr/bin/python
# -*- coding: utf-8 -*-

import array
from gimpfu import *
from math import sqrt, cos, sin, radians

# changes Hue-Saturation-Value of pixels from the source image 
def filter_adjust_color_hsv(rgb, 
                            filter_level_hue,
                            filter_level_sat,
                            filter_level_val):

    # RGB values are transformed to YIQ color model
    # user selected tranformations are applied
    # YIQ values are transformed back to RGB representation and saved
    # for further explonation behind this math see technical documentation  

    vsu = filter_level_val * filter_level_sat * cos(filter_level_hue * math.pi / 180)
    vsw = filter_level_val * filter_level_sat * sin(filter_level_hue * math.pi / 180)
    
    red = (
            (0.299 * filter_level_val + 0.701 * vsu + 0.168 * vsw) * rgb[0] +
            (0.587 * filter_level_val - 0.587 * vsu + 0.330 * vsw) * rgb[1] +
            (0.114 * filter_level_val - 0.114 * vsu - 0.497 * vsw) * rgb[2]
        ) 

    green = (
            (0.299 * filter_level_val - 0.299 * vsu - 0.328 * vsw) * rgb[0] + 
            (0.587 * filter_level_val + 0.413 * vsu + 0.035 * vsw) * rgb[1] +
            (0.114 * filter_level_val - 0.114 * vsu + 0.292 * vsw) * rgb[2]
        )

    blue = (
            (0.299 * filter_level_val - 0.300 * vsu + 1.250 * vsw) * rgb[0] +
            (0.587 * filter_level_val - 0.588 * vsu - 1.050 * vsw) * rgb[1] +
            (0.114 * filter_level_val + 0.886 * vsu - 0.203 * vsw) * rgb[2]
        )

    # save new color values in RGB color model
    rgb[0] = int(red)
    rgb[1] = int(green)
    rgb[2] = int(blue)


# Add value to selected color channel
def filter_adjust_color_rgb(rgb, filter_value_r, filter_value_g, filter_value_b):
    # adjust RED channel value
    rgb[0] = max(0, min(255, int(rgb[0] + filter_value_r)))
                        
    # adjust GREEN channel value
    rgb[1] = max(0, min(255, int(rgb[1] + filter_value_g)))

    # adjust BLUE channel value  
    rgb[2] = max(0, min(255, int(rgb[2] + filter_value_b)))

# Grayscale filter 
def filter_grayscale(rgb):

    # calculate grayscale values (RED * 0.2989 + GREEN * 0.597 + BLUE * 0.114) / 255
    sum = (rgb[0] * 0.2989 + rgb[1] * 0.587 + rgb[2] * 0.114) / 255

    # set calculated values 
    for i in range(0, 3):
        rgb[i] = sum

# Invert colors filter
def filter_invert_colors(rgb):
    for i in range(0, 3):
        rgb[i] = 255 - rgb[i]

# Sephia color filter
def filter_sephia(rgb):
    # calculate sephia red channel values (RED * 0.393 + GREEN * 0.769 + BLUE * 0.189)
    sep_r = int(min(255, rgb[0] * 0.393 + rgb[1] * 0.769 + rgb[2] * 0.189))
    # calculate sephia blue channel values (RED * 0.349 + GREEN * 0.686 + BLUE * 0.168)
    sep_g = int(min(255, rgb[0] * 0.349 + rgb[1] * 0.686 + rgb[2] * 0.168))
    # calculate sephia gree channel values (RED * 0.272 + GREEN * 0.534 + BLUE * 0.131)
    sep_b = int(min(255, rgb[0] * 0.272 + rgb[1] * 0.534 + rgb[2] * 0.131))

    # set calculated values
    rgb[0] = sep_r
    rgb[1] = sep_g
    rgb[2] = sep_b

# picks the correct name for the filter layer
def name_filter_layer(filter, filter_predefined):
    
    # RGB
    if filter == "rgb":
        name = "filter_rgb"

    # HSV
    elif filter == "hsv":
        name = "filter_hsv"

    # Predefined filters
    elif filter == "ad":
        # Grayscale
        if filter_predefined == "gs":
            name = "filter_grayscale"
        # Invert colors
        elif filter_predefined == "inv":
            name = "filter_inverted"
        # Sephia
        elif filter_predefined == "sep":
            name = "filter_sepia"

    return name

def custom_color_filter_main(image,
                             drawable,
                             filter, 
                             filter_level_r,
                             filter_level_g,
                             filter_level_b,
                             filter_level_hue,
                             filter_level_sat,
                             filter_level_val,
                             filter_predefined,
                             flatten = False):
    
    #start Undo group
    pdb.gimp_image_undo_group_start(image)

    # loads number of bytes per pixel
    # its value depends on whether the image is Grayscale* or RGB*
    bpp = drawable.bpp
    # load boundries 
    (bx1, by1, bx2, by2) = drawable.mask_bounds
    # calculate width and height
    bw = bx2 - bx1
    bh = by2 - by1
    # input layer offset
    (ox, oy) = drawable.offsets

    # gets image data as a string containing byte array with source image data
    src_rgn = drawable.get_pixel_rgn(bx1, by1, bw, bh, False, False)
    # unpack image pixel data into arrays 
    src_pixels = array.array("B", src_rgn[bx1:bx2, by1:by2])

    # changes the name of the new layer to proper one depending on the filter chosen
    name = name_filter_layer(filter, filter_predefined)
    # creates new layer with proper name
    layer = gimp.Layer(image, name, bw, bh, RGBA_IMAGE, 100, NORMAL_MODE)
    # adjust new layer position to fit the selected area
    layer.set_offsets(bx1 + ox, by1 + oy)
    # output image data
    dst_rgn = layer.get_pixel_rgn(0, 0, bw, bh, True, True)
    # all output pixels to arrays
    dst_pixels = array.array("B", dst_rgn[0:bw, 0:bh])

    # output layer is always RGBA for easier work later 
    dst_bpp = 4

    # add new layer to the project
    image.add_layer(layer, 0)

    # value adjustmets for HSV filter needs values (-1, 1)
    # from user input we get values (-100, 100)
    filter_level_val = 1 + (filter_level_val / 100.0)
    filter_level_sat = 1 + (filter_level_sat / 100.0)

    # start progress
    gimp.progress_init("Applying filter..")

    for y in range (0, bh):
        for x in range(0, bw):
            pos = (y * bw + x) * bpp

            data = src_pixels[pos:(pos + bpp)]
            # creates a simulation of RGB struct which contains each RGB channel
            # if alfa is not set, its automatically set to 255(100%)
            rgb = gimpcolor.RGB(data[0], data[1], data[2], data[3] if bpp == 4 else 255)

            # RGB color image filter 
            if filter == "rgb":
                filter_adjust_color_rgb(rgb, filter_level_r, filter_level_g, filter_level_b)

            # HSV color image filter
            if filter == "hsv":
                filter_adjust_color_hsv(rgb, filter_level_hue, filter_level_sat, filter_level_val)

            # Additional filters
            if filter == "ad":
                # Grayscale image filter
                if filter_predefined == "gs":  
                    filter_grayscale(rgb)   
                # Invert color image filter    
                elif filter_predefined == "inv":
                    filter_invert_colors(rgb)
                # Sephia  image filter
                elif filter_predefined == "sep":
                    filter_sephia(rgb)
                
            # converts our custom RGB struct into byte array
            data[0:dst_bpp] = array.array("B", rgb[0:dst_bpp])
            dst_pos = (x + bw * y) * dst_bpp
            # write filtered pixel data into the output byte array
            dst_pixels[dst_pos:(dst_pos + dst_bpp)] = data

        # update progress bar
        gimp.progress_update(float(y + 1) / bh)

    # pack output byte array into the string and save it into the output layer 
    dst_rgn[0:bw, 0:bh] = dst_pixels.tostring()
    # apply changes on the filter layer
    layer.flush()
    # apply selection mask
    layer.merge_shadow(True)
    # refresh filter layer
    layer.update(0, 0, bw, bh)

    # merges layers into one if true
    if flatten:
        pdb.gimp_image_flatten(image)

    # refresh GIMP application
    gimp.displays_flush()

    # end Undo group
    pdb.gimp_image_undo_group_end(image)

# registration form for the 
register(
    "custom-color-filter",
    "Adjust colors of the image.",
    "Cusom color filter",
    "Adam Polivka",
    "Adam Polivka",
    "2020",
    "<Image>/_Custom/Custom Color Filter",
    "RGB*, GRAY*",
    [   
        # parameters inherited from gimplugin.plugin
            # run_mode   
            # image
            # drawable 
        # plugin specific parameters - UI inputs
        # select between HSV and RGB color transformation or choose predefined filters
        (PF_RADIO, "filter", "Filter:", "rgb",
            (
                ("RGB", "rgb"),
                ("HSV", "hsv"),
                ("Predefined filters", "ad"),
            )    
        ),
        # filter level sliders
        (PF_SLIDER, "filter_level_r", "add Red:", 0, (-255, 255, 10)),
        (PF_SLIDER, "filter_level_g", "add Green:", 0, (-255, 255, 10)),
        (PF_SLIDER, "filter_level_b", "add Blue:", 0, (-255, 255, 10)),
        (PF_SLIDER, "filter_level_hue", "add Hue:", 0, (-180, 180, 10)),
        (PF_SLIDER, "filter_level_sat", "add Saturation:", 0, (-100, 100, 10)),
        (PF_SLIDER, "filter_level_val", "add Value:", 0, (-100, 100, 10)),
        # additional filters 
        (PF_RADIO, "filter_predefined", "Predefined filters:", "gs",
            (
                ("Grayscale", "gs"),
                ("Invert colors", "inv"),
                ("Sephia", "sep"),
            )    
        ),
        # merge layer into one option
        (PF_BOOL, "flatten", "Merge layers: ", False),
    ],
    [],
    custom_color_filter_main)
main()