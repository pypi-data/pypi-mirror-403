


def get_deprecated_kos():
    deprecated_kos = [
        'K11189',  # should be K02784
        'K07011',  # linked to lp_1215(cps3A) and lp_1216(cps3B) during 2018 and not replaced
        #'K24301',   # to be introduced in GPRs
    ]
    return deprecated_kos



def get_krs_to_exclude():
    return set([
        'R12328', 'R05190',  # general forms of fatty acid biosynthesis
        'R01347', 'R01348', 'R04121',  # general forms of fatty acid degradation
        'R11671',  # multi-step fatty acids reactions
        'R07860', 'R01317', 'R07064',  # aspecific fatty acid reactions
        'R11311', 'R11256', 'R11308', 'R08772', 'R08770',  # polymer reactions
        
        # inconclusive due to semplification
        'R12425', 
        
        # "incomplete reaction" / "unclear reaction"
        'R08414', 'R13037', 'R13034', 'R13036', 'R02825', 'R11178', 'R13325', 'R12855', 'R12856', 'R09809', 
        'R09808', 'R08035', 'R08034', 'R11470', 'R09360', 'R08139', 'R08318', 'R07859', 'R09361', 'R09349', 
        'R13149', 'R13066', 'R11467', 'R11255', 'R08986', 'R13156', 'R13074', 'R13150', 'R11302', 'R11388', 
        'R08341', 'R13147', 'R13155', 'R08339', 'R11466', 'R08272', 'R09348', 'R09362', 'R11107', 'R08340', 
        'R07940', 'R11120', 'R11245', 'R08269', 'R11131', 'R07943', 'R08342', 'R06766', 'R12584', 'R09852',
        'R08268', 'R11129', 'R06702', 'R08866', 'R12555', 'R08927', 'R08343', 'R13067', 'R13069', 'R13068',
        'R05670', 'R06694', 'R09851', 'R11465', 'R08928', 'R11389', 'R11464', 'R13087', 'R12586', 'R11304', 
        'R08984', 'R11254', 'R13165', 'R12884', 'R08865', 'R13151', 'R08132', 'R08929', 'R06701', 'R08345',
        'R11365', 'R11303', 'R06670', 'R11364', 'R09347', 'R08293', 'R11362', 'R03872', 'R06339', 'R10481', 
        'R10480', 'R13341', 'R06505', 'R06504', 'R06326', 'R06470', 'R06467', 'R06327', 'R06503', 'R09847',
        'R13479', 'R13447', 'R13478', 'R07510', 'R04546', 'R06468', 'R05624', 'R10706', 'R13454', 'R13556',
        'R13455', 'R12691', 
    ])



def get_rids_with_mancheck_gpr():
    rids_mancheck_gpr = [  # reactions with manually checked GPRs
        'SUCD1', 'ALKP', 'PFK_3', 'TCMPTS', 'PPA', 'APSR',
        'NADHPO', 'ACOD', '5DOAN', '5DRBK', '5DRBPI', '5DRBUPD',
        'FNPOR', 'THZPSN', 'PPTGP', 'ALATA_D2', 'XYLUR1'
    ]
    return rids_mancheck_gpr



def get_rids_with_mancheck_balancing():
    rids_mancheck_bal = [  # same reactions involving ATP can be reversible
        
        # SECTION "reversible both in KEGG and MetaCyc"
        'PGK', 'SUCOAS', 'ADK1', 'GK1', 'NNATr', 'CYTK1', 'ACKr',
        'DGK1', 'PPAKr', 'ATPSr', 'NDPK10', 'BUTKr',
        
        ### SECTION "reversible in KEGG but not in MetaCyc" ###
        'CYTK2',  # clearly reversible in KEGG but not in MetaCyc (RXN-7913)
        'DADK',  # clearly reversible in KEGG but not in MetaCyc (DEOXYADENYLATE-KINASE-RXN)
        'UMPK',  # clearly reversible in KEGG but not in MetaCyc (RXN-12002)
        'NDPK1',  # clearly reversible in KEGG but not in MetaCyc (GDPKIN-RXN)
        'NDPK2',  # clearly reversible in KEGG but not in MetaCyc (UDPKIN-RXN)  
        'NDPK3',  # clearly reversible in KEGG but not in MetaCyc (CDPKIN-RXN)
        'NDPK4',  # clearly reversible in KEGG but not in MetaCyc (DTDPKIN-RXN)
        'NDPK5',  # clearly reversible in KEGG but not in MetaCyc (DGDPKIN-RXN)
        'NDPK6',  # clearly reversible in KEGG but not in MetaCyc (DUDPKIN-RXN)
        'NDPK7',  # clearly reversible in KEGG but not in MetaCyc (DCDPKIN-RXN)
        'NDPK8',  # clearly reversible in KEGG but not in MetaCyc (DADPKIN-RXN)
        'NDPK9',  # clearly reversible in KEGG but not in MetaCyc (RXN-14120) 
        
        ### SECTION "missing reversibility info" ###
        'LPHERA',  
    ]
    return rids_mancheck_bal



def get_manual_sinks():
    
    return ['apoACP', 'aponit', 'apocarb', 'thioca', 'THI5p_b', 'cyE', 'meanfa']



def get_manual_demands():
    
    return ['scp', 'amob', 'dialurate', 'THI5p_a', 'partmass' ]



def get_custom_groups():
    
    
    return {
        'gr_ptdSTA': ['UAMAGLL', 'UMNS', 'UPPNAPT', 'UAGPT2', 'UAGPGAL', 'UAGPN6GT', 'UAAGGTLGAGT', 'UAAGGTLG3AGT', 'PPTGP'],
        'gr_ptdSTR': ['UAMAGLL', 'UMNS', 'UPPNAPT', 'UAGPT2', 'PPGAAE1', 'PPGAAE2', 'PPTGP2'],
        'gr_ptdDAP': ['UGMDL', 'UGMDDS', 'UGMDDPT', 'UAGPT3', 'PPTGP3'],
        'gr_HemeO': ['HEMEOS'],
        'gr_WTA1': ['ACGAMT', 'UNDBD', 'WTAGPT', 'WTAGPP', 'WTAUGLCT2', 'WTAALAT3', 'WTAPL3'],
        'gr_WTA2': ['ACGAMT', 'UNDBD', 'WTAGPT', 'WTARBT2', 'WTARPP2', 'WTAUGLCT', 'WTAALAT2', 'WTAPL2'],
        'gr_WTA3': ['ACGAMT', 'UNDBD', 'WTAGPT', 'WTAGPT2', 'WTARPP', 'WTAGLCNACT', 'WTAALAT', 'WTAPL'],
        'gr_WTA4': ['UNACGYL', 'UADDTRS', 'AATGALT', 'TAA13GLT', 'TAARPTR', 'TAANGTR', 'TAANGTR2', 'LPSCHPT', 'TACCHPT', 'T4WTAPOL', 'WTAPL4', 'WTAT4ALAT'], # type-IV WTA
        'gr_LTA1': ['UGDIAT', 'UGLDIAT', 'GGGDAGF2', 'LIPOPO2', 'LTANACT', 'LTAALAT2'],
        'gr_LTA2': ['UGDIAT', 'UGADIAT', 'GGGDAGF', 'LIPOPO', 'LTAGAT', 'LTAALAT'],
        'gr_LTA3': ['UNACGYL', 'UADDTRS', 'AATGALT', 'TAA13GLT', 'TAARPTR', 'TAANGTR', 'TAANGTR2', 'LPSCHPT', 'TACCHPT', 'T4WTAPOL', 'T4LTAL', 'LTAT4ALAT'], # type-IV LTA
        'gr_br': ['LYEH1', 'HIPCD1', 'LYEH2', 'HIPCD2', 'BHBRH1', 'BHBRH2'],
        'gr_PHA1': ['ACACT1r', 'AACOAR_syn', 'PHBS_syn_1', 'PHBDEP_1'],    # PHA from glycolyis
        'gr_epsLAB': ['PGTLAB', 'GTSTLAB', 'EPSPOLAB'],
    }