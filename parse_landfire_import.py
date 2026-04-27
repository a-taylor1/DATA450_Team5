
'''
This is a script to rename and extract the necessary items from a new landfire imports.
It renames the files that we need, and places the others in an extras folder.
'''


import os

lf_name_map = {
    'FDist' : 'disturbance',
      'FVH' : 'fuelheight',
      'FVC' : 'fuelcover',
      'FVT' : 'fueltype'
}

lf_folders = os.listdir('./landfire_data')
for dowload in lf_folders:
    # Skip hidden directories and zip files
    if (dowload[0] == '.') or ('.zip' in dowload): continue
    layer_folders = os.listdir(f'./landfire_data/{dowload}')
    for layer in layer_folders:
        lf_product_name = layer.split('_')[1]
        file_list = os.listdir(f'./landfire_data/{dowload}/{layer}')
        for file_name in file_list:
            split_name = file_name.split('.')
            # Ignore compound files and metadata files
            if ( (len(split_name) > 2) or ('metadata' in file_name) or ('GeoJSON' in file_name) or ('tfw' in file_name) or ('txt' in file_name) ):
                try:
                    os.mkdir(f'./landfire_data/{dowload}/{layer}/extras/')
                except Exception as e:
                    print(f'passing...')
                os.rename(f'./landfire_data/{dowload}/{layer}/{file_name}', f'./landfire_data/{dowload}/{layer}/extras/{file_name}')
                continue
            #os.rename(f'./landfire_data/{dowload}/{layer}/{file_name}.dbf', f'./landfire_data/{dowload}/{layer}/{new_name}_codes.dbf')
            #os.rename(f'./landfire_data/{dowload}/{layer}/{file_name}.tif', f'./landfire_data/{dowload}/{layer}/{new_name}_pixels.dbf')
            if 'dbf' in file_name:
                dbf_path = f'./landfire_data/{dowload}/{layer}/{file_name}'
                new_dbf_name = f'{lf_name_map[lf_product_name]}_codes.dbf'
                print(f'> FOUND DBF: {dbf_path}')
                print(f'   > RENAMING...', end = '')
                os.rename(dbf_path , f'./landfire_data/{dowload}/{layer}/{new_dbf_name}')
                print(f'DONE.')
            if 'tif' in file_name:
                tif_path = f'./landfire_data/{dowload}/{layer}/{file_name}'
                new_tif_name = f'{lf_name_map[lf_product_name]}_pixels.tif'
                print(f'> FOUND TIF: {tif_path}')
                print(f'   > RENAMING...', end = '')
                os.rename(tif_path , f'./landfire_data/{dowload}/{layer}/{new_tif_name}')
                print(f'DONE.')
        if 'extras' in os.listdir(f'./landfire_data/{dowload}/{layer}'):
            try:
                os.mkdir(f'./landfire_data/extras/')
            except Exception as e:
                print(f'passing...')
            os.rename(f'./landfire_data/{dowload}/{layer}/extras', f'./landfire_data/extras/{layer}')
            print(f'\n{layer} has extras!\n')
        
        print(f'\tFILES FOUND AFTER RENAME: {os.listdir(f'./landfire_data/{dowload}/{layer}')}\n')
    print(f'\nFILES FOUND AFTER RENAME: {os.listdir(f'./landfire_data/{dowload}')}')