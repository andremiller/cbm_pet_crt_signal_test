import argparse
import os
from PIL import Image, ImageOps

ROWS = 260    # Number of rows
HOR_TIME = 64 # Time of horizontal line in us
HOR_RES = 0.125   # Horizontal resolution in us
COLUMNS = int(HOR_TIME/HOR_RES)  # Number of columns

NAME="PET9_"+str(HOR_RES)+"us"

grid_array_vert  = [0] * COLUMNS * ROWS
grid_array_horiz = [0] * COLUMNS * ROWS


def main(img_file_names, invert_image=False):
    
    images=[]
    for input_image_name in img_file_names:
        print("Processing input image: %s" % input_image_name)
        image = Image.open(input_image_name).convert('RGB').resize((int(40/HOR_RES),200))
        if invert_image:
            image=ImageOps.invert(image)
        image = image.load()
        images.append(image)
    basefilename = os.path.splitext(img_file_names[0])[0]
    
    # Vertical
    for i in range(20): # Vertical drive is 20 lines long at start of frame
        for j in range(COLUMNS):
            grid_array_vert[i * COLUMNS + j] = 1

    # Vert starts roughly 5 usec before start of frame
    for i in range(int(5/HOR_RES)):
        grid_array_vert[COLUMNS * ROWS - (i+1)] = 1

    # Horizontal
    for i in range(ROWS):
        for j in range(int(24/HOR_RES)): # horizontal is 24 us long (2 * 12)
            grid_array_horiz[i*COLUMNS+j] = 1

    # Video
    grid_arrays_vid = []
    for image in images:
        grid_array_vid = [0] * COLUMNS* ROWS
        for x in range(int(40/HOR_RES)): # Video is 40 us long
            for y in range(200):
                p = image[x,y]
                pixel_average = (p[0] + p[1] + p[2]) / 3
                if pixel_average > 127:
                    pixel_value = 1
                else:
                    pixel_value = 0
                grid_array_vid[(y+40)*COLUMNS+(x+int(18/HOR_RES))] = pixel_value
        grid_arrays_vid.append(grid_array_vid)

    # Create an image as output
    for i, input_image_name in enumerate(img_file_names):
        test_image = Image.new('RGB', (COLUMNS, ROWS)) # Create a new black image
        for x in range(COLUMNS):
            for y in range(ROWS):
                test_image.putpixel((x, y), (grid_array_horiz[y*COLUMNS+x]*255, grid_arrays_vid[i][y*COLUMNS+x]*255, grid_array_vert[y*COLUMNS+x]*255))
        img_out_filename = NAME+'_'+os.path.splitext(input_image_name)[0]+'.png'
        print("Writing output image: %s" % img_out_filename)
        test_image.resize((512,512),Image.Resampling.NEAREST).save(img_out_filename, "PNG")

    output = []
    for i in range(ROWS*COLUMNS):
        v = 0b00000000
        # Video starts at bit 0 for first image
        for bit, grid_array_vid in enumerate(grid_arrays_vid):
            v = v | (( 1 - int(grid_array_vid[i]))   << bit)  # Video
        v = v | ((     int(grid_array_horiz[i])) << 5)  # Horiz
        
        v = v | (( 1 - int(grid_array_vert[i]))  << 6)  # Vert
        output.append(v)

    # Add reset on last byte
    v = output[ROWS*COLUMNS-1]
    v = v | (1 << 7)
    output[ROWS*COLUMNS-1]=v

    rom_out_filename = NAME+'_'+basefilename+'.bin'
    print("Writing output ROM: %s" % rom_out_filename)
    f = open(rom_out_filename, 'wb')
    f.write(bytes(output))
    f.close()


if __name__ == "__main__":
    print("== Begin %s" % NAME)
    parser = argparse.ArgumentParser(description='%s Convert image to ROM for test image.' % NAME)
    parser.add_argument('--invert', action=argparse.BooleanOptionalAction, help='Invert image colours')
    parser.add_argument('img_file_names', type=str, nargs='+', help='Path and name of image files.')
    args = parser.parse_args()   
    main(args.img_file_names, args.invert)
    print("== End %s" % NAME)