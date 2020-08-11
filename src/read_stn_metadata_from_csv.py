    
###############################################################################
# read_stn_metadata_from_csv.py
# author: Craig Smith 
# purpose: read station metadata csv file  
# usage:  
#    use_stn = 'all'
#    use_stn = 'mnet=1' # NWS only  
#    use_stn = 'mnet=1,2' # NWS, RAWS 
#    use_stn = 'all' # NWS, RAWS 
#    use_stn = '4,5,9,10'      
#    print_stn_info = 1
#    read_stn_metadata_type = 'csv' # 'db' or 'csv'
# if   (read_stn_metadata_type == 'csv'):
#     (dict_stn_metadata) = read_stn_metadata_from_csv(dir_work, project_name, use_stn, print_stn_info)
# version history 
#   05/04/2018 - forked to new library 
#   02/03/2019 - changed print_stn_info from 0/1 to boolean
# to do: 
#   - 
# notes: 
#   - 
# debugging: 
#   - 
#
###############################################################################


###############################################################################
# 
 
def read_stn_metadata_from_csv(stn_metadata_file_name, use_stn, print_stn_info):

    import pandas as pd
    import os 

    stn_read_df = pd.read_csv(stn_metadata_file_name,index_col=0)
    stn_name = stn_read_df['stn_name'].values
    stn_id   = stn_read_df['stn_id'].values
    stn_lon  = stn_read_df['stn_lon'].values
    stn_lat  = stn_read_df['stn_lat'].values
    stn_ele  = stn_read_df['stn_ele'].values
    stn_obs_hgt = stn_read_df['stn_obs_hgt'].values
    stn_mnet_id = stn_read_df['stn_mnet_id'].values
    stn_tmzn = stn_read_df['stn_tmzn'].values
    stn_dt_start = stn_read_df['stn_datetime_start'].values
    stn_dt_end = stn_read_df['stn_datetime_end'].values
    stn_state = stn_read_df['stn_state'].values
    stn_county = stn_read_df['stn_county'].values
    n_stn = len(stn_lat)
    
    del stn_read_df
    
    print ('use_stn is %s ' % (use_stn)) 
 
    if (use_stn != 'all'): 
        if   ('mnet' in use_stn):  
            use_stn_split = use_stn.split('=')
            mnet_id_list = use_stn_split[-1]
            mnet_id_list = mnet_id_list.split(',')
            n_mnet_id = len(mnet_id_list)            
            mnet_id_int = []
            for nm in range(0,n_mnet_id,1): 
                mnet_id_int.append(int(mnet_id_list[nm]))     
            use_stn = []
            for s in range(0,n_stn,1):
               # if (stn_mnet_id[s] == mnt_id_int): 
               if (stn_mnet_id[s] in mnet_id_int): 
                   use_stn.append(s)
        elif ('mnet' not in use_stn):  
            use_stn_split = use_stn.split(',')
            n_stn = len(use_stn_split)
            use_stn = []
            for s in range(0, n_stn, 1):
                use_stn.append(int(use_stn_split[s]))  
        
        stn_name           = stn_name          [use_stn]
        stn_id             = stn_id            [use_stn] 
        stn_lon            = stn_lon           [use_stn] 
        stn_lat            = stn_lat           [use_stn] 
        stn_ele            = stn_ele           [use_stn] 
        stn_obs_hgt        = stn_obs_hgt       [use_stn]   
        stn_mnet_id        = stn_mnet_id       [use_stn]
        stn_tmzn           = stn_tmzn          [use_stn]
        stn_datetime_start = stn_datetime_start[use_stn] 
        stn_datetime_end   = stn_datetime_end  [use_stn] 
        #stn_state          = stn_state         [use_stn] 
        #stn_county         = stn_county        [use_stn] 
        #stn_cwa            = stn_cwa           [use_stn] 
        #stn_notes          = stn_notes         [use_stn] 

    n_stn = len(stn_lat)
    if (print_stn_info): 
        print ('station infomation list ') 
        # for s,stn_name_temp in enumerate(stn_name):          
        for s in range(0, n_stn, 1): 
           #print ('  stn_id %s lon %s lat %s ele %s obs_hgt %s ' % (stn_id[s], stn_lon[s], stn_lat[s], stn_ele[s], stn_obs_hgt[s])) 
           print ('  %s, lon %2.2f, lat %2.2f, ele %6.2f obs_hgt %2.1f, %s ' % (stn_id[s], stn_lon[s], stn_lat[s], stn_ele[s], stn_obs_hgt[s], stn_name[s])) 

    stn_metadata_dict = {}
    stn_metadata_dict['stn_name']           = stn_name
    stn_metadata_dict['stn_id']             = stn_id
    stn_metadata_dict['stn_lon']            = stn_lon
    stn_metadata_dict['stn_lat']            = stn_lat
    stn_metadata_dict['stn_ele']            = stn_ele
    stn_metadata_dict['stn_obs_hgt']        = stn_obs_hgt
    stn_metadata_dict['stn_mnet_id']        = stn_mnet_id
    stn_metadata_dict['stn_tmzn']           = stn_tmzn
    stn_metadata_dict['stn_dt_start']       = stn_dt_start
    stn_metadata_dict['stn_dt_end']         = stn_dt_end
    #stn_metadata_dict['stn_state']          = stn_state
    #stn_metadata_dict['stn_county']         = stn_county
    #stn_metadata_dict['stn_cwa']            = stn_cwa
    stn_metadata_dict['n_stn']              = n_stn 

    return stn_metadata_dict 

# read_stn_metadata  
###############################################################################

