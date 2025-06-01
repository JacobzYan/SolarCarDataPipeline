import pandas as pd
import numpy as np
from JZY_Solar_Race_Strategy.Routing.Get_CS_Irr import get_CS_irr
combined_df = pd.read_pickle('DATA/TRIAL_DATASET.pkl')
print(f'combined df: {combined_df}\ncols: {combined_df.columns}')



timezone = 'US/Central'
CS_IRR_time = pd.DatetimeIndex(data=combined_df['startTime'][0], tz = timezone)
CS_irr_list = []
for loc in combined_df['geometry']:
    latitude = loc.x
    longitude = loc.y
    CS_irr = get_CS_irr(latitude, longitude, CS_IRR_time)
    CS_irr_list.append(np.array(CS_irr['ghi']+CS_irr['dni']+CS_irr['dhi']))

combined_df['CS_irr'] = CS_irr_list


for i in combined_df.columns:
    print(f'\ncol: {i}\n{combined_df[i].head(5)}')

print(f'CS_irr 1st: {combined_df['CS_irr'][0]}\nshape: {combined_df['CS_irr'][0].shape}')




