#!/usr/bin/env python
"""
model
=====
Defines BaseModel class used for internal simulations.

Authors:   Michael Landis and Ammon Thompson
Copyright: (c) 2022-2023, Michael Landis and Ammon Thompson
License:   MIT
"""

import masterpy
import numpy as np
#import re
import itertools

class BaseModel:
    def __init__(self, args):
        """
        Initializes the BaseModel.

        Args:
            args (dict): A dictionary containing the arguments for initialization.
        """
        self.model_stochastic = False
        return
    
    def set_args(self, args):
        """
        Sets the arguments for the model.
        
        Args:
            args (dict): A dictionary containing the arguments.
        """

        self.model_type         = args['model_type']
        self.model_variant      = args['model_variant']
        # Sim model type (stochastic or deterministic; sample tree or not)
        self.model_deterministic = ('Deterministic' in self.model_variant)
        self.model_stochastic = ('Stochastic' in self.model_variant)
        self.model_no_tree = ('NoTree' in self.model_variant)
        if self.model_deterministic:
            self.model_stochastic = False
            self.model_no_tree = True
        if not self.model_deterministic and not self.model_stochastic and not self.model_no_tree:
            self.model_stochastic = True
        self.rv_fn              = args['rv_fn']
        self.rv_arg             = args['rv_arg']
        self.dir                = args['dir']
        self.prefix             = args['prefix']
        self.min_num_taxa       = args['min_num_taxa']
        self.max_num_taxa       = args['max_num_taxa']

        # this limits the size of outbreaks. If they get too large, sim is too slow
        if 'max_num_unsampled_lineages' in args:
            self.max_num_unsampled_lineages = args['max_num_unsampled_lineages']
        else:
            self.max_num_unsampled_lineages = int(1000)

        # The number of time pts is evenly spaced and set before the sim runs.
        # If the sim terminates early, there may be a slight mismatch between the time-scale of
        # of the json data and that of the phylogenetic tree. A higher number of time pts
        # decreases that mismatch.
        if 'num_sample_time_pts' in args:
            self.num_sample_time_pts = args['num_sample_time_pts']
        else:
            self.num_sample_time_pts = int(1000)


        return
    
    def set_model(self, seed=None):
        """
        Sets the model.

        Args:
            seed (int, optional): The random seed value. Defaults to None.
        """
        # set RNG seed if provided
        #print("BaseModel.set_model", seed)
        
        # set RNG
        self.seed        = seed
        self.rng         = np.random.Generator(np.random.PCG64(seed))
        # state space
        self.states      = self.make_states()
        # params space
        self.params      = self.make_params()
        # sampled states
        self.sampled_states = self.make_sampled_states()
        # starting state
        self.start_state = self.make_start_state(self.params)
        # starting compartment sizes
        self.start_sizes = self.make_start_sizes(self.params)
        # rate-scaling compartment sizes
        self.rate_sizes = self.make_rate_sizes(self.params)
        # event space
        self.events      = self.make_events()
        # event space dataframe
        self.df_events   = masterpy.events2df(self.events)
        # number of independent lineages (number of trees sampled from same sim population)
        self.num_trees = 1
        # done
        return

    def make_xml(self, idx):
        """
        Creates an XML specification string for a simulation.

        Parameters:
        - idx (int): The index of the simulation.

        Returns:
        - xml_spec_str (str): The XML specification string for the simulation.
        """
        # state space
        xml_statespace = ''
        for k,v in self.states.items():
            var = k
            # create dimension string based on value type (vector vs. scalar)
            if isinstance(v, tuple) or isinstance(v, list):
                dim = ' '.join(str(x) for x in v)
            else:
                dim = str(v)
            xml_statespace += f"<populationType spec='PopulationType' typeName='{var}' id='{var}' dim='{dim}'/>\n"
        
        # reaction groups
        xml_events = ''
        groups = set(self.df_events.group)
        for g in groups:
            xml_events += "<reactionGroup spec='ReactionGroup' reactionGroupName='{g}'>\n".format(g=g)
            for i in range(0, len(self.df_events[ self.df_events.group == g ])):
                row        = self.df_events[ self.df_events.group == g ].iloc[i]
                rate       = row['rate']
                name       = row['name']
                reaction   = row['reaction']
                predicate  = row['predicate']
                xml_events += f"\t<reaction spec='Reaction' reactionName='{name}' rate='{rate}'>\n"
                xml_events += f"\t\t{reaction}\n"
                if predicate != '':
                    xml_events += f"\t\t\t<predicate spec='Predicate' value='{predicate}'/>\n"
                #if predicate
                xml_events +=  "\t</reaction>\n"
            xml_events += "</reactionGroup>\n"
            xml_events += '\n'

        # INITIAL MODEL STATE
        xml_init_state = "\n<initialState spec='InitState'>\n"
        
        # seed compartment(s)
        xml_init_state += "\t<!-- START STATE -->\n"

        for k,v in self.start_state.items():
            # Stochastic default
            if self.model_stochastic and not self.model_no_tree:
                xml_init_state += "\t<lineageSeedMultiple spec='MultipleIndividuals' copies='{n}'>\n".format(n=self.num_trees)
                xml_init_state += "\t\t<population spec ='Population' type='@{k}' location='{v}'/>\n".format(k=k, v=v)
                xml_init_state += "\t</lineageSeedMultiple>\n"
            # no lineage trace (no tree)
            else:
                xml_init_state += "\t<populationSize spec='PopulationSize' size='{n}'>\n".format(n=self.num_trees)
                xml_init_state += "\t\t<population spec ='Population' type='@{k}' location='{v}'/>\n".format(k=k, v=v)
                xml_init_state += "\t</populationSize>\n"

        xml_init_state += "\n"

        # compartments for state-valued individuals        
        xml_init_state += "\t<!-- COMPARTMENT SIZES -->\n"
        for k,v in self.start_sizes.items(): 
            for i,y in np.ndenumerate(v):
                loc_str = ' '.join([str(x) for x in i])
                xml_init_state += f"\t<populationSize spec='PopulationSize' size='{y}'>\n"
                xml_init_state += f"\t\t<population spec='Population' type='@{k}' location='{loc_str}'/>\n"
                xml_init_state +=  "\t</populationSize>\n"

        xml_init_state += "\n"

        # compartments for rate-scaling factors                    
        xml_init_state += "\t<!-- RATE SCALERS -->\n"
        for k,v in self.rate_sizes.items():
            dim = self.states[k]
            if isinstance(dim, int):
                dim = [dim]
            idx_range = [ list(range(x)) for x in dim ]

            # MJL 231113: note, we are not handling hidden rate categories!
            idx_prod = list(itertools.product(*idx_range))
            for i,y in enumerate(idx_prod):
                loc_str = ' '.join([str(x) for x in y])
                if len(y) == 1:
                    pop_size = v[0] # <-- v[0] - 1
                else:
                    pop_size = v[y[0:-1]]
                xml_init_state += f"\t<populationSize spec='PopulationSize' size='{pop_size}'>\n"
                xml_init_state += f"\t\t<population spec='Population' type='@{k}' location='{loc_str}'/>\n"
                xml_init_state +=  "\t</populationSize>\n"
        xml_init_state += "</initialState>\n"

        # out file names
        newick_fn = '{dir}/{prefix}.{idx}.tre'.format(dir=self.dir, prefix=self.prefix, idx=idx)
        nexus_fn  = '{dir}/{prefix}.{idx}.nex.tre'.format(dir=self.dir, prefix=self.prefix,  idx=idx)
        json_fn   = '{dir}/{prefix}.{idx}.json'.format(dir=self.dir, prefix=self.prefix,  idx=idx)
        xml_output_spec = masterpy.get_xml_output_spec(stochastic = self.model_stochastic,
                                                        no_tree   = self.model_no_tree, 
                                                        newick_fn = newick_fn,
                                                        nexus_fn  = nexus_fn,
                                                        json_fn   = json_fn)

        # Simulation type: deterministic, stochastic, tree, or no tree
        xml_run_spec = masterpy.get_xml_run_spec(self.model_stochastic, 
                                                    self.model_no_tree,
                                                    self.params['Stop_time'][0],
                                                    self.num_sample_time_pts)
        num_lineages = self.max_num_taxa * self.max_num_unsampled_lineages
        xml_sim_conditions = "" 
        xml_filter = ""       
        if self.model_stochastic and not self.model_no_tree:    
            # MJL 231009: nLineages needs to be much larger than max_num_taxa to
            # generate non-empty trees. Discuss later with group.
          
            # sim conditions
            xml_sim_conditions += "<lineageEndCondition spec='CompositeLineageEndCondition' andMode='false'>\n"
            xml_sim_conditions += f"\t<lineageEndCondition spec='LineageEndCondition' nLineages='{num_lineages}' alsoGreaterThan='true' isRejection='false'/>\n"
            xml_sim_conditions += "\t<lineageEndCondition spec='LineageEndCondition' nLineages='0' alsoGreaterThan='false' isRejection='false'/>\n"
            xml_sim_conditions += "</lineageEndCondition>\n"

            # post-processing filter
            for k in self.sampled_states:
                #xml_filter += "<!--\n"
                xml_filter += f"<inheritancePostProcessor spec='LineageFilter' populationName='{k}' reverseTime='false' discard='false' leavesOnly='false' noClean='false'/>\n"
                #xml_filter +=  "-->\n"
            xml_filter += f"<inheritancePostProcessor spec='LineageSampler' nSamples='{self.params['nSampled_tips'][0]}'/>\n"
        
        # developing
        # if self.model_deterministic:
        #     xml_sim_conditions += f"<populationEndCondition spec='PopulationEndCondition' threshold='{num_lineages}' exceedCondition='true'\n"
        #     xml_sim_conditions += f"\t<population spec='Population populationName=TBD..."
        #     xml_sim_conditions += f"</populationEndCondition>\n"

        # generate entire XML specification
        xml_spec_str = '''\
<beast version='2.0' namespace='master:master.model:master.steppers:master.conditions:master.postprocessors:master.outputs'>

{xml_run_spec}

<model spec='Model'>

{xml_statespace}

{xml_events}

</model>

{xml_init_state}

{xml_sim_conditions}

{xml_filter}

{xml_output_spec}

</run>
</beast>
'''.format(xml_run_spec=xml_run_spec,
           xml_statespace=xml_statespace,
           xml_events=xml_events,
           xml_init_state=xml_init_state,
           xml_sim_conditions=xml_sim_conditions,
           xml_filter=xml_filter,
           xml_output_spec=xml_output_spec)
        
        return xml_spec_str
    

    def clear_model(self):
        """
        Clears the model.
        """
        self.is_model_set = False
        self.states = None
        self.params = None
        self.events = None
        self.df_events = None
        self.df_states = None
        return
    
    def make_settings(self):
        """
        Creates the settings for the model.

        Raises:
            NotImplementedError: This method should be implemented in derived classes.
        """
        raise NotImplementedError
    
    def make_states(self):
        """
        Creates the state space for the model.

        Raises:
            NotImplementedError: This method should be implemented in derived classes.
        """
        raise NotImplementedError
    
    def make_events(self):
        """
        Creates the event space for the model.

        Raises:
            NotImplementedError: This method should be implemented in derived classes.
        """
        raise NotImplementedError
    
    def make_params(self):
        """
        Creates the parameter space for the model.

        Raises:
            NotImplementedError: This method should be implemented in derived classes.
        """
        raise NotImplementedError
    
    def make_sampled_states(self):
        """
        Defines which compartments to sample when retaining tree.

        Raises:
            NotImplementedError: This method should be implemented in derived classes.
        """
        raise NotImplementedError    

    def make_start_state(self, params):
        """
        Creates the starting state for the model.

        Raises:
            NotImplementedError: This method should be implemented in derived classes.
        """
        raise NotImplementedError
    
    def make_start_sizes(self, params):
        """
        Creates the starting sizes for the model.

        Raises:
            NotImplementedError: This method should be implemented in derived classes.
        """
        raise NotImplementedError
    
    def make_rate_sizes(self, params):
        """
        Creates the rate-scaler compartment sizes for the model.

        Raises:
            NotImplementedError: This method should be implemented in derived classes.
        """
        raise NotImplementedError
