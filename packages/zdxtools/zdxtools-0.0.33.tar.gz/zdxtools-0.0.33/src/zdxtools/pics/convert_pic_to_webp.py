def convert_pic_to_webp(picpath,DELETE = False,quality = 65):
    import os
    from PIL import Image
    picpath_webp = f'''{picpath.split('.')[0]}.webp'''
    img = Image.open(picpath)
    img.save(picpath_webp, 'WEBP', quality=quality)
    if DELETE:
        os.remove(picpath)

    return picpath_webp


