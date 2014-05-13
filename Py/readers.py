#readers for avsc

import os, csv, json
import pandas as pd
import random

#Read json data from Parameter file, for now, just need data_dir
JSONDC=json.JSONDecoder()
PARS=JSONDC.decode(open('../PARS.json','rU').read())

def data_files(name=None):
    ''' returns a dictionary with full path to data files. Or if name is given, just
        return that one'''
    data_dir=PARS['data_dir']
    if data_dir[-1] != '/' : data_dir+='/'
    
    files= {"offers": data_dir+"offers.csv",
            "history": data_dir+"trainHistory.csv",
            "history_test": data_dir+"testHistory.csv",
            "sample_sub": data_dir+"sampleSubmission.csv",
            "transactions": data_dir+"transactions.csv",
            "leaderboard":data_dir+"leaderboard_May12.csv"
            }	
    for key, file in files.iteritems(): assert(os.path.exists(file))
    if name : return files[name]
    return files  

def read_files_pandas(name):
    '''read data into pandas data frame'''
    filename=data_files(name)
    return pd.read_csv(filename)

def stream_data(name,frac=1.0):
    '''Return generator/stream to data as dictionaries
       If frac < 0, it will sample a random fraction of customers 
    '''
    #TODO: handle gzip?
    filename=data_files(name)
    for line in csv.DictReader(open(filename,'rU')):
        if 'id' in line:
            if hash_frac(line['id'],frac=frac) : yield line
        else:
            yield line

def hash_frac(input,frac=1.0):
    '''Useful utility for sampling some fraction of things deterministically'''
    if frac == 1.0 : return True
    if frac == 0.0 : return False
    h=abs(hash(str(input)))
    random.seed(h)
    r=random.random()
    return r < frac

def make_customer_offer_lookup(frac=1.0):
    '''Make a dictionary keyed by cust_id with their offer from history and offer info (joined in)'''
    extra={'n_tot':0,'n_category':0,'n_brand':0,'n_chain':0,'n_company':0}
    offer_history=stream_data('history',frac=frac)
    offer_info=stream_data('offers',frac=frac)
    offer_dict={}
    for offer in offer_info:
        offer_id=offer['offer']
        offer_dict[offer_id]=offer
    offer_history_dict={}
    for offer in offer_history:
        cust_id=offer['id']
        #join in offer info
        offer_id=offer['offer']
        info=offer_dict[offer_id]
        offer.update(info)
        offer.update(extra)
        offer_history_dict[cust_id]=offer
    return offer_history_dict
    
def hunt_for_features(offer_dict,frac=1.0,prompt=True):
    #TODO: modifies in place, could be dangerous so change this
    trans=stream_data('transactions',frac=frac)
    bastards=set()
    ids=set()
    for ntran,tran in enumerate(trans):
        if ntran % 1000 == 0: 
            print 'ntran: %s'%ntran
            print "%s bastards"%len(bastards)
            print "%s unique shopper"%len(ids)
        id=tran['id']
        ids.add(id)
        if id in offer_dict:
            #all should have an offer
            offer=offer_dict[id]
            assert(offer['offerdate']> tran['date'])
            
            offer['n_tot']+=1
            if tran['category'] == offer['category'] : offer['n_category']+=1
            if tran['chain'] == offer['chain'] : offer['n_chain']+=1
            if tran['brand'] == offer['brand'] : offer['n_brand']+=1
            if tran['company'] == offer['company'] : offer['n_company']+=1
                 
            assert(offer['offerdate']> tran['date'])
        else :
            bastards.add(id)
            if id not in bastards:
                print 'ntran: %s'%ntran
                print 'bastard , id=%s',id
                print "%s bastards"%len(bastards)
                print "%s unique shopper"%len(ids)
        if prompt:
            ok=raw_input("Ok")
            if ok == 'q' : 
                break
            if ok == 'p' :
                print offer,'\n'
                print tran
            if ok == 'n' :
                prompt=False
                
    print "%s bastards"%len(bastards)
    print "%s unique shopper"%len(ids)
    
def make_small_files_by_cust(name='transactions',ngroups=50,nmax=None):
    '''Make a smaller file keeping only some customers but all data for those customers''' 
    if ngroups > 100:
        print 'ngroups must be <=100'
        return 'done'
    binwidth=1.0/ngroups
     
    #TODO: do with 'with', check for errors
    infile_name=data_files(name)
    infile=csv.DictReader(open(infile_name,'rU'))
    first=infile.next()
    field_names=first.keys()
    infile=csv.DictReader(open(infile_name,'rU'))
    
    file_names=[]
    for i in xrange(ngroups):
        file_names.append(infile_name.replace('.csv','_'+str(i)+'.csv'))
    print file_names
    
    files=[]
    for i in xrange(ngroups):
        #open all the files at same time, might be a better way, check with ulimit -n
        #will silently cloobber whatever is there so be careful
        file_name=file_names[i]
        file_i=csv.DictWriter(open(file_name,'w'),field_names)
        file_i.writeheader()
        files.append(file_i)
        
    #now all file handles are open
    nrow=0
    for row in infile:
        if nrow % 1000 == 0: print "nrow: %s"%nrow 
        nrow+=1
        #hash on customer id
        hash_integer=abs(hash(str(row['id'])))
        random.seed(hash_integer)
        r=random.random()
        group_number=int(r/binwidth)
        file_i=files[group_number]
        file_i.writerow(row)
        if nmax :
            if nrow > nmax: 
                break
    print 'done'
  
def add_to_history_files(name='history'):
    #Not needed, keep anyway
    #kinda awkward, is there a better way to get header
    s=stream_data(name)
    first=s.next()
    field_names=first.keys()
    #start over
    s=stream_data(name)
    field_names.append('repeat_shopper')
    
    outfile_name=data_files(name).replace('.csv','_mod.csv')
    outfile=csv.DictWriter(open(outfile_name,'w',),field_names)
    outfile.writeheader()
    for line in s:
        n_repeat=int(line['repeattrips'])
        if n_repeat >=2 : 
            line['repeat_shopper']='Yes'
        else:
            line['repeat_shopper']='No'
        outfile.writerow(line)
    
        
               
    




