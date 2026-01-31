import os
import pickle
from importlib import resources
import shutil


import cobra
import gempipe


from ..commons import force_id_on_sbml
from ..commons import log_metrics
from ..commons import log_unbalances
from ..commons import get_databases
from ..commons import introduce_universal_biomass
from ..commons import write_excel_model
from ..commons import show_contributions
from ..commons import adjust_biomass_precursors
from ..commons import count_undrawn_rids_focus

from ..commons import format_expansion
from ..commons import check_taxon
from ..commons import download_keggorg
from ..commons import initialize_model
from ..commons import get_memote_results_dict


from .introduce import introduce_metabolites
from .introduce import introduce_reactions
from .introduce import introduce_transporters
from .introduce import introduce_sinks_demands

from .annotation import translate_annotate_genes
from .annotation import set_up_groups

from .completeness import check_completeness

from ..runsims.simplegrowth import grow_on_media
from ..runsims.precursors import precursors_on_media
from ..runsims.biosynth import biosynthesis_on_media

from ..mkmodel.polishing import remove_disconnected

from .cycles import verify_egc_all




def main(args, logger):
    
    
    
    ###### PRE-PARSING
    
    # adjust out folder path                      
    while args.outdir.endswith('/'):              
        args.outdir = args.outdir[:-1]
    os.makedirs(f'{args.outdir}/', exist_ok=True)
    
    
    # prepare empty logs folder
    shutil.rmtree(f'{args.outdir}/logs', ignore_errors=True)
    os.makedirs(f'{args.outdir}/logs', exist_ok=True)
    
    
    # check compatibility of input parameters
    if args.progress==False and args.module==True: 
        logger.error(f"You cannot ask --module without --progress (see --help).")
        return 1
    if args.progress==False and args.focus!='-':
        logger.error(f"You cannot ask --focus without --progress (see --help).")
        return 1
    
    
    # check 'goodbefore' and 'onlyauthor' params
    if args.goodbefore == '-' and args.onlyauthor != '-':
        logger.error(f"--onlyauthor must be used in conjunction with --goodbefore.")
        return 1
    if   args.goodbefore == '-': args.goodbefore = [None, None, None]
    elif len(args.goodbefore.split('-')) != 3: 
        logger.error(f"Invalid syntax detected for --goodbefore.")
        return 1
    else:
        args.goodbefore = args.goodbefore.split('-')
        if args.goodbefore[0] == 'None': args.goodbefore[0] = None
        if args.goodbefore[1] == 'None': args.goodbefore[1] = None
        if args.goodbefore[2] == 'None': args.goodbefore[2] = None
    if args.onlyauthor == '-': args.onlyauthor = None
    
    
    # check and extract the required 'gsrap.maps' file
    if os.path.exists(f'{args.inmaps}') == False:
        logger.error(f"File 'gsrap.maps' not found at {args.inmaps}.")
        return 1
    try: 
        with open(f'{args.inmaps}', 'rb') as f:
            inmaps = pickle.load(f)  
    except: 
        logger.error(f"Provided file {args.inmaps} has an incorrect format.")
        return 1
    idcollection_dict = inmaps['idcollection_dict']
    summary_dict = inmaps['summary_dict']
    
    
    # load internal resources
    with resources.path("gsrap.assets", f"kegg_compound_to_others.pickle") as asset_path: 
        with open(asset_path, 'rb') as handle:
            kegg_compound_to_others = pickle.load(handle)
    with resources.path("gsrap.assets", f"kegg_reaction_to_others.pickle") as asset_path: 
        with open(asset_path, 'rb') as handle:
            kegg_reaction_to_others = pickle.load(handle) 
            
                        
    # format the --eggnog param
    args.eggnog = format_expansion(logger, args.eggnog)  # now 'args.eggnog' could still be '-'
    
    
    # check the --taxon param
    if args.taxon != '-':
        response = check_taxon(logger, args.taxon, idcollection_dict)
        if response == 1: return 1
    
    
    # get the kegg organism if requested
    if args.keggorg != '-':
        response = download_keggorg(logger, args.keggorg, args.outdir)
        if response == 1: return 1
    
    
    # download dbuni, dbexp and lastmap:
    logger.info("Downloading updated gsrap assets...")
    response = get_databases(logger, map_id=args.focus)
    if type(response)==int: return 1
    else: dbuni, dbexp, lastmap = response
    
    
    
    ###### PARSING

    # show simple statistics of contributions
    response = show_contributions(logger, dbuni, args.goodbefore)
    if response == 1: return 1
    
    
    # create the model
    universe = cobra.Model('universe')   
    
    
    # introduce M 
    universe = introduce_metabolites(logger, dbuni, universe, idcollection_dict, kegg_compound_to_others, args.outdir, args.goodbefore[0], args.onlyauthor)
    if type(universe)==int: return 1


    # introduce R
    universe = introduce_reactions(logger, dbuni, universe, idcollection_dict, kegg_reaction_to_others, args.outdir, args.goodbefore[1], args.onlyauthor)
    if type(universe)==int: return 1


    # introduce T
    universe = introduce_transporters(logger, dbuni, universe, idcollection_dict, kegg_reaction_to_others, args.outdir, args.goodbefore[2], args.onlyauthor)
    if type(universe)==int: return 1


    # introduce sinks / demands (exchanges where included during T)
    universe = introduce_sinks_demands(logger, universe)
    if type(universe)==int: return 1


    # introducce universal biomass
    universe = introduce_universal_biomass(logger, dbexp, universe)
    if type(universe)==int: return 1


    # translate Gs to symbols and annotate them (EC, COG, GO, ...)
    universe = translate_annotate_genes(logger, universe, idcollection_dict)
    if type(universe)==int: return 1


    # introduce collections (groups of Rs as maps/modules)
    universe = set_up_groups(logger, universe, idcollection_dict)
    if type(universe)==int: return 1


    
    ###### POST-PARSING
    
    # log metrics
    log_metrics(logger, universe)
    
    
    # check absence of unbalancing above the threshold
    log_unbalances(logger, universe)

    
    # check universe completness
    df_C = check_completeness(logger, universe, args.progress, args.module, args.focus, args.taxon, args.eggnog, args.keggorg, idcollection_dict, summary_dict, args.outdir)
    if type(df_C)==int: return 1


    # remove disconnected metabolites
    if args.keepdisconn == False:
        universe = remove_disconnected(logger, universe)   # can be commented when using booster.py

    
    # avoid time-consuming activities
    if not args.justparse:
    
    
        # check erroneous EGCs
        verify_egc_all(logger, universe, args.outdir)

        
        # check growth on minmal media
        df_G = grow_on_media(logger, universe, dbexp, args.media, fva=False, universe_in_parsedb=True)
        if type(df_G)==int: return 1

    
        # check blocked biomass precursors
        cond_col_dict = adjust_biomass_precursors(logger, universe, universe, 1.0)
        df_E = precursors_on_media(logger, universe, universe, dbexp, args.media, cond_col_dict, args.precursors)
        if type(df_E)==int: return 1

    
        # check blocked metabolites / dead-ends
        df_S = biosynthesis_on_media(logger, universe, dbexp, args.media, args.biosynth)
        if type(df_S)==int: return 1


        # reset growth environment befor saving the model (changed during growth sims)
        gempipe.reset_growth_env(universe)

        
        # initialize model
        response = initialize_model(logger, universe, dbexp, args.initialize, args.media)
        if response==1: return 1


        # compute Memote metrics
        memote_results_dict = get_memote_results_dict(logger, universe)


    # write JSON 
    logger.info("Writing universal model...")
    cobra.io.save_json_model(universe, f'{args.outdir}/universe.json')
    logger.info(f"'{args.outdir}/universe.json' created!")
    
    
    # avoid time-consuming activities
    if not args.justparse:
        
        
        # write XML
        cobra.io.write_sbml_model(universe, f'{args.outdir}/universe.xml')   # groups are saved only to SBML 
        logger.info(f"'{args.outdir}/universe.xml' created!")
        force_id_on_sbml(f'{args.outdir}/universe.xml', 'universe')   # force introduction of the 'id=""' field
        
        
        # write XLSX
        sheets_dict = write_excel_model(universe, f'{args.outdir}/universe.parsedb.xlsx', args.nofigs, memote_results_dict, df_E, None, None, df_S, df_C)  
        logger.info(f"'{args.outdir}/universe.parsedb.xlsx' created!")

    
    # check if escher map is updated:
    if args.focus != '-':
        count_undrawn_rids_focus(logger, universe, lastmap, args.focus, args.outdir)
    
    
    return 0