#!/usr/bin/env python
"""
model_loader
============
Defines a registry of recognized model types and variants. Also defines methods
to quick-load requested models as needed for a phyddle analysis.

Authors:   Michael Landis and Ammon Thompson
Copyright: (c) 2022-2023, Michael Landis and Ammon Thompson
License:   MIT
"""

# standard libraries
import importlib
import pandas as pd
import numpy as np
import dendropy as dp
import re
import shutil
from itertools import combinations,chain
import json

NUM_DIGITS = 10

# model string names and class names
model_registry = []
model_registry_names = ['model_name', 'class_name',      'description' ] 
model_registry.append( ['geosse',     'GeosseModel',     'Geographic State-dependent Speciation Extinction [GeoSSE]'] )
model_registry.append( ['sir',        'SirModel',        'Susceptible-Infected-Recovered [SIR]'] )
model_registry.append( ['birthdeath', 'BirthDeathModel', 'Birth-Death [BD]'] )
model_registry = pd.DataFrame( model_registry, columns = model_registry_names)

def load(args):
    """
    Generates a Google-style docstring for the load function.
    
    Parameters:
        args (dict): A dictionary containing the arguments required for model loading.
    
    Returns:
        obj: An instance of the loaded model.
    """
    model_type = args['model_type']
    MyModelClass = get_model_class(model_type)
    return MyModelClass(args)

# convert model_name into class_name through registry
def get_model_class(model_type):
    """
    Returns the corresponding model class based on the given model_type.

    Parameters:
    - model_type (str): The type of the model to be retrieved.

    Returns:
    - MyModelClass: The class object of the corresponding model.
    """
    model_class_name = model_registry.class_name[ model_registry.model_name == model_type ].iat[0]
    MyModelModule = importlib.import_module('masterpy.models.'+model_class_name)
    #cls = getattr(import_module('my_module'), 'my_class') 
    MyModelClass = getattr(MyModelModule, model_class_name)
    return MyModelClass

# print
def make_model_registry_str():
    """
    Generates a Google-style docstring for the make_model_registry_str function.
    
    Returns:
        str: The formatted model registry string.
    """
    s = ''
    # header
    s += 'Type'.ljust(20, ' ') + 'Variant'.ljust(20, ' ') + 'Description'.ljust(40, ' ') + '\n'
    s += ''.ljust(60, '=') + '\n'
    # types
    for i in range(len(model_registry)): 
        model_i = model_registry.loc[i]
        model_name = model_i.model_name
        model_desc = model_i.description
        s += model_name.ljust(20, ' ') + '--'.ljust(20, ' ') + model_desc.ljust(40, ' ') + '\n'
        # variants per type
        model_class = model_i.class_name
        MyModelModule = importlib.import_module('models.'+model_class)
        #MyModelClass = getattr(MyModelModule, model_class)
        variant_registry = MyModelModule.variant_registry
        for j in range(len(variant_registry)):
            variant_j = variant_registry.loc[j]
            variant_name = variant_j.variant_name
            variant_desc = variant_j.description
            s += ''.ljust(20, ' ') + variant_name.ljust(20, ' ') + variant_desc.ljust(40, ' ') + '\n'
        s += '\n'

    return s


# model events
class Event:
    """
    Event objects define an event for a Poisson process with discrete-valued
    states, such as continuous-time Markov processes. Note, that
    phylogenetic birth-death models and SIR models fall into this class.
    The Event class was originally designed for use with chemical
    reaction simulations using the MASTER plugin in BEAST.
    """
    # initialize
    def __init__(self, idx, r=0.0, n=None, g=None, ix=None, jx=None, dim=None, predicate=None):
        """
        Create an Event object.

        Args:
            idx (dict): A dictionary containing the indices of the event.
            r (float): The rate of the event.
            n (str): The name of the event.
            g (str): The reaction group of the event.
            ix (list): The reaction quantities (reactants) before the event.
            jx (list): The reaction quantities (products) after the event.
        """
        self.i = -1
        self.j = -1
        self.k = -1
        self.idx = idx
        if 'i' in idx:
            self.i = idx['i']
        if 'j' in idx:
            self.j = idx['j']
        if 'k' in idx:
            self.k = idx['k']
        self.rate = r
        self.name = n
        self.group = g
        self.ix = ix
        self.jx = jx
        self.dim = dim
        self.predicate = predicate
        self.reaction = ' + '.join(ix) + ' -> ' + ' + '.join(jx)
        return
        
    # make print string
    def make_str(self):
        """
        Creates a string representation of the event.

        Returns:
            str: The string representation of the event.
        """
        s = 'Event({name},{group},{rate},{idx})'.format(name=self.name, group=self.group, rate=self.rate, idx=self.idx)        
        #s += ')'
        return s
    
    # representation string
    def __repr__(self):
        """
        Returns the representation of the event.

        Returns:
            str: The representation of the event.
        """
        return self.make_str()
    
    # print string
    def __str__(self):
        """
        Returns the string representation of the event.

        Returns:
            str: The string representation of the event.
        """
        return self.make_str()


# state space
# AMT 240402: Note SirModel doesn't use States. This might not work anymore. 
class States:
    """
    States objects define the state space that a model operates upon. Event
    objects define transition rates and patterns with respect to States. The
    central purpose of States is to manage different representations of
    individual states in the state space, e.g. as integers, strings, vectors.
    """
    def __init__(self, lbl2vec):
        """
        Create a States object.

        Args:
            lbl2vec (dict): A dictionary with labels (str) as keys and vectors
                            of states (int[]) as values.
        """
        # state space dictionary (input)
        self.lbl2vec      = lbl2vec

        # basic info
        self.int2lbl        = list( lbl2vec.keys() )
        self.int2vec        = list( lbl2vec.values() )
        self.int2int        = list( range(len(self.int2vec)) )
        self.int2set        = list( [ tuple([y for y,v in enumerate(x) if v == 1]) for x in self.int2vec ] )
        self.lbl_one        = list( set(''.join(self.int2lbl)) )
        self.num_char       = len( self.int2vec[0] )
        self.num_states     = len( self.lbl_one )

        # relational info
        self.lbl2int = {k:v for k,v in list(zip(self.int2lbl, self.int2int))}
        self.lbl2set = {k:v for k,v in list(zip(self.int2lbl, self.int2set))}
        self.lbl2vec = {k:v for k,v in list(zip(self.int2lbl, self.int2vec))}
        self.vec2int = {tuple(k):v for k,v in list(zip(self.int2vec, self.int2int))}
        self.vec2lbl = {tuple(k):v for k,v in list(zip(self.int2vec, self.int2lbl))}
        self.vec2set = {tuple(k):v for k,v in list(zip(self.int2vec, self.int2set))}
        self.set2vec = {tuple(k):v for k,v in list(zip(self.int2set, self.int2vec))}
        self.set2int = {tuple(k):v for k,v in list(zip(self.int2set, self.int2int))}
        self.set2lbl = {tuple(k):v for k,v in list(zip(self.int2set, self.int2lbl))}
        self.int2vecstr = [ ''.join([str(y) for y in x]) for x in self.int2vec ]
        self.vecstr2int = { v:i for i,v in enumerate(self.int2vecstr) }
       
        # done
        return

    def make_str(self):
        """
        Creates a string representation of the state space.

        Returns:
            str: The string representation of the state space.
        """
        # state space: {'A': [1, 0, 0], 'B': [0, 1, 0], 'C': [0, 0, 1], 'AB': [1, 1, 0], 'AC': [1, 0, 1], 'BC': [0, 1, 1], 'ABC': [1, 1, 1]}
        # string: Statespace(A,0,100;B,1,010;C,2,001;AB,3,110;AC,4,101;BC,5,011;ABC,6,111)
        s = 'Statespace('
        x = []
        for i in self.int2int:
            # each state in the space is reported as STRING,INT,VECTOR;
            x.append( self.int2lbl[i] + ',' + str(self.int2int[i]) + ',' + ''.join( str(x) for x in self.int2vec[i]) )
        s += ';'.join(x) + ')'
        return s

    # representation string
    def __repr__(self):
        """
        Returns the representation of the state space.

        Returns:
            str: The representation of the state space.
        """
        return self.make_str()

    # print string
    def __str__(self):
        """
        Returns the string representation of the state space.

        Returns:
            str: The string representation of the state space.
        """
        return self.make_str()
    

def get_xml_output_spec(stochastic = True, no_tree = False, 
                        newick_fn = None, nexus_fn = None, json_fn = None):
    if stochastic and not no_tree:
        xml_output_spec = '''
    <output spec='NewickOutput' collapseSingleChildNodes='true' fileName='{newick_fn}'/>
    <output spec='NexusOutput' fileName='{nexus_fn}'/>
    <output spec='JsonOutput' fileName='{json_fn}' />
                '''.format(newick_fn=newick_fn, nexus_fn=nexus_fn, json_fn=json_fn)
        
    else:
        xml_output_spec = '''
    <output spec='JsonOutput' fileName='{json_fn}' />
                '''.format(json_fn=json_fn)
        
    return xml_output_spec


def get_xml_run_spec(stochastic = True, no_tree = False, 
                     stop_time = 10, num_time_pts = 1000):
    if stochastic and not no_tree:
        xml_run_spec = '''
<run spec='InheritanceEnsemble'
    verbosity='1'
    nTraj='1'
    nSamples='{num_samples}'
    samplePopulationSizes='{sample_pop}'
    simulationTime='{stop_time}'
    maxConditionRejects='1'>'''.format(num_samples=num_time_pts,
                                       sample_pop='true',
                                       stop_time=stop_time)
    elif stochastic and no_tree:
        xml_run_spec = '''
<run spec='Trajectory'
    verbosity='0'
    nSamples='{num_samples}'
    simulationTime='{stop_time}'
    maxConditionRejects='1'>
    
<stepper spec='SALStepper' stepSize="0.01" />
            '''.format(num_samples=num_time_pts, stop_time=stop_time)
        
    else:
        xml_run_spec = '''
<run spec='Trajectory'
    verbosity='0'
    nSamples='{num_samples}'
    simulationTime='{stop_time}'
    maxConditionRejects='1'>
    
<stepper spec='RateEquationStepper' stepSize='0.01' iterations='5'/>
            '''.format(num_samples=num_time_pts, stop_time=stop_time)
        
    return xml_run_spec

def events2df(events):
    """
    Convert a list of Event objects to a pandas DataFrame.
    """
    df = pd.DataFrame({
        'name'      : [ e.name for e in events ],
        'group'     : [ e.group for e in events ], 
        # 'i'        : [ e.i for e in events ],
        # 'j'        : [ e.j for e in events ],
        # 'k'        : [ e.k for e in events ],
        'dim'       : [ e.dim for e in events ],
        'ix'        : [ ';'.join(e.ix) for e in events ],
        'jx'        : [ ';'.join(e.jx) for e in events ],
        'ijx'       : [ ';'.join(e.ix + e.jx) for e in events ],
        'reaction'  : [ e.reaction for e in events ],
        'predicate' : [ e.predicate if e.predicate is not None else '' for e in events  ],
        'rate'      : [ e.rate for e in events ]
    })
    return df

# def states2df(states):
#     """
#     Convert a States object to a pandas DataFrame.

#     This function takes a States object and converts it into a pandas DataFrame. The States object contains information about the state space, and the resulting DataFrame has columns 'lbl', 'int', 'set', and 'vec', representing the labels, integer representations, set representations, and vector representations of the states, respectively.

#     Args:
#         states (States): The States object to convert to a DataFrame.

#     Returns:
#         pandas.DataFrame: The resulting DataFrame with columns 'lbl', 'int', 'set', and 'vec'.
#     """
#     df = pd.DataFrame({
#         'lbl' : states.int2lbl,
#         'int' : states.int2int,
#         'set' : states.int2set,
#         'vec' : states.int2vec
#     })
#     return df

def sort_binary_vectors(binary_vectors):
    """
    Sorts a list of binary vectors.

    The binary vectors are sorted first based on the number of "on" bits, and then from left to right in terms of which bits are "on".

    Args:
        binary_vectors (List[List[int]]): The list of binary vectors to be sorted.

    Returns:
        List[List[int]]: The sorted list of binary vectors.
    """
    def count_ones(binary_vector):
        """
        Counts the number of "on" bits in a binary vector.

        Args:
            binary_vector (List[int]): The binary vector.

        Returns:
            int: The count of "on" bits.
        """
        return sum(binary_vector)

    sorted_vectors = sorted(binary_vectors, key=count_ones)

    for i in range(len(sorted_vectors)):
        for j in range(i+1, len(sorted_vectors)):
            if count_ones(sorted_vectors[j]) == count_ones(sorted_vectors[i]):
                for k in range(len(sorted_vectors[i])):
                    if sorted_vectors[i][k] != sorted_vectors[j][k]:
                        if sorted_vectors[j][k] > sorted_vectors[i][k]:
                            sorted_vectors[i], sorted_vectors[j] = sorted_vectors[j], sorted_vectors[i]
                        break

    return sorted_vectors

def int_to_one_hot(target, num_classes):
    one_hot = np.zeros(num_classes)
    one_hot[target] = 1
    return one_hot

def powerset(iterable):
    """
    Generates all possible subsets (powerset) of the given iterable.

    Args:
        iterable: An iterable object.

    Returns:
        generator: A generator that yields each subset.
    """
    s = list(iterable)  # Convert the iterable to a list
    return chain.from_iterable(combinations(s, r) for r in range(len(s) + 1))

def param_dict_to_str(params):
    """
    Convert parameter dictionary to two string representations.

    This function takes a parameter dictionary and converts it into two string representations. 
    The resulting strings includes the parameter names, indices, and values. 
    Each element of the dictionary is a list.
    The first representation is column-based, the second representation is row-based.

    Args:
        params (dict): The parameter dictionary.

    Returns:
        tuple: A tuple of two strings. First is a column of the values with names, 
        the second is as a row.
    """
    s1 = 'param,value\n'
    s2 = ''
    s3 = ''
    for k,v in params.items():
        for i,elem in np.ndenumerate(v):
            tensor_coords = k + '_' + '_'.join([str(x) for x in i])
            rate = np.round(elem, NUM_DIGITS)
            s1 += tensor_coords + "," + str(rate) + "\n"
            s2 += tensor_coords + ','
            s3 += str(rate) + ','
    labels_string = s2.rstrip(',') + '\n' + s3.rstrip(',') + '\n'
    return s1,labels_string


# def param_dict_to_str(params):
#     """
#     Convert parameter dictionary to two string representations.

#     This function takes a parameter dictionary and converts it into two string representations. 
#     The resulting strings includes the parameter names, indices, and values. 
#     The first representation is column-based, the second representation is row-based.

#     Args:
#         params (dict): The parameter dictionary.

#     Returns:
#         tuple: A tuple of two strings. The first string represents the parameter values with 
#         indices, and the second string represents the parameter names.
#     """
#     s1 = 'param,i,j,value\n'
#     s2 = ''
#     s3 = ''
#     for k,v in params.items():
#         for i,x in enumerate(v):
#             if len(v.shape) == 1:
#                 rate = np.round(x, NUM_DIGITS)
#                 s1 += '{k},{i},{i},{v}\n'.format(k=k,i=i,v=rate)
#                 s2 += '{k}_{i},'.format(k=k,i=i)
#                 s3 += str(rate) + ','
#             else:
#                 for j,y in enumerate(x):
#                     rate = np.round(y, NUM_DIGITS)
#                     s1 += '{k},{i},{j},{v}\n'.format(k=k,i=i,j=j,v=rate)
#                     s2 += '{k}_{i}_{j},'.format(k=k,i=i,j=j)
#                     s3 += str(rate) + ','

#     s4 = s2.rstrip(',') + '\n' + s3.rstrip(',') + '\n'
#     return s1,s4

def write_to_file(s, fn):
    """Writes a string to a file.

    Args:
        s (str): The string to write.
        fn (str): The file name or path to write the string to.

    Returns:
        None
    """
    f = open(fn, 'w')
    f.write(s)
    f.close()
    return

def get_popSize_at_t(json_dat, compartments, tpoi = 0):
    """ 
     Args:
    - json_dat (dict): A dictionary containing trajectory data, with keys 'trajectories', 't'.
    - tpoi (float/int): Time point of interest. 
        if tpoi is negative the time point is in the past, if positive it is in the future. 
        The present is considered time point 0.  

    Returns:
    - a dictionary containing the prevalence of each compartment at each location at this time point.
    """

    if json_dat.keys().__contains__('trajectories'):
        t_pts =  np.array(json_dat['trajectories'][0]['t'])
    else:
        t_pts =  np.array(json_dat['t'])

    # Sim starts at time 0, and current is at time t_pts[-1] or time 0 if forecast
    if tpoi <= 0:
        # the tpoi is in reverse time, so the present is time 0.
        tpoi_forward = t_pts[-1] - abs(tpoi)
    else:
        tpoi_forward = tpoi

    # Is the time point of interest before the spillover (gives total CURRENTLY in loc)
    if tpoi_forward <= 0 or tpoi_forward >= t_pts[-1]:

        before_spillover = 1
        if tpoi_forward <= 0:
            t_idx = 0
            before_spillover = 0
        else:
            t_idx = len(t_pts) - 1
        
        final_pops = {}
        for k in compartments:
            if json_dat.keys().__contains__('trajectories'):
                pop = np.array(json_dat['trajectories'][0][k])
            else:
                pop = np.array(json_dat[k])

            # create dictionary element for each location (summing over all subtypes)
            pop_size = np.array([])
            for loc in range(pop.shape[0]):
                if len(pop.shape) < 3:
                    num_in_k = np.sum(pop[loc,...,t_idx]) * before_spillover
                else:
                    num_in_k = np.sum(pop[:,loc,...,t_idx]) * before_spillover
                pop_size = np.append(pop_size, num_in_k)
            
            final_pops[k] = pop_size

    else: 
        # find flanking time pts idx, and do linear interpolation of their values
        del_t = t_pts - tpoi_forward
        t_idx = (np.where(del_t < 0)[0][-1], np.where(del_t > 0)[0][0])
        lower_weight = (tpoi_forward - t_pts[t_idx[0]]) / (t_pts[t_idx[1]] - t_pts[t_idx[0]])
    
        final_pops = {}
        for k in compartments:
            # only get first trajectory, [0]
            if json_dat.keys().__contains__('trajectories'):
                pop = np.array(json_dat['trajectories'][0][k])
            else:
                pop = np.array(json_dat[k])

            # create dictionary element for each location (summing over all subtypes)
            pop_size = np.array([])
            for loc in range(pop.shape[0]):
                # linear interpolation between two closest time pts
                if len(pop.shape) < 3:
                    num_in_k = lower_weight * np.sum(pop[loc,...,t_idx[0]]) + \
                            (1-lower_weight) *  np.sum(pop[loc,...,t_idx[1]])
                else:
                    num_in_k = lower_weight * np.sum(pop[:,loc,...,t_idx[0]]) + \
                            (1-lower_weight) *  np.sum(pop[:,loc,...,t_idx[1]])
                pop_size = np.append(pop_size, num_in_k)

            final_pops[k] = pop_size#.flatten()

    return final_pops

def get_combined_popSize_at_t(json_dat, compartments, tpoi=0):
    icd = get_popSize_at_t(json_dat, compartments, tpoi) 
    num_locs = len(icd[compartments[0]])
    combined_pop_size = np.zeros(num_locs)

    for key, value in icd.items():
        combined_pop_size = combined_pop_size + value
    return {"Prevalence" : combined_pop_size}

def get_sim_time(json_dat):
    # some sims terminate early (sim_time != stop_time)
    if json_dat.keys().__contains__('trajectories'):
        t_pts =  np.array(json_dat['trajectories'][0]['t'])
    else:
        t_pts =  np.array(json_dat['t'])
    return np.array([t_pts[-1]])

def get_age_most_recent_tip(nexus_tree_str, sim_time):
    ptrn = re.compile(r'time=[\.0-9]+')
    node_times = [float(re.sub('time=', '',x)) for x in re.findall(ptrn, nexus_tree_str)]
    if len(node_times) > 0:
        most_recent_tip_time = np.max(node_times)
    else:
        most_recent_tip_time = 0
    most_recent_tip_age = sim_time - most_recent_tip_time
    return np.round(most_recent_tip_age, decimals=6)

def remove_stem_branch(newick_file):
    # read in tree file
    with open(newick_file, 'r') as file:
        tree = file.read().strip()
    final_parenthesis = tree.rfind(')')
    new_tree = tree[:final_parenthesis + 1] + ';'  
    with open(newick_file, 'w') as file:
        file.write(new_tree)

def make_extant_phy(newick_file):
    """Prunes a phylogenetic tree by removing non-extant taxa and writes the
    pruned tree to a file.

    The function takes a phylogenetic tree `phy` and a file name `prune_fn` as 
    input. It prunes the tree by removing non-extant taxa and writes the pruned
    tree to the specified file.

    Args:
        phy (Tree): The input phylogenetic tree.
        prune_fn (str): The file name or path to write the pruned tree.

    Returns:
        dp.Tree: The pruned phylogenetic tree if pruning is successful,
                 or None if the pruned tree would have fewer than two
                 leaf nodes (invalid tree).

    """
    # copy original tree file
    saved_file = '.'.join(newick_file.split('.')[0:-1]) + '.orig.tre'
    shutil.copyfile(newick_file, saved_file)
    # read in tree file
    phy = dp.Tree.get(path=newick_file, schema='newick')
    # compute all root-to-node distances
    root_distances = phy.calc_node_root_distances()
    # find tree height (max root-to-node distance)
    tree_height = np.max( root_distances )
    # tips are considered "at present" if age is within 0.0001 * tree_height
    tol = tree_height * 1e-5
    # create empty dictionary
    d = {}
    # loop through all leaf nodes
    leaf_nodes = phy.leaf_nodes()
    for i,nd in enumerate(leaf_nodes):
        # convert root-distances to ages
        age = tree_height - nd.root_distance
        nd.annotations.add_new('age', age)
        # ultrametricize ages for extant taxa
        if age < tol:
            age = 0.0
        # store taxon and age in dictionary
        taxon_name = str(nd.taxon).strip('\'')
        taxon_name = taxon_name.replace(' ', '_')
        d[ taxon_name ] = age
    # determine what to drop
    drop_taxon_labels = [ k for k,v in d.items() if v > 1e-12 ]
    # inform user if pruning yields valid tree
    if len(leaf_nodes) - len(drop_taxon_labels) >= 2:
        # prune non-extant taxa
        phy.prune_taxa_with_labels( drop_taxon_labels )
        # write pruned tree
        phy.write(path=newick_file, schema='newick')
    else:
        f = open(newick_file, 'w')
        f.write(';\n')
        f.close()
    return
    
def convert_phy2dat_nex(phy_nex_str, num_locs, tip_type = "Sampled"):
    # this converst integers to one hot. 
    # Useful when there are a lot of locations, but can lead to confusion
    # phyddle needs to be told 5 chars and encoding = integer
    """
    """
    loc_binary = np.repeat("0", num_locs)

    # get tip names and states from NHX tree
    # nex_file = open(phy_nex_fn, 'r')
    # nex_str  = nex_file.readlines()[3]
    tip_pattern_string = rf'[0-9]+\[\&type="{tip_type}",location="[0-9 ]+"'
    matches  = re.findall(pattern=tip_pattern_string, string=phy_nex_str)
    # matches  = re.findall(pattern=r'[0-9]+\[\&type="Sampled",location="[0-9 ]+"', string=phy_nex_str)
    num_taxa = len(matches)
    # nex_file.close()
    tax_list = [re.findall(pattern = r'^[0-9]+', string=x)[0] 
                for i,x in enumerate(matches)]
    loc_list = [re.findall(pattern = r"location=.+", string=x)[0].split('"')[1] 
                for i,x in enumerate(matches)]
    tax_loc = zip(tax_list, loc_list)
    # generate taxon-state data
    #d = {}
    s_state_str = ''
    for taxon,v in tax_loc:
        current_loc = int(v.split(" ")[0])
        current_loc_binary_state = loc_binary.copy()
        current_loc_binary_state[current_loc] = "1"
        state = current_loc_binary_state
        vec_str      = ''.join(state)
        s_state_str += taxon + '  ' + vec_str + '\n'

    # build new nexus string
    s = \
'''#NEXUS
Begin DATA;
Dimensions NTAX={num_taxa} NCHAR={num_char};
Format MISSING=? GAP=- DATATYPE=STANDARD SYMBOLS="01";
Matrix
{s_state_str}
;
END;
'''.format(num_taxa=num_taxa, num_char=int(num_locs), s_state_str=s_state_str)

    return s


def blank_phy2dat_nex(phy_fn):
    """
    Creates a dummy nexus file with 1 character only in state 0

    Args:
        phy_nex_fn (str): The file name or path of the phylogenetic tree file in Newick format.
        int2vec (List[int]): The mapping of integer states to binary state vectors.

    Returns:
        str: The NEXUS file content as a string.

    Raises:
        FileNotFoundError: If the phylogenetic tree file at `phy_fn` does not exist.
    """


    num_char = 1
    # get tip names and states from Newick tree
    nex_file = open(phy_fn, 'r')
    phy = dp.Tree.get(file=open(phy_fn, 'r'), schema='newick')
    tax_list = [ x.taxon.label for x in phy.leaf_nodes() ]
    num_taxa = len(tax_list)
    # generate taxon-state data
    s_state_str = ''
    for taxon in tax_list:
        s_state_str += taxon + '  0\n'

    # build new nexus string
    s = \
'''#NEXUS
Begin DATA;
Dimensions NTAX={num_taxa} NCHAR={num_char}
Format MISSING=? GAP=- DATATYPE=STANDARD SYMBOLS="0";
Matrix
{s_state_str}
;
END;
'''.format(num_taxa=num_taxa,
           num_char=num_char,
           s_state_str=s_state_str)

    return s

def logit_params(param_dict, target_keys, offset = 0,  replace = False):
    # add or replace the values in target keys in param_dict with the log-value
    # and prepend "log_" to the key
    for k in target_keys:
        assert( k in param_dict.keys())
        if replace:
            val = param_dict.pop(k)
            val[val > 1] = 1
            param_dict['logit_' + k] = np.log((val + offset)/(1 - val + offset))
        else:
            val = param_dict[k]
            val[val > 1] = 1
            param_dict['logit_' + k] = np.log((val + offset)/(1 - val + offset))
    return param_dict


def log_params(param_dict, target_keys, offset = 0,  replace = False):
    # add or replace the values in target keys in param_dict with the log-value
    # and prepend "log_" to the key
    for k in target_keys:
        assert( k in param_dict.keys())
        if replace:
            val = param_dict.pop(k)
            param_dict['log_' + k] = np.log(val + offset)
        else:
            param_dict['log_' + k] = np.log(param_dict[k] + offset)
    return param_dict

def sqrt_params(param_dict, target_keys, replace = False):
    # add or replace the values in target keys in param_dict with the square root-value
    # and prepend "sqrt_" to the key
    for k in target_keys:
        assert( k in param_dict.keys())
        if replace:
            val = param_dict.pop(k)
            param_dict['sqrt_' + k] = np.sqrt(val)
        else:
            param_dict['sqrt_' + k] = np.sqrt(param_dict[k])
    return param_dict


## oldies but maybe goodies
def convert_phy2dat_nex_geosse(phy_nex_fn,
                        states,
                        type_match="[A-Za-z0-9_]+",
                        location_match="[0-9 ]+",
                        reaction_match="[A-Za-z0-9_]+",
                        drop_hidden=False):
    """
    Converts a phylogenetic tree in NHX format to a NEXUS file with taxon-state data.

    Reads the phylogenetic tree file in NHX format specified by `phy_nex_fn` and converts it to a NEXUS file containing taxon-state data. The binary state representations are based on the provided `int2vec` mapping.

    Args:
        phy_nex_fn (str): The file name or path of the phylogenetic tree file in NHX format.
        int2vec (List[int]): The mapping of integer states to binary state vectors.

    Returns:
        str: The NEXUS file content as a string.

    Raises:
        FileNotFoundError: If the phylogenetic tree file at `phy_nex_fn` does not exist.
    """

    # number of states
    num_char = len(states[0])
    
    # read tree
    nex_file = open(phy_nex_fn, 'r')
    nex_str  = nex_file.readlines()[3]
    nex_file.close()
    
    # find all taxon names and tip states (compartments/locations)
    pattern =   '([0-9]+)\\[\\&'
    pattern += f'type="({type_match})",'
    pattern += f'location="({location_match})",'
    matches = re.findall(pattern=pattern, string=nex_str)
    num_taxa = len(matches)
    
    # generate taxon-state data
    s_state_str = ''
    for i,v in enumerate(matches):
        t = v[0]
        s = ''.join([ str(x) for x in states[int(v[2])] ])       
        s_state_str += t + '  ' + s + '\n'
    
    # build new nexus string
    s = \
'''#NEXUS
Begin DATA;
Dimensions NTAX={num_taxa} NCHAR={num_char}
Format MISSING=? GAP=- DATATYPE=STANDARD SYMBOLS="01";
Matrix
{s_state_str}
;
END;
'''.format(num_taxa=num_taxa,
           num_char=num_char,
           s_state_str=s_state_str)

    return s

# def cleanup(prefix, clean_type):
# 	xml_fn   = f'{prefix}.xml'
# 	#beast_fn = f'{prefix}.beast.log'
# 	json_fn  = f'{prefix}.json'
# 	# logging clean-up
# 	if clean_type == 'clean':
# 		for x in [ xml_fn, beast_fn, json_fn ]:
# 			if os.path.exists(x):
# 				os.remove(x)
# 	elif self.sim_logging == 'compress':
# 		for x in [ xml_fn, beast_fn, json_fn ]:
# 			if os.path.exists(x):
# 				with open(x, 'rb') as f_in:
# 					with gzip.open(x+'.gz', 'wb') as f_out:
# 						shutil.copyfileobj(f_in, f_out)        
# 				os.remove(x)
# 	elif self.sim_logging == 'verbose':
# 		pass
# 		# do nothing
# 	return
