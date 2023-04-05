"""
Created on Tue Apr  4 16:12:56 2023

@author: groenenb, sclaan
edited by: veenstra

This is a proof of concept that will be properly coded in the near future and probably end up under hydromt-delft3dfm
"""

import os
import xarray as xr
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
import contextily as ctx
import dfm_tools as dfmt
import hydrolib.core.dflowfm as hcdfm
import datetime as dt
import glob
import numpy as np

#bathy
from matplotlib.path import Path as pth
import warnings
from dfm_tools.hydrolib_helpers import pointlike_to_DataFrame
from dfm_tools.bathymetry import write_bathy_toasc

#gridgen
import getpass
from meshkernel import Mesh2dFactory, MeshKernel
import meshkernel
import xugrid as xu


#MODELBUILDER: p:\11209231-003-bes-modellering\hydrodynamica\hackathon\preprocessing\scripts\dfm_ModelBuilder_functions.py

def download_meteodata_oceandata(
        longitude_min = 2, longitude_max = 4, latitude_min = 50, latitude_max = 52, # domain
        model = 'CMEMS', #CMEMS ERA5
        overwrite = True, # always set to True when changing the domain
        date_min = '2010-01-01', #dates as understood by pandas.period_range(). ERA5 has freq='M' (month) and CMEMS has freq='D' (day)
        date_max = '2010-01-02',
        varlist = [], 
        dir_output = './meteo_ocean_data',
        make_figs = True
        ):
     
    #download ERA5/CMEMS/HYCOM data for given domain, time extent and variables
    #TODO: add CMCC, GFDL
    #TODO: add climatedata cmip6
    #TODO: add GFS and other NOAA models (https://www.ncei.noaa.gov/products/weather-climate-models/global-forecast > NCEI > TDS)
    #TODO: add click?

    #ERA5
    if model == 'ERA5':
        if isinstance(varlist[0], list):
            varlists = varlist
        else:
            varlists = [varlist]
        
        for varlist in varlists:
            for varkey in varlist:
                if not os.path.isdir(dir_output):
                    os.mkdir(dir_output)
                
                dfmt.download_ERA5(varkey, 
                                   longitude_min=longitude_min-1/4, longitude_max=longitude_max+1/4, latitude_min=latitude_min-1/4, latitude_max=latitude_max+1/4, # download 1 grid cell row/column extra
                                   date_min=date_min, date_max=date_max,
                                   dir_output=dir_output, overwrite=overwrite)
            
                #open mfdataset to check folder contents
                if make_figs:
                    ds = xr.open_mfdataset(os.path.join(dir_output,f'era5_{varkey}_*.nc'))
                    ds.close()
                    fig,ax = plt.subplots()
                    ds[varkey].isel(time=0).plot(ax=ax)
                    ctx.add_basemap(ax=ax,crs="EPSG:4326",attribution=False)
                    #TODO    file_out = os.path.join(dir_output, f'era5_{varkey}_{time_start_str}to{time_stop_str}')
                    #TODO    name_output = f'era5_{varkey}_{dt.datetime.strftime(ds[varkey].time[0],"%Y-%m")}.nc'
                    #TODO    fig.savefig(file_out)
    
    
    #CMEMS
    if model == 'CMEMS':
        date_min_cmems = pd.Timestamp(date_min)-pd.Timedelta(days=1) #CMEMS has daily noon values (not midnight), so subtract one day from date_min to cover desired time extent
        for varkey in varlist:
            Path(dir_output).mkdir(parents=True, exist_ok=True)
            #TODO: update CMEMS urls after 15 april, since some are being replaced
            if varkey in ['bottomT','mlotst','siconc','sithick','so','thetao','uo','usi','vo','vsi','zos']: #for physchem
                #reanalisys: https://data.marine.copernicus.eu/product/GLOBAL_MULTIYEAR_PHY_001_030/description
                #dataset_url = 'https://my.cmems-du.eu/thredds/dodsC/cmems_mod_glo_phy_my_0.083_P1D-m'
                #forecast: https://data.marine.copernicus.eu/product/GLOBAL_ANALYSISFORECAST_PHY_001_024/description
                dataset_url = 'https://nrt.cmems-du.eu/thredds/dodsC/global-analysis-forecast-phy-001-024' #old location for forecasts (available up to 15 april)
                #dataset_url = 'https://nrt.cmems-du.eu/thredds/dodsC/cmems_mod_glo_phy_anfc_0.083deg_PT1H-m.html' #hourly for cur/tem/sal (surface only)
                #dataset_url = 'https://nrt.cmems-du.eu/thredds/dodsC/cmems_mod_glo_phy-cur_anfc_0.083deg_P1D-m.html' #currents
                #dataset_url = 'https://nrt.cmems-du.eu/thredds/dodsC/cmems_mod_glo_phy-thetao_anfc_0.083deg_P1D-m.html' #temperature
                #dataset_url = 'https://nrt.cmems-du.eu/thredds/dodsC/cmems_mod_glo_phy-so_anfc_0.083deg_P1D-m.html' #salinity
            else: # for bio #https://data.marine.copernicus.eu/product/GLOBAL_ANALYSIS_FORECAST_BIO_001_028/description
                dataset_url = 'https://my.cmems-du.eu/thredds/dodsC/cmems_mod_glo_bgc_my_0.25_P1D-m' #contains ['chl','no3','nppv','o2','po4','si']
                #dataset_url = 'https://nrt.cmems-du.eu/thredds/dodsC/global-analysis-forecast-bio-001-028-daily' #contains ['chl','fe','no3','nppv','o2','ph','phyc','po4','si','spco2']
            file_prefix = 'cmems_'
            
            dfmt.download_OPeNDAP(dataset_url=dataset_url,
                                  credentials=None, #credentials=['username','password'], or create "%USERPROFILE%/CMEMS_credentials.txt" with username on line 1 and password on line 2. Register at: https://resources.marine.copernicus.eu/registration-form'
                                  varkey=varkey,
                                  longitude_min=longitude_min-1/12, longitude_max=longitude_max+1/12, latitude_min=latitude_min-1/12, latitude_max=latitude_max+1/12, # download 1 grid cell row/column extra
                                  date_min=date_min_cmems, date_max=date_max,
                                  dir_output=dir_output, file_prefix=file_prefix, overwrite=overwrite)
            
            #open mfdataset to check folder contents and plot first field of each variable
            if make_figs:
                ds = xr.open_mfdataset(os.path.join(dir_output,f'{file_prefix}{varkey}_*.nc'))
                fig,ax = plt.subplots()
                if 'depth' in ds[varkey].dims:
                    ds[varkey].isel(time=0,depth=0).plot(ax=ax)
                else:
                    ds[varkey].isel(time=0).plot(ax=ax)
                ds.close()
                ctx.add_basemap(ax=ax,crs="EPSG:4326",attribution=False)
        
    
    #HYCOM
    if model == 'HYCOM':
        for varkey in varlist:
            Path(dir_output).mkdir(parents=True, exist_ok=True)
            
            period_range_years = pd.period_range(date_min,date_max,freq='Y')
            dataset_url = [f'https://tds.hycom.org/thredds/dodsC/GLBu0.08/expt_19.1/{year}' for year in period_range_years] #list is possible with hycom, since it uses xr.open_mfdataset()
            file_prefix = 'hycom_'
            
            dfmt.download_OPeNDAP(dataset_url=dataset_url,
                                  varkey=varkey,
                                  longitude_min=longitude_min, longitude_max=longitude_max, latitude_min=latitude_min, latitude_max=latitude_max,
                                  date_min=date_min, date_max=date_max,
                                  dir_output=dir_output, file_prefix=file_prefix, overwrite=overwrite)
            
            #open mfdataset to check folder contents and plot first field of each variable
            if make_figs:
                ds = xr.open_mfdataset(os.path.join(dir_output,f'{file_prefix}{varkey}_*.nc'))
                fig,ax = plt.subplots()
                if 'depth' in ds[varkey].dims:
                    ds[varkey].isel(time=0,depth=0).plot(ax=ax)
                else:
                    ds[varkey].isel(time=0).plot(ax=ax)
                ds.close()
                ctx.add_basemap(ax=ax,crs="EPSG:4326",attribution=False)
    

    
    
def preprocess_interpolate_nc_to_bc(
        refdate_str = 'minutes since 2000-01-01 00:00:00 +00:00', # if None, xarray uses ds.time.encoding['units'] as refdate_str
        dir_output = './interpolate_nc_to_bc',
        #quantities should be in conversion_dict.keys(). waterlevelbnd is steric/zos, tide is tidal components from FES/EOT
        list_quantities = ['waterlevelbnd','salinitybnd','temperaturebnd','uxuy','tide'], # e.g. ['waterlevelbnd','salinitybnd','temperaturebnd','uxuy','tide','tracerbndNO3','tracerbndOpal','tracerbndDON']
        model = 'CMEMS', #CMEMS GFDL CMCC HYCOM
        tstart = '2012-01-01 12:00',
        tstop = '2012-01-02 12:00',
        list_plifiles = [r'p:\11208054-004-dcsm-fm\models\model_input\bnd_cond\pli\DCSM-FM_OB_all_20181108_nocomments.pli'], #TODO: reading this file without '_nocomments' results in empty Polyfile, should raise an error. https://github.com/Deltares/HYDROLIB-core/issues/320
        dir_sourcefiles_hydro = r'p:\1204257-dcsmzuno\data\CMEMS\nc\DCSM_allAvailableTimes', #CMEMS hydro: bottomT, so, thetao, uo, vo, zos (2012-01-06 12:00:00 to 2013-01-03 12:00:00) (daily values at noon, not at midnight)
        make_figs = True): 
    
    list_plifiles = [Path(x) for x in list_plifiles]
    
    #TODO: add coordinate conversion of pli-coordinates? (for nesting RD models in oceanmodels)
    #TODO: additional models/sources for download/interpolate (evt xESMF for CMCC, climate forcing cmip6 procedure (=calendarconversion) and others)
    
    #The {ncvarname} wildcard in dir_pattern_hydro/dir_patern_waq is used to replace it with conversion_dict[quantity]['ncvarname'] by using str(dir_pattern).format(ncvarname)
    if model=='CMEMS': #2012-01-06 12:00:00 to 2013-01-03 12:00:00
        conversion_dict = dfmt.get_conversion_dict()
        dir_pattern_hydro = Path(dir_sourcefiles_hydro,'cmems_{ncvarname}_*.nc') # later remove 2012 from string, but this is faster for testing #TODO: it is quite slow, maybe speed up possible?
        dir_sourcefiles_waq = r'p:\11206304-futuremares\python_scripts\ocean_boundaryCMEMS\data_monthly' #CMEMS waq: no3, o2, phyc, so4, si (2011-12-16 12:00:00 to 2019-01-16 12:00:00)
        dir_pattern_waq = Path(dir_sourcefiles_waq,'cmems_mod_glo_bgc_my_0.25_P1M-m_{ncvarname}_*.nc') 
        #to reproduce old CMEMS data (icw reverse_depth=True) (from p:\1204257-dcsmzuno\data\CMEMS\bnd\NorthSeaAndBaltic_1993-2019_20210510)
        #tstart = dt.datetime(1993,1,1,12,0)
        #tstop = tstart + dt.timedelta(days=5)
        #dir_pattern_hydro = Path(dir_sourcefiles_hydro,'{ncvarname}_1993*.nc')
        #TODO tstart = pd.Timestamp(tstart)-pd.Timedelta(days=1) #similar as download: CMEMS has daily noon values (not midnight), so subtract one day from date_min to cover desired time extent
    elif model=='GFDL':
        conversion_dict = dfmt.get_conversion_dict()
        tstart = '2012-01-16 12:00'
        tstop = '2012-04-01 12:00'
        list_plifiles = [Path(r'p:\11208054-004-dcsm-fm\models\model_input\bnd_cond\pli\DCSM-FM_OB_all_20181108_nocomments.pli')] #TODO: reading this file without '_nocomments' results in empty Polyfile, should raise an error. https://github.com/Deltares/HYDROLIB-core/issues/320
        dir_sourcefiles_hydro = None
        dir_pattern_hydro = None
        dir_sourcefiles_waq = r'p:\11206304-futuremares\data\CMIP6_BC\GFDL-ESM4' #GFDL waq: no3 (1850-01-16 12:00:00 to 2014-12-16 12:00:00)
        dir_pattern_waq = Path(dir_sourcefiles_waq,'{ncvarname}_esm-hist.nc')
    elif model=='CMCC': #TODO: check method, now finding nearest points (so always has values)
        #TODO: time_bnds/lev_bnds are available, take into account in bc file?
        conversion_dict = dfmt.get_conversion_dict(ncvarname_updates={'salinitybnd':'sos', 'temperaturebnd':'tos'})
        conversion_dict['tracerbndNO3'] = {'ncvarname':'no3', 'unit':'g/m3', 'conversion':14.0} #other vars also have different conversion than cmems
        tstart = '2015-06-16 12:00'
        tstop = '2015-12-01 12:00'
        list_plifiles = [Path(r'p:\11208054-004-dcsm-fm\models\model_input\bnd_cond\pli\DCSM-FM_OB_all_20181108_nocomments.pli')] #TODO: reading this file without '_nocomments' results in empty Polyfile, should raise an error. https://github.com/Deltares/HYDROLIB-core/issues/320
        dir_sourcefiles_hydro = r'p:\11206304-futuremares\data\CMIP6_BC\CMCC-ESM2'
        dir_pattern_hydro = Path(dir_sourcefiles_hydro,'{ncvarname}_Omon_CMCC-ESM2_ssp126_r1i1p1f1_gn_*.nc')
        dir_sourcefiles_waq = dir_sourcefiles_hydro #CMCC waq: (2015-01-16 12:00:00 to 2100-12-16 12:00:00)
        dir_pattern_waq = dir_pattern_hydro
    elif model=='HYCOM':
        conversion_dict = dfmt.get_conversion_dict(ncvarname_updates={'salinitybnd':'salinity', 'temperaturebnd':'water_temp'})
        tstart = '2016-04-20'
        tstop = '2016-05-03'
        list_plifiles = [Path(r'c:\DATA\dfm_tools_testdata\GLBu0.08_expt_91.2\bcline.pli')] #HYCOM not available in DCSM area, so use other pli-file
        dir_sourcefiles_hydro = 'c:\\DATA\\dfm_tools_testdata\\GLBu0.08_expt_91.2' #HYCOM hydro: salinity/so, water_temp/thetao (2016-04-19 00:00:00 to 2016-05-06 00:00:00)
        dir_pattern_hydro = Path(dir_sourcefiles_hydro,'HYCOM_ST_GoO_*.nc')
        dir_sourcefiles_waq = None
        dir_pattern_waq = None
    else:
        raise Exception(f'invalid model: {model}')
    
    # start of interpolation process
    dtstart = dt.datetime.now()
    ext_bnd = hcdfm.ExtModel()
    if not os.path.isdir(dir_output):
        os.mkdir(dir_output)
    
    for file_pli in list_plifiles:
        file_bc_basename = file_pli.name.replace('.pli','')
        for quantity in list_quantities:
            print(f'processing quantity: {quantity}')
            if quantity=='tide': 
                tidemodel = 'FES2014' #FES2014, FES2012, EOT20, GTSM4.1preliminary
                if tidemodel == 'FES2014': #for comparing to older FES bc-files #TODO: choose flexible/generic component notation
                    component_list = ['2n2','mf','p1','m2','mks2','mu2','q1','t2','j1','m3','mm','n2','r2','k1','m4','mn4','s1','k2','m6','ms4','nu2','s2','l2','m8','msf','o1','s4']
                else:
                    component_list = None #None results in all tidemodel components
                ForcingModel_object = dfmt.interpolate_tide_to_bc(tidemodel=tidemodel, file_pli=file_pli, component_list=component_list, nPoints=None)
                for forcingobject in ForcingModel_object.forcing: #add A0 component
                    forcingobject.datablock.append(['A0',0.0,0.0])
            else:
                if quantity in ['waterlevelbnd','salinitybnd','temperaturebnd','uxuy']: #hydro
                    if dir_sourcefiles_hydro is None:
                        continue
                    if (model=='HYCOM') & (quantity not in ['salinitybnd','temperaturebnd']): #only contains quantities salinity and water_temp, so crashes on others
                        continue
                    dir_pattern = dir_pattern_hydro
                else: #waq
                    if dir_pattern_waq is None:
                        continue
                    dir_pattern = dir_pattern_waq
                
                #open regulargridDataset and do some basic stuff (time selection, renaming depth/lat/lon/varname, converting units, etc)
                data_xr_vars = dfmt.open_dataset_extra(dir_pattern=dir_pattern, quantity=quantity, #TODO: maybe replace renaming part with package CMCC/Lisa?
                                                       tstart=tstart, tstop=tstop,
                                                       conversion_dict=conversion_dict,
                                                       refdate_str=refdate_str)
                #interpolate regulargridDataset to plipointsDataset
                data_interp = dfmt.interp_regularnc_to_plipoints(data_xr_reg=data_xr_vars, file_pli=file_pli, #TODO: difference in .interp() with float vs da arguments: https://github.com/Deltares/dfm_tools/issues/287
                                                                 nPoints=None) #argument for testing
                
                #convert plipointsDataset to hydrolib ForcingModel
                ForcingModel_object = dfmt.plipointsDataset_to_ForcingModel(plipointsDataset=data_interp)
                        
            file_bc_basename = file_pli.name.replace('.pli','')
            if quantity=='tide':
                file_bc_out = Path(dir_output,f'{quantity}_{file_bc_basename}_{tidemodel}.bc')
            else:
                file_bc_out = Path(dir_output,f'{quantity}_{file_bc_basename}_{model}.bc')
            
            print(f'writing ForcingModel to bc file with hydrolib ({file_bc_out.name})')
            bc_type = 'bc' #TODO: add netcdf bc support. https://github.com/Deltares/HYDROLIB-core/issues/318
            if bc_type=='bc':
                #ForcingModel_object.serializer_config.float_format = '.3f' #TODO SOLVED: improve formatting of bc file: https://github.com/Deltares/HYDROLIB-core/issues/308
                #ForcingModel_object.serializer_config.float_format_datablock = '.5f' #maybe move this to interp_regularnc_to_plipoints/interpolate_tide_to_bc?
                ForcingModel_object.save(filepath=file_bc_out)
            
            #TODO: support for relative paths?
            #generate boundary object for the ext file (quantity, pli-filename, bc-filename)
            boundary_object = hcdfm.Boundary(quantity=quantity.replace('tide','waterlevelbnd'), #the FM quantity for tide is also waterlevelbnd
                                             locationfile=file_pli,
                                             forcingfile=ForcingModel_object)
            ext_bnd.boundary.append(boundary_object)
    
            if make_figs and quantity!='tide': #TODO: data_xr_vars/data_interp does not exist for tide yet
                #plotting dataset and polyline (is wrong for CMCC)
                varname0 = list(data_xr_vars.data_vars)[0] 
                fig,ax = plt.subplots()
                if 'depth' in data_xr_vars[varname0].dims:
                    data_xr_vars[varname0].isel(time=0,depth=0).plot(ax=ax)
                else:
                    data_xr_vars[varname0].isel(time=0).plot(ax=ax)
                plipoint_coords = data_interp.plipoints.to_dataframe()
                ax.plot(plipoint_coords['plipoint_x'],plipoint_coords['plipoint_y'],'r-')
                ctx.add_basemap(ax=ax,crs="EPSG:4326",attribution=False)
                fig.tight_layout()
                fig.savefig(str(file_bc_out).replace('.bc','_polyline'))
                
                #plotting example data point
                for iF in [2]:#range(nPoints): 
                    data_vars = list(data_interp.data_vars)
                    fig,ax1 = plt.subplots(figsize=(10, 6))
                    data_interp[data_vars[0]].isel(plipoints=iF).T.plot()
                    fig.tight_layout()
                    fig.savefig(str(file_bc_out).replace('.bc',''))
    
    file_ext_out = Path(dir_output,'example_bnd.ext')
    ext_bnd.save(filepath=file_ext_out)
    
    time_passed = (dt.datetime.now()-dtstart).total_seconds()
    print(f'>>total script time passed: {time_passed:.2f} sec')

    
def preprocess_ini_cmems_to_nc(tSimStart = dt.datetime(1998,1,1),
        dir_data  = r'p:\i1000668-tcoms\03_newModel\01_input\02_bnd\data_opendap', #folder containing CMEMS so and thetao netcdf files
        dir_out = '.'):
    #TODO: merge with other ini script and make generic for getting an inifield out of CMEMS/etc regulargrid Dataset or a 2D/3D FM map/rst Dataset
    
    file_nc_list_so = glob.glob(f'{dir_data}\\cmems_so_*.nc')
    file_nc_list_thetao = glob.glob(f'{dir_data}\\cmems_thetao_*.nc')
    file_nc_list = file_nc_list_so + file_nc_list_thetao
    
    print(f'opening {len(file_nc_list)} datasets')
    data_xr = xr.open_mfdataset(file_nc_list)
    
    if 0: #this would be the proper way to do it, but FM needs two timesteps for some reason
        print('ds.interp()')
        data_xr_ontime = data_xr.interp(time=[tSimStart],kwargs=dict(bounds_error=True)) #bounds_error makes sure, outofbounds time results in "ValueError: A value in x_new is below the interpolation range."
    else:
        print('ds.sel()')
        data_xr_ontime = data_xr.sel(time=slice(tSimStart-dt.timedelta(days=1),tSimStart+dt.timedelta(days=1)))
    
    print('writing file')
    outFile = os.path.join(dir_out,f'InitialField_{tSimStart.strftime("%Y-%m-%d_%H-%M-%S")}.nc')
    data_xr_ontime.to_netcdf(outFile,format="NETCDF4_CLASSIC")
    
    
def preprocess_merge_meteofiles(
        mode = 'HYCOM', # 'HIRLAM_meteo' 'HIRLAM_meteo-heatflux' 'HARMONIE' 'HYCOM' 'ERA5_wind_pressure' 'ERA5_heat_model' 'ERA5_radiation' 'ERA5_rainfall' 'WOA'
        varkey_list = [],
        dir_data = [],
        dir_output = '.',
        time_slice = slice('2013-12-30','2014-01-01')
        ):

    if isinstance(varkey_list[0], list):
        varkey_lists = varkey_list
    else:
        varkey_list = [varkey_list]
        
    for varkey_list in varkey_lists:
        if 'HIRLAM' in mode:
            if mode == 'HIRLAM_meteo': #1year voor meteo crasht (HIRLAM72_*\\h72_*) door conflicting dimension sizes, sourcefolders opruimen? meteo_heatflux folders zijn schoner dus daar werkt het wel
                dir_data = 'P:\\1204257-dcsmzuno\\2014\\data\\meteo\\HIRLAM72_*' #files contain: ['air_pressure_fixed_height','northward_wind','eastward_wind']
            elif mode == 'HIRLAM_meteo-heatflux':
                dir_data = 'P:\\1204257-dcsmzuno\\2014\\data\\meteo-heatflux\\HIRLAM72_*' # files contain: ['dew_point_temperature','air_temperature','cloud_area_fraction']
            fn_match_pattern = 'h72_20131*.nc'
            file_out_prefix = 'h72_'
            preprocess = dfmt.preprocess_hirlam #temporary(?) fix for >1D-vars with same name as its dim
        elif mode == 'HARMONIE':
            dir_data = 'p:\\1204257-dcsmzuno\\data\\meteo\\HARMONIE\\nc\\air_*' #many invalid files, so subsetting here
            fn_match_pattern = 'HARMONIE_*_2020_*.nc'
            file_out_prefix = 'HARMONIE_'
            preprocess = None
        elif mode == 'HYCOM':
            dir_data = 'c:\\DATA\\dfm_tools_testdata\\GLBu0.08_expt_91.2'
            fn_match_pattern = 'HYCOM_ST_GoO_*.nc'
            file_out_prefix = 'HYCOM_ST_GoO_'
            preprocess = None
            #rename_variables = {'salinity':'so', 'water_temp':'thetao'}
        elif 'ERA5' in mode:
            fn_match_pattern = f'era5_.*({"|".join(varkey_list)})_.*.nc' #simpler but selects more files: 'era5_*.nc'
            file_out_prefix = f'era5_{"_".join(varkey_list)}_'
            preprocess = dfmt.preprocess_ERA5 #reduce expver dimension if present
        elif mode == 'WOA':
            dir_data = r'p:\1204257-dcsmzuno\data\WOA13'
            fn_match_pattern = 'woa13_decav_s*.nc'
            file_out_prefix = 'woa13_decav_s_'
            preprocess = dfmt.preprocess_woa #add 360-day calendar unit to time attrs before decode_cf
        else:
            raise Exception('ERROR: wrong mode %s'%(mode))
        
        if not os.path.exists(dir_output):
            os.makedirs(dir_output)
        
        file_nc = os.path.join(dir_data,fn_match_pattern)
        
        data_xr_tsel = dfmt.merge_meteofiles(file_nc=file_nc, time_slice=time_slice, 
                                             preprocess=preprocess,
                                             add_global_overlap=False, #GTSM specific: extend data beyond -180 to 180 longitude
                                             zerostart=False) #GTSM specific: extend data with 0-value fields 1 and 2 days before all_tstart
        
        #write to netcdf file
        print('>> writing file (can take a while): ',end='')
        dtstart = dt.datetime.now()
        try:
            times_np = data_xr_tsel['time'].to_series()
        except:
            times_np = data_xr_tsel['time'].to_numpy() #.to_series() does not work for woa 360_day data. .to_numpy() results in numpy.datetime64 for other datasets, which has no attribute strftime
        time_start_str = times_np[0].strftime("%Y%m%d")
        time_stop_str = times_np[-1].strftime("%Y%m%d")
        file_out = os.path.join(dir_output, f'{file_out_prefix}{time_start_str}to{time_stop_str}_{mode}.nc')
        data_xr_tsel.to_netcdf(file_out)
        print(f'{(dt.datetime.now()-dtstart).total_seconds():.2f} sec')
        
        
        #load outputfile
        data_xr_check = xr.open_dataset(file_out)
        
        for varkey in data_xr_check.data_vars:
            varsel = data_xr_check[varkey]
            if not set(['longitude','latitude']).issubset(set(varsel.coords)): #skipping vars without lat/lon coordinate
                continue
            print(f'plotting {varkey}')
            fig,ax1 = plt.subplots()
            if 'HIRLAM' in mode:
                varsel.isel(time=0).plot(ax=ax1,x='longitude',y='latitude') #x/y are necessary since coords are not 1D and dims
            elif 'depth' in data_xr_tsel[varkey].coords:
                varsel.isel(time=0).sel(depth=0).plot(ax=ax1)
            else:
                varsel.isel(time=0).plot(ax=ax1)
            file_out = os.path.join(dir_output, f'era5_{varkey}_{time_start_str}')
            fig.savefig(file_out)


# BATHYMETRY (TEMPORARY): p:\11209231-003-bes-modellering\hydrodynamica\hackathon\preprocessing\scripts\bathy_GEBCO2021asc.py

def GEBCO2asc(lon_min,lon_max,lat_min,lat_max,dir_out='.',suffix='full',polygon=None): #TODO: default arg is None, not ''
    """
    #input
    # =============================================================================
    # ## FULL
    # suffix  = 'full'
    # polygon = ''
    # lat_min =  11.5
    # lat_max =  13
    # lon_min = -69 #-68.55 left of Klein-Curacao
    # lon_max = -67
    # =============================================================================
    # =============================================================================
    # ## REFINEMENT
    # suffix  = 'refine'
    # polygon = ''
    # lat_min =  11.85
    # lat_max =  12.55
    # lon_min = -68.5
    # lon_max = -67.9
    # =============================================================================
    # =============================================================================
    # suffix  = 'coarse'
    # polygon = Path('p:\\i1000668-tcoms\\03_newModel\\01_input\\01_network\\bathy\\coarse.pol')
    # =============================================================================


    Parameters
    ----------
    lon_min : TYPE
        DESCRIPTION.
    lon_max : TYPE
        DESCRIPTION.
    lat_min : TYPE
        DESCRIPTION.
    lat_max : TYPE
        DESCRIPTION.
    dir_out : TYPE, optional
        DESCRIPTION. The default is '.'.
    suffix : TYPE, optional
        DESCRIPTION. The default is 'full'.
    polygon : TYPE, optional
        DESCRIPTION. The default is None.

    Raises
    ------
    Exception
        DESCRIPTION.

    Returns
    -------
    None.

    """
    warnings.warn(DeprecationWarning('modelbuilder.GEBCO2asc will be deprecated since asc grid refinement will be done with sliced netcdf data and meshkernel in the near future'))
    #settings
    source='GEBCO2021' #GEBCO2014 GEBCO2020 GEBCO2021 GEBCO2021SIT
    asc_fmt='%6d' #'%6d' '%8.2f'
    LatIndexer, LonIndexer = 'lat', 'lon'
    
    #type of path (windows/linux)
    if os.name=='nt':
        pdrive = 'p:\\'
    elif os.name == 'posix':
        pdrive = '/p'
    
    # source data
    if source=='GEBCO2021':
        file_nc = os.path.join(pdrive,'metocean-data','open','GEBCO','2021','GEBCO_2021.nc')
    else:
        raise Exception('invalid source')
    data = xr.open_dataset(file_nc)
    dsel = data.sel(**{LatIndexer: slice(lat_min, lat_max),LonIndexer: slice(lon_min, lon_max)})
    
    # output directory
    if not os.path.exists(dir_out):
        os.mkdir(dir_out)
    resinv_lonlat = np.round(1/np.diff(dsel.lon[:2]),2)
    filename_asc = os.path.join(dir_out,'%s_res1d%03ddeg_%s.asc'%(source,resinv_lonlat,suffix))
    
    # convert to .asc
    lonvals = dsel.lon.to_series().values
    latvals = dsel.lat.to_series().values
    elevvals = dsel.variables['elevation'].to_numpy()
    
    # make mask based on polygon
    if polygon is not None:
        polyfile_object = hcdfm.PolyFile(polygon)
        pli_PolyObjects = polyfile_object.objects
        lon_min,lon_max,lat_min,lat_max = None,None,None,None
        for iPO, pli_PolyObject_sel in enumerate(pli_PolyObjects):
            if iPO!=0:
                raise Exception('Expected only one polygon in file')
            xPO = np.array([point.x for point in pli_PolyObject_sel.points])
            yPO = np.array([point.y for point in pli_PolyObject_sel.points])
            xyPO = [(x,y) for x,y in zip(xPO,yPO)]
            poly = pth(xyPO) #TODO: this is an inpolygon function, use also in other places in dfm_tools
        lonGrid,latGrid = np.meshgrid(lonvals,latvals)
        lonGrid,latGrid = lonGrid.flatten(),latGrid.flatten()
        gridPoints = np.vstack((lonGrid,latGrid)).T
        gridMask   = poly.contains_points(gridPoints)
        gridMask   = gridMask.reshape(len(latvals),len(lonvals))
        elevvals[~gridMask] = 32767
    
    write_bathy_toasc(filename_asc,lonvals,latvals,elevvals,asc_fmt,nodata_val=32767)


#GRIDGENERATION (TEMPORARY): p:\11209231-003-bes-modellering\hydrodynamica\hackathon\preprocessing\scripts\gridgeneration.py

def make_basegrid(lon_min,lon_max,lat_min,lat_max,dx=0.05,dy=0.05,filepath='1_base_net.nc',name='empty'):
    warnings.warn(DeprecationWarning('modelbuilder.make_basegrid will be deprecated since asc grid refinement will be done with netcdf data and meshkernel in the near future'))
    # create base grid
    nox = int(np.round((lon_max-lon_min)/dx))
    noy = int(np.round((lat_max-lat_min)/dy))
    
    #mesh2d_input = Mesh2dFactory.create_rectilinear_mesh(rows=noy, columns=nox, origin_x=lon_min, origin_y=lat_min, spacing_x=dx, spacing_y=dy)
    mesh2d_input = Mesh2dFactory.create(rows=noy, columns=nox, origin_x=lon_min, origin_y=lat_min, spacing_x=dx, spacing_y=dy)
    
    # set to spherical
    mk = MeshKernel(is_geographic=True)
    mk.mesh2d_set(mesh2d_input)
    mesh2d_mesh_kernel = mk.mesh2d_get()
    
    xu_grid = xu.Ugrid2d.from_meshkernel(mesh2d_mesh_kernel)

    # plot grid
    fig, ax = plt.subplots()
    xu_grid.plot(ax=ax)
    # add basemap
    source = ctx.providers.Esri.WorldImagery
    ctx.add_basemap(ax=ax, source=source, crs='EPSG:4326', attribution=False)
    
    #write xugrid grid to netcdf
    xu_grid.to_dataset().to_netcdf(filepath) #TODO: why is .to_dataset necessary()?



def refine_basegrid(bathydataset_refine,filepath_in='1_base_net.nc',dir_out='.',dtmax=200,dxmin_refine='2000',DIMRver='2.23.05.78259'):
    warnings.warn(DeprecationWarning('modelbuilder.refine_basegrid will be deprecated since asc grid refinement will be done with netcdf data and meshkernel in the near future'))
    #settings
    bathydataset_dummy='p:/11209231-003-bes-modellering/hydrodynamica/hackathon/preprocessing/grid/dummy.xyz' # file containing:      190     150     -9999
    #exePath = '/p/d-hydro/dimrset/weekly/%s/lnx64/bin/run_dflowfm.sh'%DIMRver
    exePath = 'p:/d-hydro/dimrset/weekly/%s/x64/dflowfm/bin/dflowfm-cli.exe'%DIMRver
    #os.system('set PATH=p:/d-hydro/dimrset/weekly/%s/x64/share/bin/;%%PATH%%'%DIMRver)
    os.environ['PATH'] += os.pathsep + 'p:/d-hydro/dimrset/weekly/%s/x64/share/bin'%DIMRver
    
    # refine base grid
    os.system('%s --refine:dtmax=%s:hmin=%s:directional=0:outsidecell=0:connect=0:smoothiters=3:jasfer3d=1 %s %s'%(exePath,dtmax,dxmin_refine,filepath_in,bathydataset_refine))
    os.replace('outdtmax%sdxmin%s_net.nc'%(dtmax,dxmin_refine),os.path.join(dir_out,'2_refined_net.nc'))
    
    # connect cells
    os.system('%s --refine:dtmax=%s:hmin=%s:directional=0:outsidecell=0:connect=1:smoothiters=0:jasfer3d=1 %s %s'%(exePath,dtmax,dxmin_refine,os.path.join(dir_out,'2_refined_net.nc'),bathydataset_dummy))
    os.replace('outdtmax%sdxmin%s_net.nc'%(dtmax,dxmin_refine),os.path.join(dir_out,'3_connected_net.nc'))
    
    # cut coastlines
    with open('cutcellpolygons.lst', 'w') as file:
        file.write('p:/i1000668-tcoms/03_newModel/01_input/01_network/scripts/construct_files/GSHHS_high_min10km2.ldb')
    os.system('%s --cutcells:jasfer3d=1 %s'%(exePath,os.path.join(dir_out,'3_connected_net.nc')))
    os.replace('out_net.nc',os.path.join(dir_out,'4_cut_net.nc'))
    os.remove('cutcellpolygons.lst')


def interp_bathy(bathydataset_full,filepath_in='4_cut_net.nc',filepath_out='5_bathy_net.nc',DIMRver='2.23.05.78259'):
    warnings.warn(DeprecationWarning('modelbuilder.interp_bathy will be deprecated since asc grid refinement will be done with netcdf data and meshkernel in the near future'))
    #settings
    exePath = 'p:/d-hydro/dimrset/weekly/%s/x64/dflowfm/bin/dflowfm-cli.exe'%DIMRver
    
    # make mdu
    # make ext
    
    # interpolate bathymetry
    os.system('%s --nodisplay --autostartstop bathy.mdu --savenet -o %s'%(exePath,filepath_out))
