import warnings
import logging
import threading

import cobra

from .downloads import SimpleLoadingWheel



def print_json_tree(data, level=0, max_level=2):
    # explore contents of a json object
    
    if level > max_level:
        return
    indent = '  ' * level
    if isinstance(data, dict):
        for key, value in data.items():
            print(f"{indent}{key}")
            print_tree(value, level + 1, max_level)
    elif isinstance(data, list):
        for i, item in enumerate(data):
            print(f"{indent}[{i}]")
            print_tree(item, level + 1, max_level)
            
            
            
def subset_for_focus(universe, rids_in_group, outdir, focus):
            
    universe_focus = universe.copy()
    to_remove = [r for r in universe_focus.reactions if r.id not in rids_in_group]


    # trick to avoid the WARNING "cobra/core/group.py:147: UserWarning: need to pass in a list" 
    # triggered when trying to remove reactions that are included in groups. 
    with warnings.catch_warnings():  # temporarily suppress warnings for this block
        warnings.simplefilter("ignore")  # ignore all warnings
        cobra_logger = logging.getLogger("cobra.util.solver")
        old_level = cobra_logger.level
        cobra_logger.setLevel(logging.ERROR)   

        universe_focus.remove_reactions(to_remove, remove_orphans=True)

        # restore original behaviour: 
        cobra_logger.setLevel(old_level)  


    # save the subset for drawing in Escher!
    cobra.io.save_json_model(universe_focus, f'{outdir}/focus_{focus}.json')
            
            
        
def count_undrawn_rids_focus(logger, universe, lastmap, focus, outdir):
    
    
    # there could be no tracked folder / no versions for this group
    if lastmap == None:
        return
    
    
    # get modeled reads for this --focus:
    rids_in_group = set()
    try: gr = universe.groups.get_by_id(focus)
    except: 
        logger.warning(f"Group '{focus}' not found!")
        return 
    for r in gr.members:
        rids_in_group.add(r.id)


    # get rids on Escher: 
    drawn_rids = set()
    for key, value in lastmap['json'][1]['reactions'].items():
        drawn_rids.add(value['bigg_id'])

        
    # get remaining rids for this map:
    remainings = rids_in_group - drawn_rids
    remainings_krs = set()
    for rid in remainings: 
        r = universe.reactions.get_by_id(rid)
        if 'kegg.reaction' in r.annotation.keys():
            krs = r.annotation['kegg.reaction']
            for kr in krs: 
                remainings_krs.add(kr)
    
    
    if len(remainings) > 0:
        if focus != 'gr_transport':
            logger.warning(f"Current '{lastmap['filename']}' is {len(remainings)} reactions behind: {' '.join(list(remainings_krs))}.")
        else:
            logger.warning(f"Current '{lastmap['filename']}' is {len(remainings)} reactions behind.")  # usually no kegg codes for tranport reactions
        
        
        # subset the universe to ease the drawing: 
        next_version_filename = f"{focus}-v{(int(lastmap['filename'].rsplit('-v',1)[-1].replace('.json', ''))+1)}.json"
        logger.warning(f"Writing model '{outdir}/focus_{focus}.json' to ease the drawing of '{next_version_filename}'...")
        
        
        t1 = threading.Thread(target = subset_for_focus, args=(
            universe, rids_in_group, outdir, focus))
        t1.start()
        slw = SimpleLoadingWheel(msg="Please wait... ")
        while t1.is_alive():
            slw.proceed()
        slw.clear()
        
        
        logger.warning(f"'{outdir}/focus_{focus}.json' created!")
    else:
        logger.info(f"Current '{lastmap['filename']}' is 0 reactions behind. Thank you ♥")
        