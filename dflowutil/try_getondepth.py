# -*- coding: utf-8 -*-
"""
Created on Tue Mar  3 17:32:08 2020

@author: veenstra
"""


import numpy as np
from netCDF4 import Dataset
import os

from dfm_tools.get_nc import get_netdata, get_ncmodeldata
from dfm_tools.get_nc_helpers import get_varname_mapnc

#code from test_get_nc test d
dir_testinput = os.path.join(r'c:/DATA/werkmap','dfm_tools_testdata')
file_nc = os.path.join(dir_testinput,r'DFM_sigma_curved_bend\DFM_OUTPUT_cb_3d\cb_3d_map.nc')

timestep = 72
layno = 5
calcdist_fromlatlon = None
multipart = None
line_array = np.array([[ 104.15421399, 2042.7077107 ],
                       [2913.47878063, 2102.48057382]])
val_ylim = None
clim_bl = None
#optimize_dist = None
#ugrid = get_netdata(file_nc=file_nc, multipart=multipart)
#intersect_gridnos, intersect_coords = ugrid.polygon_intersect(line_array, optimize_dist=None)


#code from get_xzcoords_onintersection
data_nc = Dataset(file_nc)

varn_mesh2d_s1 = get_varname_mapnc(data_nc,'mesh2d_s1')
data_frommap_wl3 = get_ncmodeldata(file_nc, varname=varn_mesh2d_s1, timestep=timestep, multipart=multipart)
data_frommap_wl3 = data_frommap_wl3[0,:]
#data_frommap_wl3_sel = data_frommap_wl3[0,intersect_gridnos]
varn_mesh2d_flowelem_bl = get_varname_mapnc(data_nc,'mesh2d_flowelem_bl')
data_frommap_bl = get_ncmodeldata(file_nc, varname=varn_mesh2d_flowelem_bl, multipart=multipart)
#data_frommap_bl_sel = data_frommap_bl[intersect_gridnos]

dimn_layer = get_varname_mapnc(data_nc,'nmesh2d_layer')
if dimn_layer is None: #no layers, 2D model
    nlay = 1
else:
    nlay = data_nc.dimensions[dimn_layer].size

varn_layer_z = get_varname_mapnc(data_nc,'mesh2d_layer_z')
if varn_layer_z is None:
    laytyp = 'sigmalayer'
    #zvals_cen = np.linspace(data_frommap_bl_sel,data_frommap_wl3_sel,nlay)
    #zvals_interface = np.linspace(data_frommap_bl_sel,data_frommap_wl3_sel,nlay+1)
    zvals_interface = np.linspace(data_frommap_bl,data_frommap_wl3,nlay+1)
else:
    laytyp = 'zlayer'
    #zvals_cen = get_ncmodeldata(file_nc=file_map, varname='mesh2d_layer_z', lay='all')#, multipart=False)
    #zvals_interface = get_ncmodeldata(file_nc=file_map, varname='mesh2d_interface_z')#, multipart=False)
    zvals_interface = data_nc.variables['mesh2d_interface_z'][:]


depth = -1
z_test_higher = np.argmax((zvals_interface > depth),axis=0)
z_test_lower = np.argmin((zvals_interface < depth),axis=0)
z_test_all = z_test_higher==z_test_lower