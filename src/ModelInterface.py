#!/usr/bin/env python
# coding: utf-8

# **ModelInterface: extension of Model class interfaced by HistStruct**  
# 
# To do: more detailed documentation (currently under a little time pressure...)
# To do: more argument and exception checking throughout the whole class

### imports

# external modules
import os
import sys
import pickle
import zipfile
import glob
#import shutil
import copy
#import math
#import pandas as pd
import numpy as np
#import matplotlib.pyplot as plt
import importlib

# local modules
from Model import Model
sys.path.append('classifiers')
from HistogramClassifier import HistogramClassifier


class ModelInterface(Model):
    
    def __init__( self, histnames ):
        super( ModelInterface, self ).__init__(histnames)
        # (setting attributes histnames, ndims, classifiers, and fitter)
        self.scores = {}
        self.globalscores = {}
        self.setnames = []
        self.default_set_name = 'default'
        self.add_setname( self.default_set_name )
        
    def __str__( self ):
        ### get a printable representation of a ModelInterface
        info = '=== ModelInterface === \n'
        if len(self.histnames)==0:
            info += '  (not initialized)'
        else:
            # classifiers
            info += '- classifiers: \n'
            for histname in self.histnames:
                info += '    -- {}: '.format(histname)
                if histname in self.classifiers.keys():
                    info += '{} \n'.format(type(self.classifiers[histname]))
                else: info += '(not initialized) \n'
            # fitter
            info += '- fitter: '
            if self.fitter is None: info += '(not initialized) \n'
            else: info += '{} \n'.format(type(self.fitter))
            # scores
            for setname in self.setnames:
                info += '- set "{}" \n'.format(setname)
                for histname in self.histnames:
                    info += '  -- scores for {}: '.format(histname)
                    if histname in self.scores[setname].keys(): info += 'initialized \n'
                    else: info += '(not initialized) \n'
                info += '  -- global scores: '
                if len(self.globalscores[setname])>0: info += 'initialized \n'
                else: info += '(not initialized) \n'
        return info
        
    def add_setname( self, setname ):
        ### initialize empty scores for extended set
        # input arguments:
        # - setname: name of extended set
        if setname in self.setnames:
            print('WARNING in ModelInterface.add_setname: set "{}"'.format(setname)
                  +' is already present in the ModelInterface')
            return
        self.setnames.append( setname )
        self.scores[setname] = {}
        self.globalscores[setname] = []
    
    def evaluate_store_classifier( self, histname, histograms, setname=None ):
        ### same as Model.evaluate_classifier but store the result internally
        # input arguments:
        # - histname: histogram name for which to evaluate the classifier
        # - histograms: the histograms for evaluation, np array of shape (nhistograms,nbins)
        # - setname: name of extended set (default: standard set)
        if setname is None: setname = self.default_set_name
        scores = super( ModelInterface, self ).evaluate_classifier(histname, histograms)
        self.scores[setname][histname] = scores
        
    def evaluate_store_classifiers( self, histograms, setname=None ):
        ### same as Model.evaluate_classifiers but store the result internally
        # input arguments:
        # - histograms: dict of histnames to histogram arrays (shape (nhistograms,nbins))
        # - setname: name of extended set (default: standard set)
        if setname is None: setname = self.default_set_name
        scores = super( ModelInterface, self ).evaluate_classifiers(histograms)
        self.scores[setname] = scores
        
    def evaluate_store_fitter( self, points, setname=None, verbose=False ):
        ### same as Model.evaluate_fitter but store the result internally
        # input arguments:
        # - points: dict matching histnames to scores (np array of shape (nhistograms))
        if setname is None: setname = self.default_set_name
        self.globalscores[setname] = super( ModelInterface, self ).evaluate_fitter(points, verbose=verbose)
        
    def get_scores( self, setname=None, histname=None ):
        if setname is None: setname = self.default_set_name
        if not setname in self.setnames:
            raise Exception('ERROR in ModelInterface.get_scores: requested setname {}'.format(setname)
                           +' but it is not in the current ModelInterface.')
        if( (histname is not None) and (histname not in self.histnames) ):
            raise Exception('ERROR in ModelInterface.get_scores: requested histname {}'.format(histname)
                           +' but it is not in the current ModelInterface.')
        if histname is None:
            return self.scores[setname]
        else: return self.scores[setname][histname]
        
    def get_globalscores( self, setname=None ):
        if setname is None: setname = self.default_set_name
        if not setname in self.setnames:
            raise Exception('ERROR in ModelInterface.get_scores: requested setname {}'.format(setname)
                           +' but it is not in the current ModelInterface.')
        return self.globalscores[setname]
        
    def save( self, path, save_classifiers=True, save_fitter=True ):
        ### save a ModelInterface object to a pkl file
        # input arguments:
        # - path where to store the file
        # - save_classifiers: a boolean whether to include the classifiers (alternative: only scores)
        # - save_fitter: a boolean whether to include the fitter (alternative: only scores)
        pklpath = os.path.splitext(path)[0]+'.pkl'
        zippath = os.path.splitext(path)[0]+'.zip'
        cpath = os.path.splitext(path)[0]+'_classifiers_storage'
        fpath = os.path.splitext(path)[0]+'_fitter_storage'
        rootpath = os.path.dirname(path)
        zipcontents = {}        
        # remove the classifiers and fitter from the object
        classifiers = dict(self.classifiers)
        self.classifiers = {}
        fitter = copy.deepcopy(self.fitter)
        self.fitter = None
        # pickle the rest
        with open(pklpath,'wb') as f:
            pickle.dump(self,f)
        zipcontents[pklpath] = os.path.relpath(pklpath, start=rootpath)
        # restore the classifiers and fitter
        self.classifiers = classifiers
        self.fitter = fitter
        # case where classifiers should be stored
        if( len(self.classifiers.keys())!=0 and save_classifiers ):
            # save the classifiers
            for histname,classifier in self.classifiers.items():
                classifier.save( os.path.join(cpath,histname) )
            # get all files to store in the zip file
            for root, dirs, files in os.walk(cpath):
                for name in files:
                    thispath = os.path.join(root, name)
                    zipcontents[thispath] = os.path.relpath(thispath, start=rootpath)
        # case where fitter should be stored
        if( self.fitter is not None and save_fitter ):
            # save the fitter
            self.fitter.save( os.path.join(fpath,'fitter') )
            # get all files to store in the zip file
            for root, dirs, files in os.walk(fpath):
                for name in files:
                    thispath = os.path.join(root, name)
                    zipcontents[thispath] = os.path.relpath(thispath, start=rootpath)
        # put everything in a zip file
        with zipfile.ZipFile( zippath, 'w' ) as zipf:
            for f, fname in zipcontents.items(): zipf.write(f, fname)
        # remove individual files
        for f in zipcontents: os.system('rm {}'.format(f))
        if os.path.exists(cpath): os.system('rm -r {}'.format(cpath))
        if os.path.exists(fpath): os.system('rm -r {}'.format(fpath))
            
    @classmethod
    def load( self, path, load_classifiers=True, load_fitter=True, verbose=False ):
        ### load a ModelInterface object
        # input arguments:
        # - path to a zip file containing a ModelInterface object
        # - load_classifiers: a boolean whether to load the classifiers if present
        # - load_fitter: a boolean whether to load the fitter if present
        # - verbose: boolean whether to print some information
        zippath = os.path.splitext(path)[0]+'.zip'
        unzippath = os.path.splitext(path)[0]+'_unzipped'
        basename = os.path.splitext(os.path.basename(zippath))[0]
        pklbasename = basename+'.pkl'
        cbasename = basename+'_classifiers_storage'
        fbasename = basename+'_fitter_storage'
        zipcontents = []
        # extract the zip file
        with zipfile.ZipFile( zippath, 'r' ) as zipf:
            zipcontents = zipf.namelist()
            zipf.extractall( path=unzippath )
        with open(os.path.join(unzippath,pklbasename),'rb') as f:
            obj = pickle.load(f)
        if( load_classifiers ):
            if len(zipcontents)==1:
                print('WARNING: requested to load classifiers, '
                      +'but this stored ModelInterface object does not seem to contain any.')
            else:
                for histname in obj.histnames:
                    obj.classifiers[histname] = obj.classifier_types[histname].load( 
                        os.path.join(unzippath,cbasename,histname) )
        if( load_fitter ):
            if not os.path.exists(os.path.join(unzippath,fbasename)):
                print('WARNING: requested to load fitter, '
                      +'but this stored ModelInterface object does not seem to contain any.')
            else:
                obj.fitter = obj.fitter_type.load( os.path.join(unzippath,fbasename,'fitter') )
        # remove individual files
        if os.path.exists(unzippath): os.system('rm -r {}'.format(unzippath))
        if verbose:
            print('Loaded a ModelInterface object with following properties:')
            print(obj)
        return obj