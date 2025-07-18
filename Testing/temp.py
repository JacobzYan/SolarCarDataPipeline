from pyproj import Geod

geod = Geod(ellps='WGS84')

a,b,c=geod.inv(-97.748919, 30.30768, -97.74881, 30.307497)

print(f'a: {a}\nb: {b}\nc: {c}')
