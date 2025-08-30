from sklearn.cluster import KMeans
from sklearn.model_selection import GroupShuffleSplit
import pandas as pd

def make_blocks(df, n_blocks, lon_col='long', lat_col='lat', random_state=0):
    """
    Assigns each row in df to a spatial block using KMeans clustering.
    
    Parameters:
        df (pd.DataFrame): Input dataframe.
        n_blocks (int): Number of spatial blocks to create.
        lon_col (str): Column name for longitude.
        lat_col (str): Column name for latitude.
        random_state (int): Random seed.
    
    Returns:
        pd.DataFrame: Copy of df with added 'block_id' column.
    """
    coords = df[[lon_col, lat_col]].to_numpy()
    block_ids = KMeans(n_clusters=n_blocks, random_state=random_state).fit_predict(coords)
    df_copy = df.copy()
    df_copy['block_id'] = block_ids
    return df_copy


def split_blocks(df_with_blocks, test_size=0.3, block_col='block_id', random_state=42):
    """
    Splits a block-assigned dataframe into train and test sets, keeping blocks intact.
    
    Parameters:
        df_with_blocks (pd.DataFrame): Dataframe containing block assignments.
        test_size (float): Fraction of blocks to assign to test set.
        block_col (str): Name of the block ID column.
        random_state (int): Random seed.
    
    Returns:
        (pd.DataFrame, pd.DataFrame): Train dataframe, Test dataframe.
    """
    gss = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=random_state)
    train_idx, test_idx = next(gss.split(df_with_blocks, groups=df_with_blocks[block_col]))
    
    train_df = df_with_blocks.iloc[train_idx].reset_index(drop=True)
    test_df = df_with_blocks.iloc[test_idx].reset_index(drop=True)
    
    return train_df, test_df


'''
Implementation
'''
# from BlockCV import split_blocks
# from BlockCV import make_blocks
# # n_blocks = len(data_vid) // 20

# data_mar_blocks = make_blocks(data_mar, n_blocks=10)
# train_mar_df, test_mar_df = split_blocks(data_mar_blocks, test_size=0.3)
