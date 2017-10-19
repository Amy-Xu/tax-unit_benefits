import sys
import pandas as pd


def read_files():
    weights = pd.read_csv('/Users/Amy/Downloads/cps_weights.csv')
    cps_income = pd.read_csv('/Users/Amy/Downloads/cps.csv')[['e00200']]
    assert len(cps_income) == len(weights)

    cps_benefit = pd.read_csv('cps_benefits.csv')
    assert len(cps_benefit) == len(cps_income)
    
    cps = cps_benefit.join(cps_income)
    cps = cps.join(weights)

    cps = cps.sort_values(by='e00200')

def create_decile_dist(cps):
    cps['WT2015_cumsum'] = cps.WT2015.cumsum()
    cps['WT2015_decile'] = np.ceil(cps.WT2015_cumsum/(max(cps.WT2015_cumsum)/10))
    
    programs = ['ss', 'ssi', 'medicaid', 'medicare', 'vb', 'snap']
    benefits_vars = [x + '_benefits_2015' for x in programs]
    p_vars = [x + '_recipients_2015' for x in programs]
    
    
    decile2015 = pd.DataFrame(np.linspace(1,10, num=10), columns=['2015_decile'])
    delta = 1e06

    for i in range(6):

        # create weighted benefit
        cps[benefits_vars[i] + '_weighted'] = cps[benefits_vars[i]] * cps['WT2015']

        # temporary variable for weighted participation
        cps['dummy'] = np.where(cps[p_vars[i]]!=0, cps['WT2015'], 0)
        
        # calculate total benefits, participation (# tax units), and average per decile
        bp = cps[[benefits_vars[i] + '_weighted', 'dummy']].groupby(cps.WT2015_decile, as_index=False).sum()/1000000
        bp['average'] = bp[benefits_vars[i] + '_weighted']/(bp['dummy'] + delta)

        # rename and save
        bp.columns = [programs[i]+'_benefits', programs[i]+'_taxunits', programs[i]+'_average']
        decile2015 = pd.concat([table2015, bp], axis=1)
        
        decile2015.to_csv('decile2015_new.csv', float_format='%.2f', index=False)
        

def create_aggregates(cps):
    benefits = pd.DataFrame(programs, columns=['programs'])
    taxunits = pd.DataFrame(programs, columns=['programs'])
    participants = pd.DataFrame(programs, columns=['programs'])
    
    for year in range(2014, 2025):
        #benefits
        benefits_vars = [x + '_benefits_' + str(year) for x in programs]
        raw_benefits = cps.loc[:,benefits_vars]
        weighted_benefits = raw_benefits.multiply(cps['WT' + str(year)], axis='index')
        benefit_total = pd.DataFrame(weighted_benefits.sum()/1000000000)
        benefits[year] = benefit_total.values

        #participants
        p_vars = [x + '_recipients_'+ str(year) for x in programs]
        raw_participants = cps.loc[:, p_vars]
        weighted_par = raw_participants.multiply(cps['WT' + str(year)], axis='index')
        participant_total = pd.DataFrame(weighted_par.sum()/1000000)
        participants[year] = participant_total.values

        # tax units
        dummy = raw_participants.astype(bool)
        weighted_taxunits = dummy.multiply(cps['WT' + str(year)], axis='index')
        taxunit_total = pd.DataFrame(weighted_taxunits.sum()/1000000)
        taxunits[year] = taxunit_total.values

    pd.options.display.float_format = '{:,.1f}'.format
    with open('aggregates_new.txt', 'w') as file:
        file.write("Total benefits (billions)\n" + benefits.to_string(index=False) + '\n\n')
        file.write('Total participating tax units (millions)\n' + taxunits.to_string(index=False) + '\n\n')
        file.write('Total participants (millions)\n' + participants.to_string(index=False) + '\n\n')
        

def create_tabs(cps):
    tabs = {}
    
    # inline function to create single year program tabulation
    p_tab = lambda program: cps[program].value_counts()

    for program in programs:
        program_tab = {}
        for year in range(2014, 2025): 
            program_tab[year] = p_tab(program+"_recipients_"+str(year))
            program_tab = pd.DataFrame(program_tab)
        
        tabs[program] = program_tab

    with open('tabs_new.txt', 'w') as file:
        for key, dfs in tabs.iteritems():
            file.write(key + '\n')
            file.write(dfs.to_string() + '\n\n')


