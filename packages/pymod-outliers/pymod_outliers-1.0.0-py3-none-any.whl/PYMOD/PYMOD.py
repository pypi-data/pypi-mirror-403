#!/usr/bin/env python
# coding: utf-8

"""
Module PYMOD - Multivariate Outlier Detection for Solar Panel Data

This module implements a comprehensive outlier detection pipeline for solar 
photovoltaic (PV) systems using multiple statistical and clustering methods.

Methods Used:
    1. Physical Validation: Filter impossible GHI-Power combinations
    2. Statistical Analysis: Z-score and IQR-based filtering
    3. Clustering: DBSCAN algorithm for spatial pattern recognition
    4. Boundary Construction: Linear interpolation to build efficiency curves
    5. Real-time Classification: Validate new data points against learned boundaries

Key Functions:
    - detect_outliers(): Main pipeline orchestrating all methods
    - ghi_p_zeros(): Filter physically impossible measurements
    - z_scores(): Statistical outlier detection using Z-score method
    - dbscan_func(): Spatial clustering using DBSCAN
    - interpolation_func(): Build efficiency boundaries from inliers
    - linear_interpol(): Validate high irradiance points
    - check_inliers_outliers(): Real-time point classification

Date: 08/01/2026
Author: SAAD BASMA
Co-Author: BOUADA MOHAMED
Version: 1.0
"""


# --------------------------------------------------
# IMPORTS
# --------------------------------------------------

import numpy as np 
import pandas as pd 
from scipy import stats
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt


# --------------------------------------------------
# 1: ghi_p_zeros
# --------------------------------------------------

def ghi_p_zeros(data1, GHI_column, Power_column):
    """
    Invalid Data filtering by : 
    -- GHI >= 200 with Power = 0 
    -- GHI == 00 while Power > 0

    Args:
        data1 (pd.DataFrame): Input Datarame 
        GHI_column (str): GHI column 
        Power_column (str): Power column

    Returns: 
        pd.Index -> Index of valid data that respect the two conditions (filtering)
    """
    # Find rows with GHI high but no power output (panel malfunction)
    l1 = list((data1[(data1[GHI_column] >= 200) & (data1[Power_column] == 0.0)]).index)
    
    # Find rows with no GHI but power output (measurement error)
    l2 = list((data1[(data1[GHI_column] == 0.0) & (data1[Power_column] > 0)]).index)
    
    # Remove invalid rows
    data2 = data1.drop(l1, axis=0)
    data3 = data2.drop(l2, axis=0)
    
    il = data3.index
    return il


# --------------------------------------------------
# 2: z_scores
# --------------------------------------------------

def z_scores(data1, pas_g, GHI_column, Power_column, Version_column):
    """
    Detect inliers using Z-score and IQR method within GHI intervals.
    Identifies statistically valid power readings by 
    binning data into GHI ranges and applying IQR filtering.

    Args:
        data1 (pd.DataFrame): Input dataFrame
        pas_g (int): step size for GHI binning
        GHI_column (str): GHI column
        Power_column (str): Power column
        Version_column (str): Panel version column

    Returns:
        list : Indice of inlier rows
    """
    IL_idx = []
    
    # Get GHI range
    ming = data1[GHI_column].min()
    maxg = data1[GHI_column].max()
    
    # Create GHI intervals (bins)
    ghi_interval = np.arange(ming, maxg + pas_g, pas_g)
    
    # Process each panel version separately
    for arr in (data1[Version_column].unique()):
        dt = data1[data1[Version_column] == arr]
        
        # Process each GHI interval
        for i in range(len(ghi_interval) - 1):
            min_v_ghi, max_v_ghi = ghi_interval[i], ghi_interval[i + 1]
            
            # Filter data for this GHI interval
            df_ghi = dt[(dt[GHI_column] >= min_v_ghi) &
                        (dt[GHI_column] < max_v_ghi)]
            
            # Calculate Z-scores of power values
            ZC = stats.zscore(df_ghi[Power_column])
            
            # Calculate IQR bounds (Tukey's method)
            q1 = np.percentile(abs(ZC), 25)
            q3 = np.percentile(abs(ZC), 75)
            iqr = q3 - q1
            upper_bound = q3 + 1.5 * iqr
            
            # Add Z-scores to dataframe
            df_ghi['ZC'] = ZC
            
            # Get indices of inliers (within IQR bounds)
            il = list((df_ghi[df_ghi['ZC'] >= -upper_bound]).index)
            
            IL_idx.extend(il)

    return IL_idx


# --------------------------------------------------
# 3: dbscan_func
# --------------------------------------------------

def dbscan_func(data1, GHI_column, Power_column, Version_column, eps, min_s):
    """
    Clustering solar data using DBSCAN algorithm to identify inliers
    based on GHI-Power spatial patterns.
    Finds optimal eps and min_samples parameters to separate inliers (label 0) from 
    outliers (label -1).

    Args:
        data1 (pd.DataFrame): Filtered data
        GHI_column (str): GHI column
        Power_column (str): Power column
        Version_column (str): panel version column
        eps (list): Epsilon values for the test
        min_s (list): Minimum sample values for the test

    Returns:
        tuple: inlier indices and inlier percentages per version.
    """
    percentages = []
    cols = [GHI_column, Power_column]
    IL = []
    
    # Process each panel version
    for i in data1[Version_column].unique():
        break_out = False
        features = data1[data1[Version_column] == i]
        
        if (features.shape[0] != 0):
            # Standardize the features for DBSCAN
            scaler = StandardScaler()
            features_scaled = scaler.fit_transform(features[cols])
            
            # Test different parameter combinations
            for e in eps:
                for m in min_s:
                    # Apply DBSCAN
                    dbscan = DBSCAN(eps=e, min_samples=m)
                    labels = dbscan.fit_predict(features_scaled)
                    features['labels'] = labels
                    s = features[features['labels'] != -1].shape[0]
                    
                    # Check if we got optimal clustering (2 labels)
                    if (len(features['labels'].unique()) == 2):
                        break_out = True
                        break
                
                if (break_out == True):     
                    break
            
            # Store results
            percentages.append((s * 100) / features.shape[0])
            idx = list(features[features['labels'] != -1].index)
            IL.extend(idx)
        
    return IL, percentages


# --------------------------------------------------
# 4: calculate_slop
# --------------------------------------------------

def calculate_slop(ghimin1, ghimin2, pmin1, pmin2):
    """
    Calculate slope and intercept from two GHI/Power points.

    Args:
        ghimin1 (float): GHI value at point 1
        ghimin2 (float): GHI value at point 2
        pmin1 (float): Power value corresponds to ghimin1
        pmin2 (float): Power value corresponds to ghimin2

    Returns:
        tuple: slope (a), intercept (b)
    """     
    # Calculate slope: a = (y2 - y1) / (x2 - x1)
    a = (pmin2 - pmin1) / (ghimin2 - ghimin1)
    
    # Calculate intercept: b = y1 - a*x1
    b = pmin1 - (a * ghimin1)
    
    return a, b


# --------------------------------------------------
# 5: interpolation_func
# --------------------------------------------------

def interpolation_func(df, IL, pas_g, f, GHI_column, Power_column, Version_column):
    """
    Creates boundaries from inliers and identify additional valid outliers points using 
    linear interpolation.
    Creates upper/lower power limits for each GHI interval based on inlier distribution.
    
    Args:
        df (pd.DataFrame): Full dataset
        IL (list): DBSCAN Inlier indices
        pas_g (int): GHI bin size
        f (float): Defined threshold for the Power (W)
        GHI_column (str): GHI column
        Power_column (str): Power column
        Version_column (str): panel version column

    Returns:
        tuple: (additional inlier indices, slope a1, intercept b1, 
                slope a2, intercept b2, boundary dataframe)
    """ 
    columns = [Version_column, 'GHI_start', 'GHI_end', 'a1', 'b1', 'a2', 'b2']
    df_borders = pd.DataFrame(columns=columns)
    
    # Variables for high irradiance boundary
    a = b = c = d = 0
    thebool = 0
    OL_to_add = []
    IL_to_keep = []
    
    # Round values for consistency
    df['Active_Power_r'] = df[Power_column].round(0)
    df['Global_Horizontal_Radiation_r'] = df[GHI_column].round(0)
    
    # Separate inliers and outliers
    df_IL = df.loc[IL]
    df_OL = df.drop(index=IL)
    
    # Get data ranges
    minp = df_IL[Power_column].min()
    maxg = df_IL[GHI_column].max()
    maxp = df_IL[Power_column].max()
    ming = df_IL[GHI_column].min()

    # Create GHI intervals
    ghi_interval = np.arange(ming, maxg + pas_g, pas_g)
    
    # Process intervals from highest to lowest GHI
    for i in range(len(ghi_interval) - 1, 0, -1):
        arr = []
        arr.extend(df[Version_column].unique())
        
        # First interval (highest GHI)
        if (i == len(ghi_interval) - 1):
            max_v_ghi, min_v_ghi = ghi_interval[i], ghi_interval[i - 1]

            dfghi = df_IL[(df_IL['Global_Horizontal_Radiation_r'] >= min_v_ghi) &
                        (df_IL['Global_Horizontal_Radiation_r'] <= max_v_ghi)]
            
            min_ghi = dfghi['Global_Horizontal_Radiation_r'].min()
            max_ghi = dfghi['Global_Horizontal_Radiation_r'].max()
            
            # Find power bounds at max GHI
            min1_v_p = dfghi[dfghi['Global_Horizontal_Radiation_r'] == max_ghi]['Active_Power_r'].min()
            max1_v_p = dfghi[dfghi['Global_Horizontal_Radiation_r'] == max_ghi]['Active_Power_r'].max()
            
            # Find power bounds at min GHI
            max2_v_p = dfghi[dfghi['Global_Horizontal_Radiation_r'] == min_ghi]['Active_Power_r'].max()
            min2_v_p = dfghi[dfghi['Global_Horizontal_Radiation_r'] == min_ghi]['Active_Power_r'].min()
            
            IL_max_ghi = max_ghi
            IL_max_power = max1_v_p
            IL_min_power = min1_v_p
            
        # Other intervals
        else:
            max_v_ghi, min_v_ghi = min_ghi, ghi_interval[i - 1]
            
            dfghi = df_IL[(df_IL['Global_Horizontal_Radiation_r'] >= min_v_ghi) &
                        (df_IL['Global_Horizontal_Radiation_r'] <= max_v_ghi)]
            
            min_ghi = dfghi['Global_Horizontal_Radiation_r'].min()
            max_ghi = dfghi['Global_Horizontal_Radiation_r'].max()
        
            # Use previous interval's bounds as starting point
            min1_v_p = min2_v_p
            max1_v_p = max2_v_p
            
            # Get new bounds at min GHI
            max2_v_p = dfghi[dfghi['Global_Horizontal_Radiation_r'] == min_ghi]['Active_Power_r'].max()
            min2_v_p = dfghi[dfghi['Global_Horizontal_Radiation_r'] == min_ghi]['Active_Power_r'].min()
        
        arr.extend([max_ghi])
        arr.extend([min_ghi])
        
        # Adjust if jump is too large (potential data gap)
        if (abs(min1_v_p - min2_v_p) > f):
            df_pv = dfghi[dfghi['Global_Horizontal_Radiation_r'] == min_ghi].sort_values(by=['Active_Power_r'], ascending=True)
            df_pv = df_pv.reset_index(drop=True)
            
            for i in df_pv.index:
                if (abs(min1_v_p - (df_pv['Active_Power_r'][i])) <= f):
                    min2_v_p = df_pv['Active_Power_r'][i]
                    break
        
        # Adjust upper bound if necessary
        if (abs(max1_v_p - max2_v_p) > f):
            df_pv = dfghi[dfghi['Global_Horizontal_Radiation_r'] == min_ghi].sort_values(by=['Active_Power_r'], ascending=False)
            
            for i in df_pv.index:
                if (abs(max1_v_p - df_pv['Active_Power_r'][i]) <= f):
                    max2_v_p = df_pv['Active_Power_r'][i]
                    break
        
        # Calculate boundary lines
        a1, b1 = calculate_slop(max_ghi, min_ghi, min1_v_p, min2_v_p)
        a2, b2 = calculate_slop(max_ghi, min_ghi, max1_v_p, max2_v_p)
        
        arr.extend([a1])
        arr.extend([b1])
        arr.extend([a2])
        arr.extend([b2])
        
        # Add to boundary dataframe
        new_row = pd.Series({
            Version_column: arr[0], 
            'GHI_start': arr[1], 
            'GHI_end': arr[2],
            'a1': arr[3],
            'b1': arr[4],
            'a2': arr[5],
            'b2': arr[6]
        })
        df_borders = pd.concat([df_borders, new_row.to_frame().transpose()], ignore_index=True)
        
        # Validate outliers against boundaries
        dfg = df[(df['Global_Horizontal_Radiation_r'] >= min_ghi) & 
                (df['Global_Horizontal_Radiation_r'] <= max_ghi)]
        
        for j in dfg.index:
            power = dfg['Active_Power_r'][j]
            
            # Calculate boundary limits
            d1 = (dfg['Global_Horizontal_Radiation_r'][j] * a1) + b1
            d2 = (dfg['Global_Horizontal_Radiation_r'][j] * a2) + b2
            
            # Check if within boundaries
            if ((power >= d1) & (power <= d2)):
                OL_to_add.append(j)
    
        # Store boundary for high irradiance (GHI >= 1000)
        if ((min_ghi <= 1000) & (thebool == 0)):
            a = a1
            b = b1
            c = a2
            d = b2
            thebool = 1
    
    return OL_to_add, a, b, c, d, df_borders


# --------------------------------------------------
# 6 : linear_interpol
# --------------------------------------------------

def linear_interpol(df, a1, b1, a2, b2):
    """
    Validate outlier points against linear efficiency boundaries for high irradiance (GHI >= 1000 W/m²).

    Args:
        df (pd.DataFrame): Dataset with rounded GHI/Power columns
        a1 (float): Slope of lower boundary	
        b1 (float): Intercept of lower boundary
        a2 (float): Slope of upper boundary
        b2 (float): Intercept of upper boundary

    Returns:
        list: Indices of points within efficiency boundaries
    """
    # Data after max GHI in DBSCAN will be preserved 
    # because at high GHI panel efficiency may decrease due to temperature effects
    
    OL_to_add = []
    dfg = df[(df['Global_Horizontal_Radiation_r'] >= 1000)]
   
    for j in dfg.index:
        power = dfg['Active_Power_r'][j]
        
        # Calculate boundary limits
        d1 = (dfg['Global_Horizontal_Radiation_r'][j] * a1) + b1
        d2 = (dfg['Global_Horizontal_Radiation_r'][j] * a2) + b2
            
        # Check if within boundaries
        if ((power >= d1) & (power <= d2)):
            OL_to_add.append(j)
  
    return OL_to_add


# --------------------------------------------------
# 7: check_inliers_outliers
# --------------------------------------------------

def check_inliers_outliers(df_borders, row, pv_power, GHI_column, Power_column, Version_column):
    """
    Classify a single data point as inlier (0) or outlier (-1) using stored efficiency boundaries.

    Args:
        df_borders (pd.DataFrame): Boundary coefficients per GHI interval
        row (pd.Series): Point to classify
        pv_power (float): power value to check (classify)
        GHI_column (str): GHI column
        Power_column (str): Power column
        Version_column (str): panel version column

    Returns:
        int : 0 or -1 (0 : inlier, -1: outlier)
    """
    inl = -1
    
    ghi = row[GHI_column]
    arr = row[Version_column]
    
    # Get boundaries for this version
    df_c = df_borders[(df_borders[Version_column] == arr)]
    df_c = df_c.reset_index(drop=True)
    
    max_ghi = df_c['GHI_end'].max()
    ghi_interval = np.arange(0, max_ghi + 100, 100)
    
    # Find correct interval for this GHI
    for i in range(len(ghi_interval) - 1, 0, -1):
        max_v_ghi, min_v_ghi = ghi_interval[i], ghi_interval[i - 1]
        
        if (min_v_ghi <= ghi < max_v_ghi):
            # Get boundary coefficients
            a1 = df_c[df_c['GHI_end'] == min_v_ghi]['a1'].item()
            b1 = df_c[df_c['GHI_end'] == min_v_ghi]['b1'].item()
            a2 = df_c[df_c['GHI_end'] == min_v_ghi]['a2'].item()
            b2 = df_c[df_c['GHI_end'] == min_v_ghi]['b2'].item()
            
            # Calculate boundaries
            d1 = (ghi * a1) + b1
            d2 = (ghi * a2) + b2
            
            # Check if within boundaries
            if d1 <= pv_power <= d2:
                inl = 0
    
    # Special case for high irradiance (GHI >= 1000)
    if (ghi >= 1000):
        a1 = df_c[df_c['GHI_end'] == 1000]['a1'].item()
        b1 = df_c[df_c['GHI_end'] == 1000]['b1'].item()
        a2 = df_c[df_c['GHI_end'] == 1000]['a2'].item()
        b2 = df_c[df_c['GHI_end'] == 1000]['b2'].item()
        
        d1 = (ghi * a1) + b1
        d2 = (ghi * a2) + b2
        
        if d1 <= pv_power <= d2:
            inl = 0

    return inl


# --------------------------------------------------
# 8: detect_outliers (MAIN PIPELINE)
# --------------------------------------------------

def detect_outliers(data1, Version_column, GHI_column, Power_column, Rating_column, eps, min_s):
    """    
    Complete outlier detection pipeline combining Z-score, DBSCAN, 
    and interpolation methods.
    
    Filters invalid data, applies multiple detection algorithms, builds 
    efficiency curves, and returns final inlier list.

    Args:
        data1 (pd.DataFrame): Raw solar data
        Version_column (str): Panel version column
        GHI_column (str): GHI column
        Power_column (str): Power column
        Rating_column (str): Panel rated power column
        eps (list): Epsilon values to test
        min_s (list): Minimum sample values to test
        
    Returns : 
        tuple : (efficiency boundary dataframe, list of final inlier indices)
    """
    # Reset index for clean data handling
    data1 = data1.reset_index(drop=True)
    
    # Step 1: Filter physically impossible data
    ilzero = ghi_p_zeros(data1, GHI_column, Power_column)
    Dzeros = data1.loc[ilzero]
    print('Dzeros shape : ', Dzeros.shape)
    
    # Step 2: Apply Z-score filtering
    IL_ZC = z_scores(Dzeros, 100, GHI_column, Power_column, Version_column)
    data_ZC = Dzeros.loc[IL_ZC]
    
    # Step 3: Apply DBSCAN clustering
    il_t, percentages = dbscan_func(data_ZC, GHI_column, Power_column, Version_column, eps, min_s)
    print('data_before db shape : ', data_ZC.shape)
    
    data1_db = data_ZC.loc[il_t]
    data1_db = data1_db.reset_index(drop=True)
    print('data_after db shape : ', data1_db.shape)
    
    # Initialize boundary dataframe
    columns = [Version_column, 'GHI_start', 'GHI_end', 'a1', 'b1', 'a2', 'b2']
    df_borders = pd.DataFrame(columns=columns)
    
    # Separate inliers and outliers
    inliers = data1.loc[il_t]
    outliers = data1.drop(il_t)
    print('inliers shape : ', inliers.shape)
    print('outliers shape : ', outliers.shape)
    
    inliers_all = []
    
    # Step 4: Process each panel version
    for arr in (data1[Version_column].unique()):
        dt = data1[data1[Version_column] == arr]
        dt_in = inliers[inliers[Version_column] == arr]
        dt_out = outliers[outliers[Version_column] == arr]
        print('dt_in shape : ', dt_in.shape)
        print('dt_out shape : ', dt_out.shape)
        
        il = dt_in.index
        
        # Calculate efficiency threshold from rated power
        eff = round((dt[Rating_column].max()) / 10, 0)
        
        # Step 5: Build efficiency boundaries and validate outliers
        inliers_to_keep, a, b, c, d, dfb = interpolation_func(dt, il, 100, eff, GHI_column, Power_column, Version_column)
        print('inliers to keep : ', len(inliers_to_keep))
        
        df_borders = pd.concat([df_borders, dfb], ignore_index=True)
        
        # Step 6: Validate high irradiance points
        inlier_interpol = linear_interpol(dt, a, b, c, d)
        
        # Collect all inliers
        inliers_all.extend(inliers_to_keep)
        inliers_all.extend(inlier_interpol)

    # Remove duplicates
    unique_inliers = list(set(inliers_all)) 
        
    return df_borders, unique_inliers




