import os
import contextlib
import importlib.metadata 



import memote




def get_memote_results_dict(logger, model):
    
    
    logger.info(f"Running selected modules of MEMOTE v{importlib.metadata.metadata('memote')['Version']}...")


    # launch memote (only relevant modules)        
    with open(os.devnull, 'w') as devnull:
        with contextlib.redirect_stdout(devnull), contextlib.redirect_stderr(devnull):
            try: memote_report = memote.suite.api.test_model(model, exclusive=[
                'test_annotation', 
                'test_sbo',
                'test_stoichiometric_consistency',
                'test_reaction_mass_balance',
                'test_reaction_charge_balance',
                'test_find_disconnected',
                'test_find_reactions_unbounded_flux_default_condition'], results=True)
            except ValueError: memote_report = None
            

    # parse memote's results
    results_dict = {}
    results_dict['version'] = importlib.metadata.version("memote")
    test_results = dict(memote_report[1])['tests']
    sections = {
        'consistency': [
            ('test_stoichiometric_consistency', 3),
            ('test_reaction_mass_balance', 1),
            ('test_reaction_charge_balance', 1),
            ('test_find_disconnected', 1),
            ('test_find_reactions_unbounded_flux_default_condition', 1)
        ],
        'annotation_M': [
            ('test_metabolite_annotation_presence', 1),
            ('test_metabolite_annotation_overview', 1),
            ('test_metabolite_annotation_wrong_ids', 1),
            ('test_metabolite_id_namespace_consistency', 1),
        ],
        'annotation_R': [
            ('test_reaction_annotation_presence', 1),
            ('test_reaction_annotation_overview', 1),
            ('test_reaction_annotation_wrong_ids', 1),
            ('test_reaction_id_namespace_consistency', 1),
        ],
        'annotation_G': [
            ('test_gene_product_annotation_presence', 1),
            ('test_gene_product_annotation_overview', 1),
            ('test_gene_product_annotation_wrong_ids', 1),
        ],
        'annotation_SBO': [
            ('test_metabolite_sbo_presence', 1),
            ('test_metabolite_specific_sbo_presence', 1),
            ('test_reaction_sbo_presence', 1),
            ('test_metabolic_reaction_specific_sbo_presence', 1),
            ('test_transport_reaction_specific_sbo_presence', 1),
            ('test_exchange_specific_sbo_presence', 1),
            ('test_demand_specific_sbo_presence', 1),
            ('test_sink_specific_sbo_presence', 1),
            ('test_gene_sbo_presence', 1),
            ('test_gene_specific_sbo_presence', 1),
            ('test_biomass_specific_sbo_presence', 1),
        ],
    }
    section_multipliers = {
        'consistency': 3,
        'annotation_M': 1,
        'annotation_R': 1,
        'annotation_G': 1,
        'annotation_SBO': 2,
    }
    
    
    numerator_total = 0
    denominator_total = 0
    for section, metrics in sections.items(): 
        numerator = 0
        denominator = 0
        results_dict[section] = {}
        
        
        # iterate metrics of this section: 
        for metric, metric_multiplier in metrics:
            metric_raw = test_results[metric]['metric']
            
            
            # no subcategories here: 
            if type(metric_raw) == float: 
                metric_percentage = ((1- metric_raw ) *100)
                numerator = numerator + (metric_percentage * metric_multiplier)
                denominator = denominator + metric_multiplier
                results_dict[section][metric] = round(metric_percentage, 1)
                                
            
            # there are subcategories (like in the case of M/R/G/SBO annots)
            else:   
                results_dict[section][metric] = {}
                for key, value in metric_raw.items():
                    n_subcategories = len(metric_raw)
                    multiplier_corrected = metric_multiplier / n_subcategories
                    metric_percentage = ((1- value ) *100)
                    numerator = numerator + (metric_percentage * multiplier_corrected)
                    denominator = denominator + multiplier_corrected
                    results_dict[section][metric][key] = round(metric_percentage, 1)
                    
                    
        # compute the subtotal:
        sub_total = numerator / denominator
        results_dict[section]['sub_total'] = int(round(sub_total, 0))
        
        
        # compute the total:
        denominator_total = denominator_total + section_multipliers[section] *denominator
        numerator_total = numerator_total + section_multipliers[section] *numerator 
    total = numerator_total / denominator_total
    results_dict['total'] = int(round(total, 0))


    logger.info(f"Done! MEMOTE Total Score: {results_dict['total']}%.")
    
    
    return results_dict