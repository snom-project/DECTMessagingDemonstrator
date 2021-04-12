import os
import glob
import pandas as pd
os.chdir(".")

extension = 'csv'
all_filenames = [i for i in glob.glob('*.{}'.format(extension))]

print(f'merge filenames: {all_filenames}')
#combine all files in the list
combined_csv = pd.concat([pd.read_csv(f) for f in all_filenames ], sort=False)

# re-arrange all rooms columns to the left
cols = combined_csv.columns.tolist()
cols = cols[-len(all_filenames)+1:] + cols[:-len(all_filenames)+1]
#print('result:', cols)
combined_csv = combined_csv[cols]
#export to csv
print(combined_csv)
combined_csv.to_csv( "combined_csv.csv", index=False, encoding='utf-8', na_rep='0', float_format='%.f')
