import numpy as np
import utils
import pickle
import os

# Define folder/dataset:
datafile = 'WASP19/w19_140322.pkl' 
# Define LD laws, comparison stars to use:
ld_law_white = 'squareroot'
comps = [0,1,2,3,4,6]
# Priors to be used. First period and its standard deviation:
Pmean,Psd = 0.788839316,0.000000017
# Same for a/Rstar:
amean,asd =  3.50,0.1
# Rp/Rs:
pmean,psd = 0.14,0.01
# Impact parameter:
bmean,bsd = 0.6,0.1
# Time of transit center:
t0mean,t0sd = 2456739.547178,0.001
# Define if fixed eccentricity will be used:
fixed_eccentricity = False
# Eccentricity and omega. If fixed_eccentricity = True, eccmean and omegamean will be the 
# fixed parameters for these orbital elements of the orbit:
eccmean,eccsd = 0.0046,0.0044 
omegamean,omegasd = 3.0,70.0

######################################
target,pfilename = datafile.split('/')
out_folder = 'outputs/'+datafile.split('.')[0]

if not os.path.exists('outputs'):
    os.mkdir('outputs')

if not os.path.exists('outputs/'+target):
    os.mkdir('outputs/'+target)

if not os.path.exists(out_folder):
    os.mkdir(out_folder)
    data = pickle.load(open(datafile,'rb'))
    if not os.path.exists(out_folder+'/white-light'):
        os.mkdir(out_folder+'/white-light')
        # 1. Save external parameters:
        out_eparam = open(out_folder+'/eparams.dat','w')
        # Get median of FWHM, background flux, accross all wavelengths, and trace position of zero point.
        # First, find chips-names of target:
        names = []
        for name in data['fwhm'].keys():
            if target in name:
                names.append(name)
        if len(names) == 1:
            Xfwhm = data['fwhm'][names[0]]
            Xsky = data['sky'][names[0]]
        else:
            Xfwhm = np.hstack((data['fwhm'][names[0]],data['fwhm'][names[1]]))
            Xsky = np.hstack((data['sky'][names[0]],data['sky'][names[1]]))
        fwhm = np.zeros(Xfwhm.shape[0])
        sky = np.zeros(Xfwhm.shape[0])
        trace = np.zeros(Xfwhm.shape[0])
        for i in range(len(fwhm)):
            idx = np.where(Xfwhm[i,:]!=0)[0]
            fwhm[i] = np.median(Xfwhm[i,idx])
            idx = np.where(Xsky[i,:]!=0)[0]
            sky[i] = np.median(Xsky[i,idx])
            trace[i] = np.polyval(data['traces'][target][i],Xfwhm.shape[1]/2)
        print 'Saving eparams...'
        # Save external parameters:
        out_eparam.write('#Times \t                 Airmass \t Delta Wav \t FWHM \t        Sky Flux \t      Trace Center \n')
        for i in range(len(data['t'])):
            out_eparam.write('{0:.10f} \t {1:.10f} \t {2:.10f} \t {3:.10f} \t {4:.10f} \t {5:.10f} \n'.format(data['t'][i],\
                              data['Z'][i],data['deltas'][target+'_final'][i],fwhm[i],sky[i],trace[i]))
        out_eparam.close()
  
        # 2. Save (mean-substracted) target and comparison lightcurves (in magnitude-space):
        lcout = open(out_folder+'/white-light/lc.dat','w')
        lccompout = open(out_folder+'/white-light/comps.dat','w')
        for i in range(len(data['t'])):
            lcout.write('{0:.10f} {1:.10f} 0\n'.format(data['t'][i],-2.51*np.log10(data['oLC'][i])-np.median(-2.51*np.log10(data['oLC']))))
            for j in range(len(comps)): 
                if j != len(comps)-1:
                    lccompout.write('{0:.10f} \t'.format(-2.51*np.log10(data['cLC'][i,comps[j]]) - np.median(-2.51*np.log10(data['cLC'][:,comps[j]]))))
                else:
                    lccompout.write('{0:.10f}\n'.format(-2.51*np.log10(data['cLC'][i,comps[j]]) - np.median(-2.51*np.log10(data['cLC'][:,comps[j]]))))
        lcout.close()
        lccompout.close() 

# 3. If not already done, run code for all PCAs, extract best-fit parameters, model-average them, save them. For this,
# first check maximum number of samples sampled from posterior from all the fits:
if not os.path.exists(out_folder+'/white-light/BMA_posteriors.pkl'):
    lnZ = np.zeros(len(comps))
    nmin = np.inf
    for i in range(1,len(comps)+1): 
	if not os.path.exists(out_folder+'/white-light/PCA_'+str(i)):
            if not fixed_eccentricity:
                ecc_arg = ' --fixed_ecc'
            else:
                ecc_arg = ''
	    os.system('python GPTransitDetrendWL.py -outfolder '+out_folder+'/white-light/ -compfile '+out_folder+\
			  '/white-light/comps.dat -lcfile '+out_folder+'/white-light/lc.dat -eparamfile '+out_folder+\
			  '/eparams.dat -ldlaw '+ld_law_white+' -Pmean '+str(Pmean)+' -Psd '+str(Psd)+' -amean '+str(amean)+' -asd '+str(asd)+' '+\
			  '-pmean '+str(pmean)+' -psd '+str(psd)+' -bmean '+str(bmean)+' -bsd '+str(bsd)+' -t0mean '+str(t0mean)+' -t0sd '+str(t0sd)+' -eccmean '+str(eccmean)+' '+\
			  '-eccsd '+str(eccsd)+' -omegamean '+str(omegamean)+' -omegasd '+str(omegasd)+' --PCA -pctouse '+str(i)+ecc_arg)
	    os.mkdir(out_folder+'/white-light/PCA_'+str(i))
	    os.system('mv '+out_folder+'/white-light/out* '+out_folder+'/white-light/PCA_'+str(i)+'/.')
	    os.system('mv '+out_folder+'/white-light/*.pkl '+out_folder+'/white-light/PCA_'+str(i)+'/.')
	    os.system('mv detrended_lc.dat '+out_folder+'/white-light/PCA_'+str(i)+'/.')
	fin = open(out_folder+'/white-light/PCA_'+str(i)+'/posteriors_trend_george.pkl','r')
	posteriors = pickle.load(fin)
	if len(posteriors['posterior_samples']['p'])<nmin:
	    nmin = len(posteriors['posterior_samples']['p'])
	lnZ[i-1] = posteriors['lnZ']
	fin.close()
    # Calculate posterior probabilities of the models from the Bayes Factors:
    lnZ = lnZ - np.max(lnZ)
    Z = np.exp(lnZ)
    Pmodels = Z/np.sum(Z)
    # Prepare array that saves outputs:
    periods = np.array([])
    aR = np.array([])
    p = np.array([])
    b = np.array([])
    t0 = np.array([])
    ecc = np.array([])
    omega = np.array([])
    q1 = np.array([])
    q2 = np.array([])
    jitter = np.array([])
    max_GPvariance = np.array([])
    alpha0 = np.array([])
    alpha1 = np.array([])
    alpha2 = np.array([])
    alpha3 = np.array([])
    alpha4 = np.array([])
    alpha5 = np.array([])
    mmean = np.array([])
    # With the number at hand, extract draws from the  posteriors with a fraction equal to the posterior probabilities to perform the 
    # model averaging scheme:
    for i in range(1,len(comps)+1):
	fin = open(out_folder+'/white-light/PCA_'+str(i)+'/posteriors_trend_george.pkl','r')
	posteriors = pickle.load(fin)
	fin.close()
	nextract = int(Pmodels[i-1]*nmin)
	idx_extract = np.random.choice(np.arange(len(posteriors['posterior_samples']['P'])),nextract,replace=False)
	# Extract transit parameters:
	periods = np.append(periods,posteriors['posterior_samples']['P'][idx_extract])
	aR = np.append(aR,posteriors['posterior_samples']['a'][idx_extract])
	p = np.append(p,posteriors['posterior_samples']['p'][idx_extract])
	b = np.append(b,posteriors['posterior_samples']['b'][idx_extract])
	t0 = np.append(t0,posteriors['posterior_samples']['t0'][idx_extract])
        if not fixed_eccentricity:
	    ecc = np.append(ecc,posteriors['posterior_samples']['ecc'][idx_extract])
	    omega = np.append(omega,posteriors['posterior_samples']['omega'][idx_extract])
	q1 = np.append(q1,posteriors['posterior_samples']['q1'][idx_extract])
	q2 = np.append(q2,posteriors['posterior_samples']['q2'][idx_extract])
	# Note bayesian average posterior jitter saved is in mmag (MultiNest+george sample the log-variance, not the log-sigma):
	jitter = np.append(jitter,np.sqrt(np.exp(posteriors['posterior_samples']['ljitter'][idx_extract])))
	# Mean lightcurve in magnitude units:
	mmean = np.append(mmean,posteriors['posterior_samples']['mmean'][idx_extract])
	# Max GP variance:
	max_GPvariance = np.append(max_GPvariance,posteriors['posterior_samples']['max_var'][idx_extract])
	# Alphas:
	alpha0 = np.append(alpha0,posteriors['posterior_samples']['alpha0'][idx_extract])
	alpha1 = np.append(alpha1,posteriors['posterior_samples']['alpha1'][idx_extract])
	alpha2 = np.append(alpha2,posteriors['posterior_samples']['alpha2'][idx_extract])
	alpha3 = np.append(alpha3,posteriors['posterior_samples']['alpha3'][idx_extract])
	alpha4 = np.append(alpha4,posteriors['posterior_samples']['alpha4'][idx_extract])
	alpha5 = np.append(alpha5,posteriors['posterior_samples']['alpha5'][idx_extract])

    # Now save final BMA posteriors:
    out = {}
    out['P'] = periods
    out['aR'] = aR
    out['p'] = p
    out['b'] = b
    out['inc'] = np.arccos(b/aR)*180./np.pi
    out['t0'] = t0
    if not fixed_eccentricity:
        out['ecc'] = ecc 
        out['omega'] = omega
    out['jitter'] = jitter
    out['q1'] = q1
    out['q2'] = q2
    out['mmean'] = mmean
    out['max_var'] = max_GPvariance
    out['alpha0'] = alpha0
    out['alpha1'] = alpha1
    out['alpha2'] = alpha2
    out['alpha3'] = alpha3
    out['alpha4'] = alpha4
    out['alpha5'] = alpha5
    pickle.dump(out,open(out_folder+'/white-light/BMA_posteriors.pkl','wb'))
    fout = open(out_folder+'/white-light/results.dat','w')
    fout.write('# Variable \t Value \t SigmaUp \t SigmaDown\n')
    for variable in out.keys():
        v,vup,vdown = utils.get_quantiles(out[variable])
        print variable
        fout.write(variable+' \t {0:.10f} \t {1:.10f} \t {2:.10f}\n'.format(v,vup-v,v-vdown))
    fout.close()
else:
    out = pickle.load(open(out_folder+'/white-light/BMA_posteriors.pkl','rb'))