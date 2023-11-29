import pandas as pd


def percent_collagen_mean(df):
    hp_percentage = 10.5 # hydroxyproline percentage in collagen
    # for biopsy_result

    # convert mg/cm2 to collagen mg/cm2, divide by 0.105
    df['collagen_mg_per_cm2'] = df['mg_per_cm2_mean']/(hp_percentage/100)

    print(df['collagen_mg_per_cm2'])
    df['collagen_mg_per_cm2_std'] = df['mg_per_cm2_std']/(hp_percentage/100)
    
    print(df['tissue_areal_density_mg_per_cm2'] - df['areal_density_mg_per_cm2'])
    # collagen percent calculation
    df['percent_collagen'] = df['collagen_mg_per_cm2']/(df['tissue_areal_density_mg_per_cm2'] - df['areal_density_mg_per_cm2'])*100
    df['percent_collagen_std'] = df['collagen_mg_per_cm2_std']/(df['tissue_areal_density_mg_per_cm2'] - df['areal_density_mg_per_cm2'])*100

    return df
