#!/usr/bin/env python
"""
BirthDeathModel
=========
Defines a class for the birth-death model.
Derives from phyddle.Model.BaseModel.

Authors:   Michael Landis and Ammon Thompson
Copyright: (c) 2022-2023, Michael Landis and Ammon Thompson
License:   MIT
"""

# import itertools
# import scipy as sp
# import numpy as np

from .model import BaseModel
from masterpy import Event #States,Event

SIG_DIGIT = 3
RATE_SCALE = 1. # 10. ** SIG_DIGIT
BASE_RATE = 1. / RATE_SCALE
# BASE_RATE = BASE_RATE / 5

class BirthDeathModel(BaseModel):

    # initialize model
    def __init__(self, args):
        super().__init__(args)
        self.set_args(args)
        self.model_variant_check()
        self.set_model(None)
        return

    # assign initial arguments
    def set_args(self, args):
        super().set_args(args)
        self.num_char        = 0
        self.num_states      = 1
        self.num_hidden_char = args['num_hidden_char']
        # self.dim = [ self.num_states ] * 2 + [ self.num_hidden_char + 1 ]

        return

    def set_model(self, seed=None):
        super().set_model(seed)
        return

    def model_variant_check(self):

        self.model_death_density = ('DensityDependentDeath' in self.model_variant)

        assert ('EqualRates' in self.model_variant) or \
               ('FreeRates' in self.model_variant)

    # birth-death state space
    def make_states(self):

        nhc = self.num_hidden_char
        states = {}

        # default Birth-Death compartments
        states['Extant'] = (nhc,)
        states['Extinct'] = (nhc,)
        states['SampleCount'] = (nhc,)

        return states

    def make_params(self):
        params = {}

        # get sim RV functions and arguments
        num_states = self.num_states
        shape_mtx = (num_states,num_states)
        # TODO: add hidden character support?
        num_hidden_char = self.num_hidden_char
        rv_fn = self.rv_fn
        rv_arg = self.rv_arg

        # assume all variables are iid, modify later if required by model variant
        params = {
            'DivConst' : rv_fn['DivConst'](size=num_states, random_state=self.rng, **rv_arg['DivConst']),
            'Turnover' : rv_fn['Turnover'](size=num_states, random_state=self.rng, **rv_arg['Turnover'])
        }
        
        # convert to rates
        params['BirthConst'] = params['DivConst'] / abs(1.0 - params['Turnover'])
        params['DeathConst'] = params['BirthConst'] * params['Turnover']

        # Simulation time
        params['Stop_time'] = rv_fn['Stop_time'](size=1, random_state=self.rng, **rv_arg['Stop_time'])

        # proportion of sample in tree
        params['nSampled_tips'] = rv_fn['nSampled_tips'](size=1, random_state=self.rng, **rv_arg['nSampled_tips'])

        # visit depart-return rates
        if self.model_death_density:
            params['DeathCarryK'] = rv_fn['DeathCarryK'](size=1,random_state=self.rng, **rv_arg['DeathCarryK'])
            # b - d - (K - 1) * x = 0   ## net diversification of 0
            # b - d = (K - 1) * x
            # x = (b - d) / (K - 1)
            d = params['DeathConst']
            b = params['BirthConst']
            K = params['DeathCarryK']
            params['DeathDensity'] = (b - d) / (K - 1)

        # # apply equal rates        
        # if 'EqualRates' in self.model_variant:
        #     for k,v in params.items():
        #         if len(v.shape) == 1:
        #             params[k] = np.full(v.shape, v[0])
        #         elif len(v.shape) == 2:
        #             params[k] = np.full(v.shape, v[0][0])
        #         elif len(v.shape) == 3:
        #             params[k] = np.full(v.shape, v[0][0][0])
        #         else:
        #             raise NotImplementedError('param has too many dimensions!')

        return params

    def make_sampled_states(self):
        sampled_states = [ 'Extant' ]
        return sampled_states

    def make_start_state(self, params):
        start_state = {}
        # note to self: assumes hidden state 0 for now
        start_state['Extant'] = '0'
        return start_state
        
    def make_start_sizes(self, params):
        nhc = self.num_hidden_char
        start_sizes = {}
        start_sizes['Extant'] = [ nhc ]
        return start_sizes
    
    def make_rate_sizes(self, params):
        """Make rate sizes,  not needed for this model."""
        rate_sizes = {}
        return rate_sizes

    def make_events(self):
        
        # Standard Birth-Death events
        events_birth_const = self.make_events_birth_const()
        events_death_const = self.make_events_death_const()

        # Use Density-Dependent Death model variant?
        if self.model_death_density:
            events_death_density = self.make_events_death_density()
        else:
            events_death_density = []

        events = events_birth_const + \
                 events_death_const + \
                 events_death_density
        
        return events

#####################

    def make_events_birth_const(self):
        group = 'Birth_Const'
        name = 'r_birth_const'
        idx = {}
        events = []
        rate = self.params['BirthConst'][0]
        ix = [ '1Extant[u]:1' ]
        jx = [ '2Extant[u]:1' ]
        dim = {'u':self.num_hidden_char}

        e = Event( g=group, n=name, idx=idx, r=rate, ix=ix, jx=jx, dim=dim )
        events.append(e)
        return events

    def make_events_death_const(self):
        group = 'Death_Const'
        name = 'r_death_const'
        idx = {}
        events = []
        rate = self.params['DeathConst'][0]
        ix = [ '1Extant[u]:1' ]
        jx = [ '1Extinct[u]:1' ]
        dim = {'u':self.num_hidden_char}
        
        e = Event( g=group, n=name, idx=idx, r=rate, ix=ix, jx=jx, dim=dim )
        events.append(e)
        return events

    def make_events_death_density(self):
        group = 'Death_Density'
        name = 'r_death_density'
        idx = {}
        events = []
        rate = self.params['DeathDensity'][0]
        ix = [ '1Extant[u]:1', '1Extant[u]:2' ]
        jx = [ '1Extinct[u]:1', '1Extant[u]:2' ]
        dim = {'u':self.num_hidden_char}
        
        e = Event( g=group, n=name, idx=idx, r=rate, ix=ix, jx=jx, dim=dim )
        events.append(e)
        return events
