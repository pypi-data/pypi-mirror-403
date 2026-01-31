import sys

import pandas as pnd
import cobra

from .repeating import check_author
from .repeating import check_rstring_arrow
from .repeating import check_gpr
from .repeating import add_reaction
from .repeating import get_curator_notes

from .manual import get_manual_sinks
from .manual import get_manual_demands


    
def introduce_metabolites(logger, db, model, idcollection_dict, kegg_compound_to_others, outdir, goodbefore, onlyauthor):
    goodbefore_reached = False
    
    
    logger.info("Parsing metabolites ('M' sheet)...")

    
    # check duplicated puremids:
    if len(set(db['M']['pure_mid'].to_list())) != len(db['M']): 
        pure_mids = db['M']['pure_mid'].to_list()
        duplicates = list(set([item for item in pure_mids if pure_mids.count(item) > 1]))
        logger.error(f"Sheet 'M' has duplicated metabolites: {duplicates}.")
        return 1
   
        
    # parse M (row by row):    
    db['M'] = db['M'].set_index('pure_mid', drop=True, verify_integrity=True)
    kc_ids_modeled = set()   # account for kc codes modeled
    cnt = 0  # counter for parsed records
    msg = '' # to be cleared
    for iteration, (pure_mid, row) in enumerate(db['M'].iterrows()):
        
        
        # skip empty lines!
        if type(pure_mid) != str: continue
        if pure_mid.strip() == '': continue
        if pure_mid == goodbefore:
            goodbefore_reached = True
            
            
        # manage goodbefore/onlyauthor
        if goodbefore != None and goodbefore_reached:
            if onlyauthor == None:
                logger.warning(f"Skipping metabolite '{pure_mid}' as requested with --goodbefore[0] '{goodbefore}'.")
                continue
        
        
        # parse and get curators
        response = check_author(logger, pure_mid, row, db, 'M')
        if type(response) == int: return 1
        else: authors = response
        
        
        # manage goodbefore/onlyauthor
        if goodbefore != None and goodbefore_reached:
            if onlyauthor != None and onlyauthor not in authors:
                authors_string = '; '.join(authors)
                logger.warning(f"Skipping metabolite '{pure_mid}' (authors '{authors_string}') as requested with --goodbefore[0] '{goodbefore}' and --onlyauthor '{onlyauthor}'.")
                continue
            
        
        # parse formula:
        if pnd.isna(row['formula']):
            logger.error(f"Metabolite '{pure_mid}' has missing formula: '{row['formula']}'.")
            return 1
  
        
        # parse charge: 
        if pnd.isna(row['charge']): 
            logger.error(f"Metabolite '{pure_mid}' has missing charge: '{row['charge']}'.")
            return 1
        
        
        # parse kc:
        if pnd.isna(row['kc']): 
            logger.error(f"Metabolite '{pure_mid}' has missing KEGG annotation (kc): '{row['kc']}'.")
            return 1
        kc_ids = row['kc'].split(';')
        kc_ids = [i.strip() for i in kc_ids]
        for kc_id in kc_ids:
            if kc_id == 'CXXXXX':  # not in KEGG; could be knowledge gap (e.g. methyl group acceptor in R10404)
                with open(f"{outdir}/logs/M.notkegg.txt", 'a') as f:
                    print(f"Metabolite '{pure_mid}' is not in KEGG ('{kc_id}')!", file=f)
                continue  
            #    
            # check if 'kc' codes are real:
            if kc_id not in idcollection_dict['kc']:
                logger.error(f"Metabolite '{pure_mid}' has invalid KEGG annotation (kc): '{kc_id}'.")
                return 1
            #
            # check if 'kc' was already used:
            if kc_id in kc_ids_modeled:
                logger.error(f"KEGG annotation (kc) '{kc_id}' used in metabolite '{pure_mid}' is duplicated.")
                return 1
            if kc_id != 'CXXXXX':
                kc_ids_modeled.add(kc_id)
            
            
        # check the existance of the inchikey
        if pnd.isna(row['inchikey']): 
            logger.error(f"Metabolite '{pure_mid}' has missing inchikey: '{row['inchikey']}'.")
            return 1
        
        # check inchikey format:
        if len(row['inchikey']) != 27 or row['inchikey'][14] != '-' or row['inchikey'][25] != '-':
            logger.error(f"Metabolite '{pure_mid}' has badly formatted inchikey: '{row['inchikey']}'.")
            return 1
        
        
        # check if this 'kc' is already in BiGG (rely on MNX)
        eqbiggids = set()
        for kc_id in kc_ids:
            if kc_id != 'CXXXXX':
                if kc_id in kegg_compound_to_others.keys():
                    for eqbiggid in kegg_compound_to_others[kc_id]['bigg.metabolite']:
                        eqbiggids.add(eqbiggid)
        if pure_mid not in eqbiggids and eqbiggids != set():
            with open(f"{outdir}/logs/M.inbigg.txt", 'a') as f:
                print(f"Metabolites '{'; '.join(kc_ids)}' already in BiGG as {eqbiggids} ({authors} gave '{pure_mid}').", file=f)        
        
        
        # add metabolite to model
        m = cobra.Metabolite(f'{pure_mid}_c')
        model.add_metabolites([m])
        m = model.metabolites.get_by_id(f'{pure_mid}_c')
        m.name = row['name'].strip()
        m.formula = row['formula']
        m.charge = row['charge']
        m.compartment='c'
        
        
        # write curators as annotations
        m.annotation['curator_codes'] = authors
        
        
        # add annotations to model (same order of Memote)
        ankeys = [
            'pubchem.compound', 'kegg.compound', 'seed.compound',
            'inchikey', 'inchi', 'chebi', 'hmdb', 'reactome',
            'metanetx.chemical', 'bigg.metabolite', 'biocyc',
        ]
        # initialize sets:
        for ankey in ankeys:
            if ankey == 'kegg.compound': m.annotation[ankey] = set(kc_ids) - set(['CXXXXX'])
            else: m.annotation[ankey] = set()
        #    
        # populate sets:
        for kc_id in kc_ids:
            if kc_id != 'CXXXXX':
                if kc_id in kegg_compound_to_others.keys():
                    for ankey in ankeys:
                        m.annotation[ankey].update(kegg_compound_to_others[kc_id][ankey])
        #
        # save as list: 
        for ankey in ankeys:
            m.annotation[ankey] = list(m.annotation[ankey])
            
            
        # # force the manual-curated version of the inchikey
        if m.annotation['inchikey'] != [] and m.annotation['inchikey'] != [row['inchikey']]:
            with open(f"{outdir}/logs/M.diffinchi.txt", 'a') as f:
                print(f"Metabolite '{pure_mid}': manual-curated inchikey ({[row['inchikey']]}) is different from the one derived from MNX ({m.annotation['inchikey']}).", file=f)
        m.annotation['inchikey'] = [row['inchikey']]  
        #
        # remove inchikey if unknown:
        if m.annotation['inchikey'] == ['XXXXXXXXXXXXXX-XXXXXXXXXX-X']:
            m.annotation['inchikey'] = []
            
            
        # add SBO annotation
        m.annotation['sbo'] = ['SBO:0000247']  # generic metabolite
        
        
        # add curator_notes
        m.annotation['curator_notes'] = get_curator_notes(logger, row)
        
        
        # communicate progress:
        cnt += 1
        msg = f"Done {cnt}/{len(db['M'])}!"
        print(msg, file=sys.stderr, end='\r')
    print(''.join([' ' for i in range(len(msg))]), file=sys.stderr, end='\r')
   
        
    # check goodbefore reaching:
    if goodbefore != None and goodbefore_reached == False:
        logger.warning(f"Metabolite '{goodbefore}' never reached. Are you sure about your --goodbefore?")
                    
                    
    return model
    
    
    
def introduce_reactions(logger, db, model, idcollection_dict, kegg_reaction_to_others, outdir, goodbefore, onlyauthor): 
    goodbefore_reached = False
    
    
    logger.info("Parsing non-transport reactions ('R' sheet)...")
                    
    
    # check duplicated rids:
    if len(set(db['R']['rid'].to_list())) != len(db['R']): 
        rids = db['R']['rid'].to_list()
        duplicates = list(set([item for item in rids if rids.count(item) > 1]))
        logger.error(f"Sheet 'R' has duplicated reactions: {duplicates}.")
        return 1
    
        
    # parse R (row by row):
    db['R'] = db['R'].set_index('rid', drop=True, verify_integrity=True)
    cnt = 0  # counter for parsed records
    msg = '' # to be cleared
    for rid, row in db['R'].iterrows():
        
        
        # skip empty lines!
        if type(rid) != str: continue
        if rid.strip() == '': continue
        if rid == goodbefore:
            goodbefore_reached = True
        
        
        # manage goodbefore/onlyauthor
        if goodbefore != None and goodbefore_reached:
            if onlyauthor == None:
                logger.warning(f"Skipping reaction '{rid}' as requested with --goodbefore[1] '{goodbefore}'.")
                continue
        
        
        # parse and get curators
        response = check_author(logger, rid, row, db, 'R')
        if type(response) == int: return 1
        else: authors = response
                    
                    
        # manage goodbefore/onlyauthor
        if goodbefore != None and goodbefore_reached:
            if onlyauthor != None and onlyauthor not in authors:
                authors_string = '; '.join(authors)
                logger.warning(f"Skipping reaction '{rid}' (authors '{authors_string}') as requested with --goodbefore[1] '{goodbefore}' and --onlyauthor '{onlyauthor}'.")
                continue
        
        
        # parse reaction string
        response = check_rstring_arrow(logger, rid, row, 'R')
        if response == 1: return 1
        

        # parse 'kr':
        if pnd.isna(row['kr']): 
            logger.error(f"Reaction '{rid}' has missing KEGG annotation (kr): '{row['kr']}'.")
            return 1
        kr_ids = row['kr'].split(';')
        kr_ids = [i.strip() for i in kr_ids]
        for kr_id in kr_ids:
            if kr_id == 'RXXXXX':  # not in KEGG; could be knowledge gap 
                with open(f"{outdir}/logs/R.notkegg.txt", 'a') as f:
                    print(f"Reaction '{rid}' is not in KEGG ('{kr_id}')!", file=f)
                continue  
            #
            # check if 'kr' codes are real:
            if kr_id not in idcollection_dict['kr']:
                logger.error(f"Reaction '{rid}' has invalid KEGG annotation (kr): '{kr_id}'.")
                return 1
        
            
        # check GPR:
        response = check_gpr(logger, rid, row, kr_ids, idcollection_dict, 'R', outdir)
        if response == 1: return 1
    
    
        # check if this 'kr' is already in BiGG (rely on MNX)
        eqbiggids = set()
        for kr_id in kr_ids:
            if kr_id != 'RXXXXX':
                if kr_id in kegg_reaction_to_others.keys():
                    for eqbiggid in kegg_reaction_to_others[kr_id]['bigg.reaction']:
                        eqbiggids.add(eqbiggid)
        if rid not in eqbiggids and eqbiggids != set():
            with open(f"{outdir}/logs/R.inbigg.txt", 'a') as f:
                print(f"Reactions '{'; '.join(kr_ids)}' already in BiGG as {eqbiggids} ({authors} gave '{rid}').", file=f) 
        
        
        # add reaction to model
        response = add_reaction(logger, model, rid, authors, row, kr_ids, kegg_reaction_to_others, 'R', outdir)
        if response == 1: return 1
    
    
        # communicate progress:
        cnt += 1
        msg = f"Done {cnt}/{len(db['R'])}!"
        print(msg, file=sys.stderr, end='\r')
    print(''.join([' ' for i in range(len(msg))]), file=sys.stderr, end='\r')
               
    
    # check goodbefore reaching:
    if goodbefore != None and goodbefore_reached == False:
        logger.warning(f"Reaction '{goodbefore}' never reached. Are you sure about your --goodbefore?")
    
    
    return model
      
    
    
def introduce_transporters(logger, db, model, idcollection_dict, kegg_reaction_to_others, outdir, goodbefore, onlyauthor): 
    goodbefore_reached = False
    
    
    logger.info("Parsing transport reactions ('T' sheet)...")
    
    
    def clone_to_external(model, mid_c, mid_e):
        # given an existing '_c' M, create its '_e' equivalent
    
        m = cobra.Metabolite(f'{mid_e}')
        model.add_metabolites([m])
        
        m_c = model.metabolites.get_by_id(f'{mid_c}')
        m_e = model.metabolites.get_by_id(f'{mid_e}')
        m_e.compartment='e'
        
        m_e.name = m_c.name
        m_e.formula = m_c.formula
        m_e.charge = m_c.charge
        
        m_e.annotation = m_c.annotation   # transfer all annotations, including SBO!
            
    
    def add_exchange_reaction(model, mid_e):
        # given an existing '_e' M, create the corresponding EX_change reaction
        
        r = cobra.Reaction(f'EX_{mid_e}')
        model.add_reactions([r])
        r = model.reactions.get_by_id(f'EX_{mid_e}')
        
        r.name = f"Exchange for {model.metabolites.get_by_id(mid_e).name}"
        r.build_reaction_from_string(f'{mid_e} --> ')
        r.bounds = (0, 1000)
            
        # add SBO annotation
        r.annotation['sbo'] = ['SBO:0000627']  # exchange reaction    
        
    
    
    # get all already inserted metabolites and reactions
    mids_parsed = [m.id for m in model.metabolites]
    rids_parsed = [r.id for r in model.reactions]
    
    
    # parse T (row by row):
    db['T'] = db['T'].set_index('rid', drop=True, verify_integrity=True)
    cnt = 0  # counter for parsed records
    msg = '' # to be cleared
    for rid, row in db['T'].iterrows():
        
        
        # skip empty lines!
        if type(rid) != str: continue
        if rid.strip() == '': continue
        if rid == goodbefore:
            goodbefore_reached = True
            
            
        # avoid duplicates!
        if rid in rids_parsed:
            logger.error(f"Tranport '{rid}' has ID identical to previously added reaction!")
            return 1
            
            
        # manage goodbefore/onlyauthor
        if goodbefore != None and goodbefore_reached:
            if onlyauthor == None:
                logger.warning(f"Skipping transport '{rid}' as requested with --goodbefore[2] '{goodbefore}'.")
                continue
        
        
        # parse author
        response = check_author(logger, rid, row, db, 'T')
        if type(response) == int: return 1
        else: authors = response
                    
                    
        # manage goodbefore/onlyauthor
        if goodbefore != None and goodbefore_reached:
            if onlyauthor != None and onlyauthor not in authors:
                authors_string = '; '.join(authors)
                logger.warning(f"Skipping transport '{rid}' (authors '{authors_string}') as requested with --goodbefore[2] '{goodbefore}' and --onlyauthor '{onlyauthor}'.")
                continue
        
        
        # parse reaction string
        response = check_rstring_arrow(logger, rid, row, 'T')
        if response == 1: return 1
    
    
        # parse 'kr':
        if pnd.isna(row['kr']): 
            logger.error(f"Reaction '{rid}' has missing KEGG annotation (kr): '{row['kr']}'.")
            return 1
        if row['kr'] != '-':
            kr_ids = row['kr'].split(';')
            kr_ids = [i.strip() for i in kr_ids]
            for kr_id in kr_ids:
                #
                # check if 'kr' codes are real
                if kr_id not in idcollection_dict['kr']:
                    logger.error(f"Reaction '{rid}' has invalid KEGG annotation (kr): '{kr_id}'.")
                    return 1
        else: 
            # no 'kr' for the majority of transport reactions!
            kr_ids = []

            
        # check GPR:
        response = check_gpr(logger, rid, row, kr_ids, idcollection_dict, 'T', outdir)
        if response == 1: return 1
        
        
        # iterate the involved metabolites
        involved_mids = row['rstring'].split(' ')  # dirty (arrows, coefficints are included)
        for mid in involved_mids: 
            if mid.endswith('_e'):
                mid_e = mid
                mid_c = mid.rsplit('_', 1)[0] + '_c'
                #
                # the cytosolic counterpart must be already modeled:
                if mid_c not in mids_parsed:
                    logger.error(f"{rid}: the metabolite '{mid_c}', counterpart of '{mid_e}', was not previously modeled.")
                    return 1
                #
                # clone to add external metabolite to model
                if mid_e not in mids_parsed:
                    clone_to_external(model, mid_c, mid_e)
                    mids_parsed.append(mid_e)
                #    
                # add corresponding exchange reaction to model
                if f'EX_{mid_e}' not in rids_parsed:
                    add_exchange_reaction(model, mid_e)
                    rids_parsed.append(f'EX_{mid_e}')
                    
                    
        # check if this 'kr' is already in BiGG (rely on MNX)
        eqbiggids = set()
        for kr_id in kr_ids:
            if kr_id != '-':  # (was 'RXXXXX' for metabolic reactions)
                if kr_id in kegg_reaction_to_others.keys():
                    for eqbiggid in kegg_reaction_to_others[kr_id]['bigg.reaction']:
                        eqbiggids.add(eqbiggid)
        if rid not in eqbiggids and eqbiggids != set():
            with open(f"{outdir}/logs/T.inbigg.txt", 'a') as f:
                print(f"Reactions '{'; '.join(kr_ids)}' already in BiGG as {eqbiggids} ({authors} gave '{rid}').", file=f) 
                    
                    
        # add reaction to model
        response = add_reaction(logger, model, rid, authors, row, kr_ids, kegg_reaction_to_others, 'T', outdir)
        if response == 1: return 1
        rids_parsed.append(rid)   # update list of rids in model
        
        
        # communicate progress:
        cnt += 1
        msg = f"Done {cnt}/{len(db['T'])}!"
        print(msg, file=sys.stderr, end='\r')
    print(''.join([' ' for i in range(len(msg))]), file=sys.stderr, end='\r')
        
        
    # check goodbefore reaching:
    if goodbefore != None and goodbefore_reached == False:
        logger.warning(f"Transport '{goodbefore}' never reached. Are you sure about your --goodbefore?")
        
    
    return model



def introduce_sinks_demands(logger, model): 
    
    
    logger.debug("Introducing sinks and demands...")
    
    
    sinks = get_manual_sinks()
    demands = get_manual_demands()
    
    
    for puremid in sinks: 
        r = cobra.Reaction(f'sn_{puremid}_c')
        model.add_reactions([r])
        r = model.reactions.get_by_id(f'sn_{puremid}_c')
        r.name = f"Sink for {model.metabolites.get_by_id(f'{puremid}_c').name}"
        r.build_reaction_from_string(f'{puremid}_c <=> ')
        r.bounds = (-1000, 1000)
        
        # add SBO annotation
        r.annotation['sbo'] = ['SBO:0000632']  # sink reaction 
    
    
    for puremid in demands: 
        r = cobra.Reaction(f'dm_{puremid}_c')
        model.add_reactions([r])
        r = model.reactions.get_by_id(f'dm_{puremid}_c')
        r.name = f"Demand for {model.metabolites.get_by_id(f'{puremid}_c').name}"
        r.build_reaction_from_string(f'{puremid}_c --> ')
        r.bounds = (0, 1000)
        
        # add SBO annotation
        r.annotation['sbo'] = ['SBO:0000628']  # demand reaction 
    
    
    return model



        

    
