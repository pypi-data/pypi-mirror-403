#!/usr/bin/env python
"""
SirModel
=========
Defines a class for a Susceptible-Infectious-Recovered (SIR) model.
Dervies from phyddle.Model.BaseModel.

Authors:   Michael Landis and Ammon Thompson
Copyright: (c) 2022-2023, Michael Landis and Ammon Thompson
License:   MIT
"""

# import itertools
import scipy as sp
import numpy as np
import json
import masterpy

from .model import BaseModel
from masterpy import Event #States,Event

SIG_DIGIT = 3
RATE_SCALE = 10. ** SIG_DIGIT
BASE_RATE = 1. / RATE_SCALE
# BASE_RATE = BASE_RATE / 5

class SirModel(BaseModel):

    # initialize model
    def __init__(self, args):
        super().__init__(args)
        self.set_args(args)
        self.set_model(None) 
        self.model_variant_check()
        return
    
    # assign initial arguments
    def set_args(self, args):
        super().set_args(args)
        
        self.num_char = args['num_char']
        self.num_states = args['num_states']
        self.num_hidden_char = args['num_hidden_char']
        self.dim = [ self.num_states ] * 2 + [ self.num_hidden_char + 1 ]

        # set model variant [Default = Migration]
        # order of precedence: VisitorApproximation > Visitor > migration
        self.model_visitor = ('Visitor' in self.model_variant)
        self.model_visitor_approx = ('VisitorApproximation' in self.model_variant)
        if ('Migration' in self.model_variant) \
                and not self.model_visitor \
                and not self.model_visitor_approx:
            self.model_migration = True
            assert('Migrate' in self.rv_fn.keys())
        else:
            self.model_migration = False

        self.model_recover_approx = ('RecoverApproximation' in self.model_variant)

        self.model_immunity_loss = ('ImmunityLoss' in self.model_variant )
        assert not (self.model_visitor and self.model_visitor_approx)

        self.model_exposed = ('Exposed' in self.model_variant)
        if self.model_exposed:
            self.num_exposed_cat = args['num_exposed_cat']
            assert(self.num_exposed_cat > 0)

        # Extant sampling
        if 'prop_extant_sampled' in args:
            self.prop_extant_sampled = args['prop_extant_sampled']
        else:
            self.prop_extant_sampled = 0

        return
    
    def set_model(self, idx):
        super().set_model(idx)
        return

    def model_variant_check(self):
        
        assert( ('EqualRates' in self.model_variant) or \
                ('FreeRates' in self.model_variant) )

    # SIR state space
    def make_states(self):
        
        # State space expects at most 2x observable characters (k states)
        #     and 1x hidden character (2 states)
        #
        # Each individual state is encoded as follows: [Home][Current][Hidden]. 
        #
        # Example of all states for k=3, regions ABC:
        #     AA0, AB0, AC0, AA1, AB1, AC1,
        #     BA0, BB0, BC0, BA1, BB1, BC1,
        #     CA0, CB0, CC0, CA1, CB1, CC1
        #
        # Encode these as indexed compartments in MASTER:
        #     [0,0,0], [0,1,0], [0,2,0], [0,0,1], [0,1,1], [0,2,1],
        #     [1,0,0], [1,1,0], [1,2,0], [1,0,1], [1,1,1], [1,2,1],
        #     [2,0,0], [2,1,0], [2,2,0], [2,0,1], [2,1,1], [2,2,1]
        #
        # In addition, use static compartments W,X,Y to scale rates
        # against the variable-indexed MASTER reactions.

        ns = self.num_states
        nhc = self.num_hidden_char
        
        states = {}

        # default SIR compartments
        states['Susceptible'] = (ns,ns,nhc)    # suscept  home/curr/hidden
        states['Contagious']  = (ns,ns,nhc)    # infect   home/curr/hidden
        states['Recovered']   = (ns,ns,nhc)    # recover  home/curr/hidden
        states['Sampled']     = (ns,nhc)       # sample   curr/hidden
        states['X']           = (1,)           # terminate lineage after sampling

        # default SIR rate scalers
        states['SampleScale']  = (ns,nhc)      # scales sample_A_to_I
        states['RecoverScale'] = (ns,nhc)      # scales recover_I_to_R
        states['InfectScale']  = (ns,nhc)      # scales infect_S_to_I
        states['R2SScale']     = (ns,nhc)

        if self.model_recover_approx and not self.model_visitor_approx:
            states['R2SScale']    = (ns,ns,nhc)
        
        # exposed model compartments/scalers
        if self.model_exposed:
            # home, current, E-stage, hidden-state
            nec = self.num_exposed_cat
            states['Infected'] = (ns,ns,nec,nhc)
            states['ProgressInfectedScale'] = (nhc)

        # visitor model compartments/scalers
        if self.model_visitor or self.model_visitor_approx:
            # home, current, hidden-state
            states['VisitDepartScale'] = (ns,ns,nhc)
            states['VisitReturnScale'] = (ns,ns,nhc)
        
        if self.model_visitor_approx:
            # states['Susceptible'] = (ns,1,nhc)
            # states['Recovered']   = (ns,1,nhc)
            states['InfectScale'] = (ns,ns,nhc)

        if self.model_migration:
            states['MigrateScale'] = (ns,ns,nhc)
        
        states['SampleCount'] = (ns)

        return states
        
    def make_params(self):
        params = {}

        # get sim RV functions and arguments
        num_states = self.num_states
        shape_mtx = (num_states,num_states)
        num_hidden_char = self.num_hidden_char
        rv_fn = self.rv_fn
        rv_arg = self.rv_arg

        # assume all variables are iid, modify later if required by model variant
        # S0 is initial num susceptible.
        params = {
            'S0'        : rv_fn['S0'](size=num_states, random_state=self.rng, **rv_arg['S0']),
            'R0'        : rv_fn['R0'](size=num_states, random_state=self.rng, **rv_arg['R0']),
            'Sample'    : rv_fn['Sample'](size=num_states, random_state=self.rng, **rv_arg['Sample']),
            'Recover'   : rv_fn['Recover'](size=num_states, random_state=self.rng, **rv_arg['Recover']),
        }

        # Simulation time
        params['Stop_time'] = rv_fn['Stop_time'](size=1, random_state=self.rng, **rv_arg['Stop_time'])

        # time point of interest for prediction of prevalence
        params['Time_of_interest'] = rv_fn['Time_of_interest'](size=1, random_state=self.rng, **rv_arg['Time_of_interest'])

        # proportion of sample in tree
        params['nSampled_tips'] = rv_fn['nSampled_tips'](size=1, random_state=self.rng, **rv_arg['nSampled_tips'])

        # Recover rate
        params['Recover'] = np.full(params['Recover'].shape, params['Recover'][0])

        # waining immunity: rate become susceptible R -> S.
        params['R2S'] = np.zeros(num_states)
        if self.model_immunity_loss and 'R2S' in rv_fn and 'R2S' in rv_arg:
            params['R2S'] = np.full(params['R2S'].shape, rv_fn['R2S'](size=1, random_state=self.rng, **rv_arg['R2S'])[0] )

        
        # set up initial compartment sizes
        params['S0'] = np.diag(np.array(np.round(params['S0']), dtype='int'))
        params['Total_S0'] = np.array([params['S0'][i,i] for i in range(params['S0'].shape[0])])

        # set up infect rate
        # the rate of entering the infection sequence (either Contagious or Infected[0])
        # beta is the rate of one infectious (I) infecting one susceptible (S)
        # MJL: work this out for self
        ## R0 = infect * S0 / (gamma + delta)
        ## lambda = R0 * (gamma + delta)  ## RevBayes
        ## beta_MASTER = lambda / S0      ## MASTER, S0 is the number CURRENTLY in location
        params['Infect'] = params['R0'] * (params['Recover'] + params['Sample']) *  (1. / np.diag(params['S0']))

        # visit depart-return rates
        # TODO: allow for different matrix structures (equal-return, equal-depart), or can be handled with custom rvs in script
        if self.model_visitor or self.model_visitor_approx:
            params['VisitDepart'] = rv_fn['VisitDepart'](size=num_states**2,
                                                         random_state=self.rng, 
                                                         **rv_arg['VisitDepart']).reshape(shape_mtx)
            params['VisitReturn'] = rv_fn['VisitReturn'](size=num_states**2,
                                                         random_state=self.rng, 
                                                         **rv_arg['VisitReturn']).reshape(shape_mtx)            
        elif self.model_migration: # migration model
            params['Migrate'] = rv_fn['Migrate'](size = num_states**2, 
                                                 random_state=self.rng, 
                                                 **rv_arg['Migrate']).reshape(shape_mtx)

        # disease progression rates
        if self.model_exposed:
            # all locations and infection stages progress at the same rate
            params['ProgressInfected'] = rv_fn['ProgressInfected'](size=1,
                                                                   random_state=self.rng,
                                                                   **rv_arg['ProgressInfected'])
        
        # apply equal rates        
        if 'EqualRates' in self.model_variant:
            for k,v in params.items():
                if len(v.shape) == 1:
                    params[k] = np.full(v.shape, v[0])
                elif len(v.shape) == 2:
                    params[k] = np.full(v.shape, v[0][0])
                elif len(v.shape) == 3:
                    params[k] = np.full(v.shape, v[0][0][0])
                else:
                    raise NotImplementedError('param has too many dimensions!')

        # get stationary frequencies
        if self.model_visitor or self.model_visitor_approx:
            vd = params['VisitDepart']
            vr = params['VisitReturn']
            
            f = np.zeros((num_states,num_states))
            for m in range(num_states):
                denom = 0.0
                for n in range(num_states):
                    # get numerator (unnormalized frequency)
                    numer = np.prod(vr[:,m]) / vr[m,m]    
                    if m != n:
                        numer = numer * vd[m,n] / vr[m,n]
                    f[m,n] = numer
                    # accumulate denominator (to normalize frequencies)
                    denom += numer
                # compute normalized frequencies
                f[m,:] = f[m,:] / denom

            params['VisitStationaryFreqs'] = f

            # multiply each the equilibrium home-away frequencies
            # by the base number of susceptibles for each location i
            params["stationary_S"] = np.diag(params['S0'])[:,np.newaxis] * f
            # beta / S, where S is the number of susceptibles CURRENTLY IN each location
            # if you want S to be FROM a location, then set np.sum axis to 1.
            # Doesn't matter for R0, but R(t) becomes hard to interpret if 
            # S is "FROM" rather than "CURRENTLY IN"
            params['Infect'] = params['R0'] * (params['Recover'] + params['Sample']) * \
                    (1. / np.sum(params["stationary_S"], axis = 0))

        # update home-away locations for susceptibles
        if self.model_visitor:
            params['S0'] = params["stationary_S"]            

        # only keep diagonal elements for visitor approx
        if self.model_visitor_approx:
            params['S0'] = np.diag(np.diag(params['S0']))
            # rescale infection rate and convert to matrix of infection rates
            params['VisitApproxInfect'] = np.multiply(params['Infect'], params['VisitStationaryFreqs'])

        # only keep diagonal elements for migration model
        if self.model_migration:
            params['S0'] = np.diag(np.diag(params['S0']))

        # rescale R -> S rate for recovered compartment
        if self.model_recover_approx and not self.model_visitor_approx:
            params['ApproxR2S'] = np.multiply(params['R2S'], params['VisitStationaryFreqs'])

        ### Patient zero ###
        # set up initial patient zero outbreak state (contagious or infected)
        if self.model_visitor or self.model_visitor_approx:
            # sample uniformly across population based on size
            p_home_start = params['S0'].sum(axis=1) / np.sum(params['S0'])
            home_state = sp.stats.multinomial.rvs(n=1, p=p_home_start, random_state=self.rng)
            home_idx = np.where( home_state==1 )[0][0]
            curr_probs = params['VisitStationaryFreqs'][home_idx,:]
            curr_state = sp.stats.multinomial.rvs(n=1, p=curr_probs, random_state=self.rng)
            curr_idx = np.where( curr_state==1 )[0][0]
            params['StartState'] = np.array([home_idx, curr_idx])
        else:
            # sample uniformly across popuation based on size
            p_start_sizes = np.diag(params['S0']) / np.sum(np.diag(params['S0']))
            start_state = sp.stats.multinomial.rvs(n=1, p=p_start_sizes, random_state=self.rng)
            params['StartState'] = np.array([ np.where( start_state==1 )[0][0], np.where( start_state==1 )[0][0] ])
        
        # index case starts in exposed step 0 if SEIR model
        if self.model_exposed:
            params['StartState'] = np.append(params['StartState'], 0)
        
        # AMT 240402 NOTE: S0 hidden state issue. 
        # S0 setup above does not include the hidden states dimension.
        # Will need to implement a stationry distro among hidden states.
        # Assuming transitions among hidden states are possible for S0.
        params['S0'] = params['S0'].reshape(self.states['Susceptible'])
        
        return params

    def make_sampled_states(self):
        sampled_states = [ 'Sampled' ]
        return sampled_states

    def make_start_state(self, params):
        start_state = {}
        # note to self: assumes hidden state 0 for now
        if self.model_exposed:
            start_state['Infected'] = ' '.join([str(x) for x in params['StartState']]) + ' 0'
        else:
            start_state['Contagious'] = ' '.join([str(x) for x in params['StartState']]) + ' 0'
        return start_state
        
    def make_start_sizes(self, params):
        start_sizes = {}
        start_sizes['Susceptible'] = params['S0']
        return start_sizes
    
    def set_start_sizes(self, compartments):
        start_sizes = {}
        for k,v in compartments.items():
            start_sizes[k] = v
        self.start_sizes = start_sizes
        # return start_sizes

    def make_rate_sizes(self, params):
        rate_sizes = {}
        rate_sizes['SampleScale'] = params['Sample'] * RATE_SCALE
        rate_sizes['InfectScale'] = params['Infect'] * RATE_SCALE
        rate_sizes['RecoverScale'] = params['Recover'] * RATE_SCALE
        rate_sizes['R2SScale'] = params['R2S'] * RATE_SCALE
        
        if self.model_exposed:
            #rate_sizes['ToInfectedScale'] = params['ToInfected'] * RATE_SCALE
            rate_sizes['ProgressInfectedScale'] = params['ProgressInfected'] * RATE_SCALE

        if self.model_visitor or self.model_visitor_approx:
            rate_sizes['VisitDepartScale'] = params['VisitDepart'] * RATE_SCALE
            rate_sizes['VisitReturnScale'] = params['VisitReturn'] * RATE_SCALE

        if self.model_visitor_approx:
            rate_sizes['InfectScale'] = params['VisitApproxInfect'] * RATE_SCALE

        if self.model_recover_approx and not self.model_visitor_approx:
            rate_sizes['R2SScale'] = params['ApproxR2S'] * RATE_SCALE

        if self.model_migration:
            rate_sizes['MigrateScale'] = params['Migrate'] * RATE_SCALE

        return rate_sizes

    def make_events(self):
        
        # Standard SIR recovery and sampling
        events_R_to_S = self.make_events_R_to_S()
        events_I_to_R = self.make_events_I_to_R()
        events_I_to_A = self.make_events_I_to_A()

        # Use SIR or SEIR (exposure/infected) model?
        if self.model_exposed:
            events_S_to_I = []
            events_S_to_E = self.make_events_S_to_E()
            events_E_to_E = self.make_events_E_to_E()
            events_E_to_I = self.make_events_E_to_I()
        else:
            events_S_to_I = self.make_events_S_to_I()
            events_S_to_E = []
            events_E_to_E = []
            events_E_to_I = []

        # Use Visitor model?
        if self.model_visitor or self.model_visitor_approx:
            events_VD = self.make_events_VD()
            events_VR = self.make_events_VR()
            events_M  = []
        elif self.model_migration:
            events_M  = self.make_events_migration()
            events_VD = []
            events_VR = []
        else:
            events_VD = []
            events_VR = []
            events_M  = []

        # Tip sampling
        if self.model_stochastic:
            events_tip = self.make_events_tip_sample()
        else:
            events_tip = []

        # Extant sampling
        if self.prop_extant_sampled > 0:
            events_I_to_A_extant = self.make_events_I_to_A_extant()
        else:
            events_I_to_A_extant = []

        events = events_S_to_I + \
                 events_S_to_E + \
                 events_E_to_E + \
                 events_E_to_I + \
                 events_I_to_A + \
                 events_I_to_A_extant + \
                 events_I_to_R + \
                 events_R_to_S + \
                 events_VD + \
                 events_VR + \
                 events_M + \
                 events_tip
        
        return events

#####################
    # Basic SIR events

    def make_events_S_to_I(self):
        group = 'Infect_S_to_I'
        name = 'r_S_I'
        idx = {}
        events = []
        rate = BASE_RATE
        if self.model_visitor_approx:
            ix = [ 'Susceptible[h,h,u]',  'Contagious[i,j,u]:1', 'InfectScale[h,j,u]:2']
            jx = [ 'Contagious[h,j,u]:1', 'Contagious[i,j,u]:1', 'InfectScale[h,j,u]:2']
        else:
            ix = [ 'Susceptible[h,j,u]',  'Contagious[i,j,u]:1', 'InfectScale[j,u]:2']
            jx = [ 'Contagious[h,j,u]:1', 'Contagious[i,j,u]:1', 'InfectScale[j,u]:2']
        dim = {'h':self.num_states,
               'i':self.num_states,
               'j':self.num_states,
               'u':self.num_hidden_char}
        e = Event( g=group, n=name, idx=idx, r=rate, ix=ix, jx=jx, dim=dim )
        events.append(e)
        return events

    def make_events_I_to_R(self):
        group = 'Infect_I_to_R'
        name = 'r_I_R'
        idx = {}
        events = []
        rate = BASE_RATE
        if self.model_visitor_approx or self.model_recover_approx:
            ix = [ 'Contagious[h,j,u]', 'RecoverScale[j,u]' ]
            jx = [ 'Recovered[h,h,u]', 'RecoverScale[j,u]' ]
        else:
            ix = [ 'Contagious[h,j,u]', 'RecoverScale[j,u]' ]
            jx = [ 'Recovered[h,j,u]', 'RecoverScale[j,u]' ]
        dim = {'h':self.num_states,
               'j':self.num_states,
               'u':self.num_hidden_char}
        e = Event( g=group, n=name, idx=idx, r=rate, ix=ix, jx=jx, dim=dim )
        events.append(e)
        return events

    def make_events_R_to_S(self):
        group = 'Wane_R_to_S'
        name = 'r_R_S'
        idx = {}
        events = []
        rate = BASE_RATE
        if self.model_visitor_approx:
            ix = [ 'Recovered[h,h,u]', 'R2SScale[h,u]' ]
            jx = [ 'Susceptible[h,h,u]', 'R2SScale[h,u]']
        else:
            if self.model_recover_approx:
                ix = [ 'Recovered[h,h,u]', 'R2SScale[h,j,u]' ]
                jx = [ 'Susceptible[h,j,u]', 'R2SScale[h,j,u]' ]
            else:
                ix = [ 'Recovered[h,j,u]', 'R2SScale[h,u]' ]
                jx = [ 'Susceptible[h,j,u]', 'R2SScale[h,u]' ]
        dim = {'h':self.num_states,
               'j':self.num_states,
               'u':self.num_hidden_char}
        e = Event( g=group, n=name, idx=idx, r=rate, ix=ix, jx=jx, dim=dim )
        events.append(e)
        return events

    def make_events_I_to_A(self):

        # extant sampling approximation (set serial sampling rate to zero at T - dt)
        if self.prop_extant_sampled > 0:
            dt = 10**-10
            rate_string = str(BASE_RATE) + ":0," +  \
                "0:" + str(self.params['Stop_time'][0] - dt)
        else:
            rate_string = BASE_RATE

        idx = {}
        events = []
        rate = rate_string

        # sample infectious
        name = 'r_I_A'
        group = 'Sample_I_to_A'
        if self.model_visitor_approx or self.model_recover_approx:
            ix = [ 'Contagious[h,j,u]:1', 'SampleScale[j,u]:2' ]
            jx = [ 'Sampled[j,u]:1', 'Recovered[h,h,u]:2', 'SampleScale[j,u]:2', 'SampleCount[j]' ]
        else:
            ix = [ 'Contagious[h,j,u]:1', 'SampleScale[j,u]:2' ]
            jx = [ 'Sampled[j,u]:1', 'Recovered[h,j,u]:2', 'SampleScale[j,u]:2', 'SampleCount[j]' ]


        dim = {'h':self.num_states,
               'j':self.num_states,
               'u':self.num_hidden_char}
        e = Event( g=group, n=name, idx=idx, r=rate, ix=ix, jx=jx, dim=dim )
        events.append(e)

        # # sample infected
        # if self.model_exposed:
        #     name = 'r_E_A'
        #     group = 'Sample_EI_to_A'
        #     ix = [ 'Infected[h,j,u]', 'SampleScale[j,u]' ]
        #     jx = [ 'Sampled[j,u]', 'Recovered[h,j,u]', 'SampleScale[j,u]' ]
        #     e = Event(g=group, n=name, idx=idx, r=rate, ix=ix, jx=jx, dim=dim)
        #     events.append(e)

        return events
    
    def make_events_I_to_A_extant(self):

        # extant sampling approximation
        dt = 10**-7
        r = self.prop_extant_sampled / dt
        rate_string = "0:0," +  \
            str(r) + ":" + str(self.params['Stop_time'][0] - dt) + \
                ",0:" + str(self.params['Stop_time'][0])
        
        idx = {}
        events = []
        rate = rate_string

        # sample infectious
        name = 'r_I_A_extant'
        group = 'Sample_I_to_A_extant'
        if self.model_visitor_approx or self.model_recover_approx:
            ix = [ 'Contagious[h,j,u]:1']
            jx = [ 'Sampled[j,u]:1', 'Recovered[h,h,u]:2', 'SampleCount[j]' ]
        else:
            ix = [ 'Contagious[h,j,u]:1']
            jx = [ 'Sampled[j,u]:1', 'Recovered[h,j,u]:2', 'SampleCount[j]' ]


        dim = {'h':self.num_states,
               'j':self.num_states,
               'u':self.num_hidden_char}
        e = Event( g=group, n=name, idx=idx, r=rate, ix=ix, jx=jx, dim=dim )
        events.append(e)

        return events


#######################

    # Exposure Model

    def make_events_S_to_E(self):
        group = 'Infect_S_to_E'
        name = 'r_S_E'
        idx = {}
        events = []
        rate = BASE_RATE
        if self.model_visitor_approx:
            ix = [ 'Susceptible[h,h,u]',  'Contagious[i,j,u]:1', 'InfectScale[h,j,u]:2']
            jx = [ 'Infected[h,j,0,u]:1', 'Contagious[i,j,u]:1', 'InfectScale[h,j,u]:2']
        else:
            ix = [ 'Susceptible[h,j,u]', 'Contagious[i,j,u]:1', 'InfectScale[j,u]:2' ]
            jx = [ 'Infected[h,j,0,u]:1',  'Contagious[i,j,u]:1', 'InfectScale[j,u]:2' ]
        dim = {'h':self.num_states,
               'i':self.num_states,
               'j':self.num_states,
               'u':self.num_hidden_char}
        e = Event( g=group, n=name, idx=idx, r=rate, ix=ix, jx=jx, dim=dim )
        events.append(e)
        return events

    def make_events_E_to_E(self):
        group = 'Infect_E_to_E'
        name = 'r_E_E'
        idx = {}
        events = []
        rate = BASE_RATE
        predicate = 'k == l - 1'
        ix = [ 'Infected[h,j,k,u]:1', 'ProgressInfectedScale[u]:2']
        jx = [ 'Infected[h,j,l,u]:1', 'ProgressInfectedScale[u]:2']
        dim = {'h':self.num_states,
            'j':self.num_states,
            'l':self.num_exposed_cat,
            'u':self.num_hidden_char}
        
        if self.num_exposed_cat > 1:
            e = Event( g=group, n=name, idx=idx, r=rate, ix=ix, jx=jx, dim=dim, predicate=predicate )
            events.append(e)

        return events

    def make_events_E_to_I(self):
        group = 'Infect_E_to_I'
        k = self.num_exposed_cat - 1 # last exposed category-index!
        name = 'r_E_I'
        idx = {}
        events = []
        rate = BASE_RATE
        ix = [ f'Infected[h,j,{k},u]:1', 'ProgressInfectedScale[u]:2']
        jx = [ 'Contagious[h,j,u]:1', 'ProgressInfectedScale[u]:2']
        dim = {'h':self.num_states,
               'j':self.num_states,
               'u':self.num_hidden_char}
        e = Event( g=group, n=name, idx=idx, r=rate, ix=ix, jx=jx, dim=dim )
        events.append(e)
        return events

#######################
    # Migration Model

    def make_events_migration(self):
        group = 'Migrate'
        name = 'r_M'
        idx = {}
        events = []
        rate = BASE_RATE
        dim = {'h': self.num_states,
               'j': self.num_states,
               'u':self.num_hidden_char}
        predicate = 'h != j'
                # I (Contagious)
        ix = [ 'Contagious[h,h,u]:1', 'MigrateScale[h,j,u]:2' ]
        jx = [ 'Contagious[j,j,u]:1', 'MigrateScale[h,j,u]:2' ]
        e = Event(g=group, n=name, idx=idx, r=rate, ix=ix, jx=jx, dim=dim, predicate=predicate)
        events.append(e)
        
        # E (Infected)
        if self.model_exposed:
            ix = [ 'Infected[h,h,k,u]:1', 'MigrateScale[h,j,u]:2' ]
            jx = [ 'Infected[j,j,k,u]:1', 'MigrateScale[h,j,u]:2' ]
            e = Event(g=group, n=name, idx=idx, r=rate, ix=ix, jx=jx, dim=dim, predicate=predicate)
            events.append(e)

        # if not self.model_recover_approx:
        #     # R (Recovered)
        #     ix = [ 'Recovered[h,h,u]', 'VisitDepartScale[h,j,u]:2' ]
        #     jx = [ 'Recovered[h,j,u]', 'VisitDepartScale[h,j,u]:2' ]
        #     e = Event(g=group, n=name, idx=idx, r=rate, ix=ix, jx=jx, dim=dim, predicate=predicate)
        #     events.append(e)

        return events     

    # Visitor Model

    def make_events_VD(self):
        group = 'Visit_Depart'
        name = 'r_VD'
        idx = {}
        events = []
        rate = BASE_RATE
        dim = {'h':self.num_states,
               'j':self.num_states,
               'u':self.num_hidden_char}
        predicate = 'h != j'

        # I (Contagious)
        ix = [ 'Contagious[h,h,u]:1', 'VisitDepartScale[h,j,u]:2' ]
        jx = [ 'Contagious[h,j,u]:1', 'VisitDepartScale[h,j,u]:2' ]
        e = Event(g=group, n=name, idx=idx, r=rate, ix=ix, jx=jx, dim=dim, predicate=predicate)
        events.append(e)
        
        # E (Infected)
        if self.model_exposed:
            ix = [ 'Infected[h,h,k,u]:1', 'VisitDepartScale[h,j,u]:2' ]
            jx = [ 'Infected[h,j,k,u]:1', 'VisitDepartScale[h,j,u]:2' ]
            e = Event(g=group, n=name, idx=idx, r=rate, ix=ix, jx=jx, dim=dim, predicate=predicate)
            events.append(e)

        if self.model_visitor:
            # S (Susceptible)
            ix = [ 'Susceptible[h,h,u]', 'VisitDepartScale[h,j,u]:2' ]
            jx = [ 'Susceptible[h,j,u]', 'VisitDepartScale[h,j,u]:2' ]
            e = Event(g=group, n=name, idx=idx, r=rate, ix=ix, jx=jx, dim=dim, predicate=predicate)
            events.append(e)

            if not self.model_recover_approx:
                # R (Recovered)
                ix = [ 'Recovered[h,h,u]', 'VisitDepartScale[h,j,u]:2' ]
                jx = [ 'Recovered[h,j,u]', 'VisitDepartScale[h,j,u]:2' ]
                e = Event(g=group, n=name, idx=idx, r=rate, ix=ix, jx=jx, dim=dim, predicate=predicate)
                events.append(e)

        return events     
    
    def make_events_VR(self):
        group = 'Visit_Return'
        name = 'r_VR'
        idx = {}
        events = []
        rate = BASE_RATE
        dim = {'h':self.num_states,
               'j':self.num_states,
               'u':self.num_hidden_char}
        predicate = 'h != j'
        
        # (Note: Do not confuse the h,j indices ReturnScale with that of the return rate matrix)
        # I (Contagious)
        ix = [ 'Contagious[h,j,u]:1', 'VisitReturnScale[h,j,u]:2' ]
        jx = [ 'Contagious[h,h,u]:1', 'VisitReturnScale[h,j,u]:2' ]
        e = Event(g=group, n=name, idx=idx, r=rate, ix=ix, jx=jx, dim=dim, predicate=predicate)
        events.append(e)

        # E (Infected)
        if self.model_exposed:
            ix = [ 'Infected[h,j,k,u]:1', 'VisitReturnScale[h,j,u]:2' ]
            jx = [ 'Infected[h,h,k,u]:1', 'VisitReturnScale[h,j,u]:2' ]
            e = Event(g=group, n=name, idx=idx, r=rate, ix=ix, jx=jx, dim=dim, predicate=predicate)
            events.append(e)

        if self.model_visitor:
            # S (Susceptible)
            ix = [ 'Susceptible[h,j,u]', 'VisitReturnScale[h,j,u]:2' ]
            jx = [ 'Susceptible[h,h,u]', 'VisitReturnScale[h,j,u]:2' ]
            e = Event(g=group, n=name, idx=idx, r=rate, ix=ix, jx=jx, dim=dim, predicate=predicate)
            events.append(e)
            
            if not self.model_recover_approx:
                # R (Recovered)
                ix = [ 'Recovered[h,j,u]', 'VisitReturnScale[h,j,u]:2' ]
                jx = [ 'Recovered[h,h,u]', 'VisitReturnScale[h,j,u]:2' ]
                e = Event(g=group, n=name, idx=idx, r=rate, ix=ix, jx=jx, dim=dim, predicate=predicate)
                events.append(e)
        
        return events
    
#######################
    
    def make_events_tip_sample(self):
        # extant sampling approximation
        # turn off tip sampling reaction at stop_time - dt
        # this will result in extant tips of type Sample at time stop_time
        # which will be approximately the target proportion of lineages extant sampled
        if self.prop_extant_sampled > 0:
            dt = 10**-10
            rate_string = str(BASE_RATE * 1e18) +\
                  ":0,0:" + str(self.params['Stop_time'][0] - dt)
        else:
            rate_string = BASE_RATE * 1e18

        group = 'TipSample'
        name = 'r_tip_sample'
        idx = {}
        events = []
        rate = rate_string
        ix = [ 'Sampled[j,u]:1' ]
        jx = [ 'X']
        dim = {'j':self.num_states,
               'u':self.num_hidden_char}
        e = Event( g=group, n=name, idx=idx, r=rate, ix=ix, jx=jx, dim=dim )
        events.append(e)
        return events
    

#######################

    # some SIR utilities

    def get_json_stats(self, json_dat_fn, reverse_time = False):
        with open(json_dat_fn) as f:
            jsondat = json.load(f)
        actual_sim_time          = masterpy.get_sim_time(jsondat)
        num_sampled              = masterpy.get_popSize_at_t(jsondat, ["SampleCount"], 0)
        total_sampled            = [np.sum([v for k,v in num_sampled.items()])]
        
        # each compartment at X time points
        if 'trajectories' in jsondat.keys():
            compartments = jsondat['trajectories'][0]
        else:
            compartments = jsondat
        nlocs = self.num_states

        # this can be used to simulate future projections (forecasts)
        final_pop_sizes = {'final_Susceptible':np.array(compartments["Susceptible"])[...,-1]}
        final_pop_sizes['final_Contagious']  = np.array(compartments['Contagious'])[...,-1]
        final_pop_sizes['final_Recovered']   = np.array(compartments['Recovered'])[...,-1]

        # num susceptibles CURRENTLY in each location if visitor model, and FROM for migration model
        S0_from    = self.params["Total_S0"]
        S_at_t = masterpy.get_popSize_at_t(jsondat, ["Susceptible"], 
                                           self.params['Time_of_interest'])["Susceptible"]
        if self.model_visitor:
            S0_current = np.sum(self.params["stationary_S"], axis = 0)
        elif self.model_visitor_approx:
            S0_current = np.sum(self.params["stationary_S"], axis = 0)
            S_at_t = np.sum(np.diag(S_at_t) * self.params['VisitStationaryFreqs'], axis = 0)
        else:
            S0_current = S0_from
            S_at_t = masterpy.get_popSize_at_t(jsondat, ["Susceptible"], 
                                           self.params['Time_of_interest'])["Susceptible"]
        
        # R_e(t) effective reproduction number. R_e(t) = S(t) / S(0) x R_0
        R_e = {"R_e" : self.params['R0'] * S_at_t / S0_current}

        # prevalence
        if self.model_exposed:
            final_pop_sizes['final_Infected'] = np.array(compartments['Infected'])[...,-1]
            # exposed is summed over the number of exposed steps, i.e. E1,E2,..,En
            exposed        = np.sum(np.array(compartments['Infected']), axis = 2)
            contagious     = np.array(compartments['Contagious'])
            total_infected = exposed + contagious
            prevalence_at_t      = masterpy.get_combined_popSize_at_t(jsondat, 
                                        ["Infected", "Contagious"], 
                                        self.params['Time_of_interest'])
        else:
            total_infected = np.array(compartments['Contagious'])
            contagious_at_t      = masterpy.get_popSize_at_t(jsondat, 
                                        ["Contagious"], 
                                        self.params['Time_of_interest'])
            prevalence_at_t = {"Prevalence" : contagious_at_t['Contagious']}

        # per capita prevalence (contagious per person CURRENTLY IN location x)
        per_capita_prevalence_at_t = {"per_capita_prevalence_at_t" : 
                                      prevalence_at_t['Prevalence'] /  S0_current}
                                                                #   S0_from}

        # time of peak
        iloc = np.sum(total_infected, axis = (0,2))
        peak_idx = np.array([np.where(iloc[x,:] == np.max(iloc[x,:]))[0][0] for x in range(nlocs)]).flatten()
        time_of_peak_prev = {"time_of_peak_prev": np.array([compartments["t"][x] for x in peak_idx])}
        if reverse_time:
            time_of_peak_prev["time_of_peak_prev"] = time_of_peak_prev["time_of_peak_prev"] - compartments["t"][-1]


        # peak number infected CURRENTLY IN location i per number people TYPICALLY IN location i
        # For migration models this is just the number of residents
        peak_infected = {"peak_infected": np.array([np.sum(total_infected[:,i,0,peak_idx[i]]) for i in range(nlocs)])}
        per_capita_peak_prevalence = {"per_capita_peak_prevalence" : 
                                          peak_infected["peak_infected"] / S0_current}
                                                        #S0_from}

        # cumulative number sampled per resident of a location (FROM)
        num_sampled_per_capita   = {"num_sampled_per_capita" : num_sampled["SampleCount"] / S0_from}
                                                                                        # S0_current}
        # TODO: cumulative proportion infected at time of interest 
        
        return {"actual_sim_time":actual_sim_time, 
                **num_sampled, 
                "total_sampled" :total_sampled, 
                **num_sampled_per_capita,
                **prevalence_at_t,
                **per_capita_prevalence_at_t, 
                **final_pop_sizes,
                **R_e,
                **time_of_peak_prev,
                **peak_infected,
                **per_capita_peak_prevalence}
    


    # def get_nexus_tree_stats(self, nexus_tree_string, types, rxns, locations):

    #     type_count_dict = {}
    #     for k in xargs:
    #         type_count_dict[k] = nexus_tree_string.count('type=\"' + k +'\"')

    #     num_tips = nexus_tree_string.count('type="Sampled"')

    # def get_json_stats(self, json_dat_fn):
    #     with open(json_dat_fn) as f:
    #         jsondat = json.load(f)
    #     actual_sim_time          = masterpy.get_sim_time(jsondat)
    #     num_sampled              = masterpy.get_popSize_at_t(jsondat, ["SampleCount"], 0)
    #     num_sampled_per_capita   = {"num_sampled_per_capita_" +\
    #                                 str(i):num_sampled['num_SampleCount_in_loc_' +\
    #                                 str(i)]/self.params["Total_S0"][i]
    #                                 for i in range(len(num_sampled))}
    #     if self.model_exposed:
    #         prevalence_at_t      = masterpy.get_combined_popSize_at_t(jsondat, 
    #                                     ["Infected", "Contagious"], 
    #                                     self.params['Time_of_interest'])
    #     else:
    #         prevalence_at_t      = masterpy.get_popSize_at_t(jsondat, ["Contagious"], 
    #                                     self.params['Time_of_interest'])
            
    #     per_capita_prevalence_at_t = {"per_capita_prevalence_at_t_" + str(i) : \
    #                                   prevalence_at_t['Prevalence_' + str(i)] / \
    #                                     self.params["Total_S0"][i]
    #                                 for i in range(self.num_states)}

    #     return {"actual_sim_time":actual_sim_time, **num_sampled, 
    #             **num_sampled_per_capita, **prevalence_at_t,
    #             **per_capita_prevalence_at_t}





#######################

    # TODO: probably safe to remove
    
    # # Approximated Visitor Model

    # def make_events_VD_approx(self):
    #     group = 'Visit_Depart'
    #     name = 'r_VD'
    #     idx = {}
    #     events = []
    #     rate = BASE_RATE
    #     dim = {'h':self.num_states,
    #            'j':self.num_states,
    #            'u':self.num_hidden_char}
    #     predicate = 'h != j'

    #     # S (Susceptible)
    #     # ... ignored under approximation
        
    #     # I (Contagious)
    #     ix = [ 'Contagious[h,h,u]:1', 'VisitDepartScale[h,j,u]:2' ]
    #     jx = [ 'Contagious[h,j,u]:1', 'VisitDepartScale[h,j,u]:2' ]
    #     e = Event(g=group, n=name, idx=idx, r=rate, ix=ix, jx=jx, dim=dim, predicate=predicate)
    #     events.append(e)
        
    #     # R (Recovered)
    #     # ... ignored under approximation

    #     # E (Infected)
    #     if self.model_exposed:
    #         ix = [ 'Infected[h,h,k,u]:1', 'VisitDepartScale[h,j,u]:2' ]
    #         jx = [ 'Infected[h,j,k,u]:1', 'VisitDepartScale[h,j,u]:2' ]
    #         e = Event(g=group, n=name, idx=idx, r=rate, ix=ix, jx=jx, dim=dim, predicate=predicate)
    #         events.append(e)

    #     return events     
    
    # def make_events_VR_approx(self):
    #     group = 'Visit_Return'
    #     name = 'r_VR'
    #     idx = {}
    #     events = []
    #     rate = BASE_RATE
    #     dim = {'h':self.num_states,
    #            'j':self.num_states,
    #            'u':self.num_hidden_char}
    #     predicate = 'h != j'
        
    #     # S (Susceptible)
    #     # ... ignored under approximation
        
    #     # I (Contagious)
    #     ix = [ 'Contagious[h,j,u]:1', 'VisitReturnScale[j,h,u]:2' ]
    #     jx = [ 'Contagious[h,h,u]:1', 'VisitReturnScale[j,h,u]:2' ]
    #     e = Event(g=group, n=name, idx=idx, r=rate, ix=ix, jx=jx, dim=dim, predicate=predicate)
    #     events.append(e)
        
    #     # R (Recovered)
    #     # ... ignored under approximation
        
    #     # E (Infected)
    #     if self.model_exposed:
    #         ix = [ 'Infected[h,j,k,u]:1', 'VisitReturnScale[j,h,u]:2' ]
    #         jx = [ 'Infected[h,h,k,u]:1', 'VisitReturnScale[j,h,u]:2' ]
    #         e = Event(g=group, n=name, idx=idx, r=rate, ix=ix, jx=jx, dim=dim, predicate=predicate)
    #         events.append(e)

    #     return events
    
