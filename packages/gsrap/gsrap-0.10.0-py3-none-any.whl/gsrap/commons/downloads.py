import requests
import io
import threading
import time
import tempfile
import json
import glob
import sys


import gdown
import pandas as pnd




class SimpleLoadingWheel():
    # a simple endless loading wheel
    
    msg = ''
    wheel_figures = ['|', '/', '-', '\\']
    wheel_cnt = 0
    
    def __init__(self, msg='Please wait... '):
        self.msg = msg
    
    def proceed(self):
        print(f"{self.msg}{self.wheel_figures[self.wheel_cnt]}", file=sys.stderr, end='\r')
        self.wheel_cnt += 1
        if self.wheel_cnt == 4: self.wheel_cnt = 0
        time.sleep(0.5)
        
    def clear(self):
        clear_str = ''.join([' ' for i in range(len(self.msg)+1)])
        print(f'{clear_str}', file=sys.stderr, end='\r')
        wheel_cnt = 0
    


def get_dbuni(logger):
    
    
    #sheet_id = "1dXJBIFjCghrdvQtxEOYlVNWAQU4mK-nqLWyDQeUZqek"
    sheet_id = "1dCVOOnpNg7rK3iZmTDz3wybW7YrUNoClnqezT9Q5bpc" # alternative
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"
    response = requests.get(url)  # download the requested file
    if response.status_code == 200:
        excel_data = io.BytesIO(response.content)   # load into memory
        exceldb = pnd.ExcelFile(excel_data)
    else:
        logger.error(f"Error during download. Retry! If persists, please contact the developer.")
        return 1
    
    
    # check table presence
    sheet_names = exceldb.sheet_names
    for i in ['T', 'R', 'M', 'curators']: 
        if i not in sheet_names:
            logger.error(f"Sheet '{i}' is missing!")
            return 1
        
        
    # load the tables
    dbuni = {}
    dbuni['T'] = exceldb.parse('T')
    dbuni['R'] = exceldb.parse('R')
    dbuni['M'] = exceldb.parse('M')
    dbuni['curators'] = exceldb.parse('curators')
    
    
    # check table headers
    headers = {}
    headers['T'] = ['rid', 'rstring', 'kr', 'gpr_manual', 'name', 'curator', 'notes']
    headers['R'] = ['rid', 'rstring', 'kr', 'gpr_manual', 'name', 'curator', 'notes']
    headers['M'] = ['pure_mid', 'formula', 'charge', 'kc', 'name', 'inchikey', 'curator', 'notes']
    headers['curators'] = ['username', 'first_name', 'last_name', 'role', 'mail']
    for i in dbuni.keys(): 
        if set(dbuni[i].columns) != set(headers[i]):
            logger.error(f"Sheet '{i}' is missing the columns {set(headers[i]) - set(dbuni[i].columns)}.")
            return 1
        
    return dbuni



def get_dbexp(logger):
    
    
    sheet_id = "1qGbIIipHJgYQjk3M0xDWKvnTkeInPoTeH9unDQkZPwg"
    #sheet_id = "1qxTRf30SeT9WJFYxWm2ChCxkTR0sTn7BbDOFhUuUQIE"   # alternative
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"
    response = requests.get(url)  # download the requested file
    if response.status_code == 200:
        excel_data = io.BytesIO(response.content)   # load into memory
        exceldb = pnd.ExcelFile(excel_data)
    else:
        logger.error(f"Error during download. Retry! If persists, please contact the developer.")
        return 1
    
    
    # check table presence
    sheet_names = exceldb.sheet_names
    for i in ['media', 'PM1', 'PM2A', 'PM3B', 'PM4A', 'MWF', 'DNA', 'RNA', 'PROTS', 'LIPIDS_PL', 'LIPIDS_FA', 'authors']: 
        if i not in sheet_names:
            logger.error(f"Sheet '{i}' is missing!")
            return 1
        
        
    # load the tables
    dbexp = {}
    dbexp['media'] = exceldb.parse('media')
    dbexp['PM1'] = exceldb.parse('PM1')
    dbexp['PM2A'] = exceldb.parse('PM2A')
    dbexp['PM3B'] = exceldb.parse('PM3B')
    dbexp['PM4A'] = exceldb.parse('PM4A')
    dbexp['MWF'] = exceldb.parse('MWF')
    dbexp['DNA'] = exceldb.parse('DNA')
    dbexp['RNA'] = exceldb.parse('RNA')
    dbexp['PROTS'] = exceldb.parse('PROTS')
    dbexp['LIPIDS_PL'] = exceldb.parse('LIPIDS_PL')
    dbexp['LIPIDS_FA'] = exceldb.parse('LIPIDS_FA')
    dbexp['authors'] = exceldb.parse('authors')
    
    
    # format tables (media):
    # assign substrates as index
    dbexp['media'].index = dbexp['media'].iloc[:, 1]
    # remove first 2 useless column (empty & substrates)
    dbexp['media'] = dbexp['media'].iloc[:, 2:]
    
    
    # format tables (Biolog(R)):
    for sheet in ['PM1', 'PM2A', 'PM3B', 'PM4A']:
        # assign wells as index
        dbexp[sheet].index = dbexp[sheet].iloc[:, 2]
        # remove first 3 useless columns
        dbexp[sheet] = dbexp[sheet].iloc[:, 3:]
        
        
    # format tables (biomass):
    dbexp['MWF'].index = dbexp['MWF'].iloc[:, 0]   # assign index
    dbexp['MWF'] = dbexp['MWF'].iloc[:, 1:]        # remove meaningless columns
    #
    dbexp['DNA'].index = dbexp['DNA'].iloc[:, 0]   # assign index
    dbexp['DNA'] = dbexp['DNA'].iloc[:, 1:]        # remove meaningless columns
    #
    dbexp['RNA'].index = dbexp['RNA'].iloc[:, 0]   # assign index
    dbexp['RNA'] = dbexp['RNA'].iloc[:, 1:]        # remove meaningless columns
    # 
    dbexp['PROTS'].index = dbexp['PROTS'].iloc[:, 1]   # assign index
    dbexp['PROTS'] = dbexp['PROTS'].iloc[:, 2:]        # remove meaningless columns
    #
    dbexp['LIPIDS_PL'].index = dbexp['LIPIDS_PL'].iloc[:, 1]   # assign index
    dbexp['LIPIDS_PL'] = dbexp['LIPIDS_PL'].iloc[:, 2:]        # remove meaningless columns
    #
    dbexp['LIPIDS_FA'].index = dbexp['LIPIDS_FA'].iloc[:, 1]   # assign index
    dbexp['LIPIDS_FA'] = dbexp['LIPIDS_FA'].iloc[:, 2:]        # remove meaningless columns
    
    
    return dbexp



def get_eschermap(logger, map_id):
    
    
    dict_escher_maps = {
        'gr_other_reactions': '1un4Nqpc7l-U3k8iX67osIqM_I6AntWDy',
        'gr_sinks_demands':   '1lKS2_kXhdBWTFY_vsABRBfPUH3SidgQK',
        'gr_unsaturates_w7':  '1jh5quSsiqJ6PecvlWRRp00s9Uj-96SBK',
        'gr_transport':    '180QXr_e99GmYTUFtmV-Btw8-O7C7VeRO',
        'map00010': '1mTMwrnNd1n4j7SHAwJ86EtOtIt9NOqp6',
        'map00020': '1J7bHRZv1OU6E8JkpW6JxThWp-p0sqS-N',
        'map00030': '121nngh-p29TQrvlDeVOREhVaOZ0Qe94H',
        'map00040': '17e-e4z5pYrLG0sJRhY1lll183MAUmfeC',
        'map00051': '1A6lpAuilGP7VvfLh_9PsqcE23YM0_RZA',
        'map00052': '1ZDrLZIsCxK2-2rDuYbZck_ls5g-VTYAS',
        'map00053': '1eluZkBAA3_SSP625refRJQLAp0lSGJSq',
        'map00061': '1RDgv4yLkpYh9p2Zy_OPDc7kmJNATHpJY',
        'map00071': '1ieltgCeNZT11cTHQ_uvWJVtfrjZ8O-yB',
        'map00100': '1a7WAA3y9J8gQmwuM7nDfmPABxi5M3IGU',
        'map00130': '1OXvBIbZzz4vSgrVpfXeQsxg74N5tqSNE',
        'map00190': '1j0SQYt5fNMCvKI3GFc1cOU0YGDyWidS5',
        'map00195': '1ceRpKB3JuxqHVrAVRVADX9sjcLPrwsoa',
        'map00220': '1ntN8R9NiG8kNjUntPqziIblhxoZgSR7N',
        'map00230': '1MVWZQs4V6jBk6kYv4kPait5SoBT7ZRmA',
        'map00240': '1-n8jzvfapLDGEvCF_jmVMhbBVy7UHf-z',
        'map00250': '1qh0dk4-bvml3FVLb5Qbw--GM0t4r-NwX',
        'map00260': '18l-dMc2a_uEgeSY3RcTQdScAIkvstpQo',
        'map00270': '1TGKhD3rnPgbPzL_NPR0NpO8CkWU4mTFE',
        'map00280': '1HSP6UibDxw5KaE0Q7LZR09OYvt8ie50R',
        'map00290': '1eObr-DGu1FSUZC0wh18UmDfgKbdpc4ez',
        'map00300': '1fgK9prq7Z-xskFtKSsp_nBW_avBTeKe3',
        'map00310': '1lKxkgnzXHdPZhT7QJN7Ohf7UMJix74Sl',
        'map00330': '1R-4vMiHQNyyZkpID0DgfunPCuVGhTz5g',
        'map00340': '16g1_a5aDs04ZrMNrEJCc5CdpgFcJGiDZ',
        'map00350': '1kkbmpmQY3f9zqy2GNdZKPd9HOz6MrnGc',
        'map00360': '1BC4IeVM6Px2bWleGmcX-h109RI-9KvhC',
        'map00380': '1ZfEK2U87gW77y1sosDTHlavJ66PLRgRY',
        'map00400': '1PKmNTpnfUaydtLQvGrJtP8LH7tj1Ka-Z',
        'map00450': '106flHuSeJID56rhYeJ5zJgDh8owfxW2K',
        'map00460': '1QBPL7deHN998Maj25LpVrrEB0l6_y4Q9',
        'map00470': '1u67PtRrS2xy8clSLt2daxiwO1j0wScRL',
        'map00480': '12p9hrG_xw-XigK4euy4-EDH8JH1t8U4c',
        'map00500': '1erMsLa2zcZUxizPiALZN4GmuaZSpmElF', 
        'map00520': '1K9mU6M99_hFeOc8x_rYDpWPpVO-6NCN3',
        'map00541': '1CDSQ8jqaSgdxAqMUIU6DsZnZXjXj7fe9', 
        'map00543': '1MkO45ap63_7ViJ-i8KtoEDl9q5ueXfJM', 
        'map00550': '1HCvMcqThZqTZXa2ErL3ZpcJ86gBw2Sh3', 
        'map00552': '1GcRd4ADgLVRg-RuI-6CklkNao4EgVL5s',
        'map00561': '17_hAqfz89xBX3f_eUkGefEFiqZ0xS-hL',
        'map00562': '1HxBd0LbZaqbrnjhpxxK7lEQGlW7HN3bU',
        'map00564': '1XI3tcJgJbBDkDj6DVBAuzZ-Ok6uK_TfB', 
        'map00620': '1e9lGVCYs3nt-LgTPY55vLeeQtWk4Zpna',
        'map00630': '1LXW-Htoh25wAWXdrWu6wTnegxuK9BNy5', 
        'map00640': '1kjummzfu7lgy91QVZr3IV_coLFjU9nsS',
        'map00650': '1fBOBJzPpTmNIUnpsSeM3JxSUTqHVFJ00', 
        'map00660': '1N9HbppTMcFTWTfBQhI1bF_SxbWhkGlKe',
        'map00670': '12jolzJP2sOUnL1z8MPGJy4dr3Jz4K0y0',
        'map00680': '1wopxju_tgy37Lb5uO7xkcE5hiUgppzJ2', 
        'map00710': '1HF1-j4h76nPgq-x0foqNmPj9Icb3CJet',
        'map00720': '1v40fQu6ByNq7g2_qiZ9qucBXYJPeKvpK',  
        'map00730': '1Spryv2M2eiPXF55dZoNb1_nv_f0oxN1v', 
        'map00740': '1WJ6iydXKLb2s1K8_F8OCIIurDBbGNAfM',
        'map00750': '1Z_7Z4710P738MOQJFuExjz7Nsff0_EZk',
        'map00760': '1PKJs7sZ2xvdHQAdz_E4faFugaownqXxw',
        'map00770': '1nbbTwRtUF4vOxwMUSwcyU1K4ltgLNVbx',
        'map00780': '1HUvLt4_xK_pnGbqiz8UjvZyvaGIomAxf', 
        'map00790': '13r-w61f0zPsDnpUHqJQU_r8ZXvE-cxhx',
        'map00791': '1SX8WSG6zUOf144RhAT9QycDrjEskZi4w',
        'map00860': '18DqnA4rNfDp2pCNyvwRg4XoTS8KefFAc',
        'map00900': '1Xm9g8dTDJWJmQ7AY9PPybefcE6G3smTh',
        'map00906': '1jnMtXsHVXipy9ApialPNFQDW_GCgpKas',
        'map00910': '196D351gJ10416ZI6y1rJGLrmxCBiHLkI',
        'map00920': '1tnm0WGewYgINyvrj-A-iv2tO--bAKwxV',
        'map00930': '1UycN6OXFGR3g4Vwfz5zQXHmdaAJmqpox',
        'map00970': '1-bDiZJNxkM6JhcUpbI44O3kWvhTSYlGq',
    }
    
    
    
    # return None if not requested
    if map_id == None or map_id == '-': 
        return None
    
    
    # check the esistance of the map  
    if map_id not in dict_escher_maps.keys():
        logger.warning(f"No online folder is tracked for '{map_id}' yet. Please contact the developer to start tracking '{map_id}'.")
        return None    
    
    
    # object to be returned
    lastmap = dict()  
    
    
    # the temporary folder (/tmp/on-the-fly-code) will be deleted once exiting the with statement
    with tempfile.TemporaryDirectory() as tmp_dir:
        
        
        # get available versions without downloading:
        folder_id = dict_escher_maps[map_id]
        folder_url = f"https://drive.google.com/drive/folders/{folder_id}?usp=sharing"
        contents = gdown.download_folder(folder_url, output=tmp_dir, quiet=True, skip_download=True)

        # check empty folder
        if len(contents) == 0:
            logger.warning(f"Online folder for '{map_id}' seems empty. Please draw and upload '{map_id}-v1.json'.")
            return None
        
        # check crowded folder
        if len(contents) > 40:
            logger.warning(f"Online folder for '{map_id}' contains >40 versions. An error will be raised at 50 versions. Please free space by moving older versions into 'older/' now.")
        
        # create dict of available files:
        files = {i.path: i.id for i in contents}
        
        # check file name consistency
        map_ids = set([i.rsplit('-v',1)[0] for i in files.keys()])
        if len(map_ids) != 1:
            logger.error(f"Several different map names in online folder for '{map_id}'.")
            return 1
        
        # check concordance to mother folder
        if list(map_ids)[0] != map_id:
            logger.error(f"Online folder for '{map_id}' contains versions for another map.")
            return 1
        
        # get the last available version (natural order)
        last_version = max([int(i.rsplit('-v',1)[-1].replace('.json', '')) for i in files.keys()])
        last_file_name = list(files.keys())[0].rsplit('-v',1)[0] + f"-v{last_version}.json"
        last_file_id = files[last_file_name]
        lastmap['filename'] = last_file_name
        
        # download last version:
        try: pathfile_tmpfolder = gdown.download(id=last_file_id, output=f"{tmp_dir}/{last_file_name}", quiet=True)
        except: 
            logger.error(f"Downloading of last-version for '{map_id}'. Retry. If persists, please contact the developer.")
            return 1
        
        # load json
        with open(pathfile_tmpfolder, 'r') as file:
            json_data = json.load(file)
            lastmap['json'] = json_data

        
    return lastmap
        
    
    
def get_databases(logger, map_id): 
    

    # define a function to fill the dict
    def run_with_result(func, logger, results_dict, key, *extra_args):
        result = func(logger, *extra_args)
        results_dict[key] = result
        
    
    # start threads
    results_dict = dict()
    t1 = threading.Thread(target=run_with_result, args=(
        get_dbuni, logger, results_dict, 'dbuni'))
    t2 = threading.Thread(target=run_with_result, args=(
        get_dbexp, logger, results_dict, 'dbexp'))
    t3 = threading.Thread(target=run_with_result, args=(
        get_eschermap, logger, results_dict, 'eschermap', map_id))

    
    # wait for the longest download:
    t1.start()
    t2.start()
    t3.start()
    slw = SimpleLoadingWheel(msg="Please wait... ")
    while t1.is_alive() or t2.is_alive() or t3.is_alive():
        slw.proceed()
    slw.clear()
    
    
    # check if errors where raised:
    if type(results_dict['dbuni'])==int:
        return 1
    if type(results_dict['dbexp'])==int:
        return 1
    if type(results_dict['eschermap'])==int:
        return 1
    
    
    return (results_dict['dbuni'], results_dict['dbexp'], results_dict['eschermap'])



def format_expansion(logger, eggnog):
    
    
    # linux/macos usually perform argument axpansion befor passing the parameter to python.
    if type(eggnog) == list: # already expanded by the terminal
        if len(eggnog)==1 and '*' in eggnog[0]:
            original_eggnog = eggnog[0]
            eggnog = glob.glob(eggnog[0])  # glob will append only existing files to the list
            if eggnog == []:
                logger.info(f"No file matching '{original_eggnog}'.")
    
    
    elif type(eggnog) == str:  # in the terminal, it can be specified by using single quotes
        original_eggnog = False
        if eggnog != '-': # user wanted to specify something
            original_eggnog = eggnog
        eggnog = glob.glob(eggnog)  # glob will append only existing files to the list
        if original_eggnog and eggnog == []:
            logger.info(f"No file matching '{original_eggnog}'.")
            
            
    if eggnog == [] or eggnog == ['-']:
        eggnog = '-'   # return always a list except for this case
        
        
    return eggnog
    


def check_taxon(logger, taxon, idcollection_dict):
    
    
    # verify presence of needed assets
    if 'ko_to_taxa' not in idcollection_dict.keys():
        logger.error(f"Asset 'ko_to_taxa' not found in 'gsrap.maps'. Please update 'gsrap.maps' with 'gsrap getmaps'.")
        return 1
    
    
    # extract level and name
    try: level, name = taxon.split(':')
    except: 
        logger.error(f"Provided --taxon is not well formatted: '{taxon}'.")
        return 1
    
    
    # compute available levels and check
    avail_levels = set(['kingdom', 'phylum'])            
    if level not in avail_levels:
        logger.error(f"Provided level is not acceptable: '{level}' (see --taxon). Acceptable levels are {avail_levels}.")
        return 1
    
    
    # compute available taxa at input level
    avail_taxa_at_level = set()
    ko_to_taxa = idcollection_dict['ko_to_taxa']
    for ko in ko_to_taxa.keys():
        for taxon_name in ko_to_taxa[ko][level]:
            avail_taxa_at_level.add(taxon_name)
    if name not in avail_taxa_at_level:
        logger.error(f"Provided taxon name is not acceptable: '{name}' (see --taxon). Acceptable taxon names for level '{level}' are {avail_taxa_at_level}.")
        return 1
    
    
    return 0
