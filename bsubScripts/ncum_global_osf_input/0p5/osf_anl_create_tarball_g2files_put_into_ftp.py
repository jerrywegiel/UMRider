#!/usr/bin/env python

## This is call back script which will be executed after created the grib2 files.
## 
## OSF Model Input requires analysis of 06, 12, 18-hours from 
## yesterday and 00-hours from today date. All 6-hourly forecasts from
## today date.
## 
## While creating tar ball, all files must be in present directory, so that
## when user extract it, will produce only files instead of entire paths!
##
## And finally putting into their ftp server.
##
## Arulalan.T
## 04-Mar-2016.

import os, subprocess, datetime, getopt, sys, glob

pbzip2 = '/gpfs1/home/Libs/GNU/ZIPUTIL/pbzip2'
pigz = '/gpfs1/home/Libs/GNU/ZIPUTIL/pigz'

def createTarBalls(path, oftype, today, utc, stephr=6):
    
    cdir = os.getcwd()
    os.chdir(path)
    tarpath = os.path.abspath('../TarFiles')
    if not os.path.exists(tarpath): os.makedirs(tarpath)
    
    if oftype == 'analysis':    
        anal_ftemp = 'anal*%s*%s*.grb'
        tDay = datetime.datetime.strptime(today, "%Y%m%d")
        lag1 = datetime.timedelta(days=1)
        yDay = (tDay - lag1).strftime('%Y%m%d')
        lag4 = datetime.timedelta(days=4)
        y4Day = (tDay - lag4).strftime('%Y%m%d')
        # get past 11th day timestamp
        y11Day = (tDay - datetime.timedelta(days=11)).strftime('%Y%m%d')
        # get yesterday's analysis files from 06hr onwards
        yanal = [anal_ftemp % (str(hr).zfill(2), yDay) for hr in range(6, 24, stephr)]
        # get today's analysis 00 and 03 hr
        tanal_files = [anal_ftemp % (str(hr).zfill(2), today) for hr in range(0, 6, stephr)]
        # store available yesterday anal_files
        yanal_files = []
        for yf in yanal:
            # move yesterday's analysis files to today's directory        
            wildcard_anlfile = '../%s/%s' % (yDay, yf)
            print "wildcard_anlfile = ", wildcard_anlfile
            if not glob.glob(wildcard_anlfile): continue
            cmd = 'cp %s .' % wildcard_anlfile
            print cmd
            subprocess.call(cmd, shell=True)
            yanal_files.append(yf)
        # end of for yf in yanal:
        
        print "currnet path : ", os.getcwd()
        # normal "$ tar cvjf fcst_20160223.tar.bz2 *fcst*grb2" cmd takes 6 minutes 43 seconds.
        #
        # where as in parallel bz2, "$ tar -c *fcst*grb2 | pbzip2 -v -c -f -p32 -m500 > fcst_20160223_parallel.tar.bz2" cmd takes only just 23 seconds alone, with 32 processors and 500MB RAM memory.
        #
        # create analysis files tar file in parallel # -m500 need to be include for pbzip2
        anal_files = '  '.join(['./'+af for af in yanal_files + tanal_files])  
        cmd = "tar -c  %s | %s -v  -c -f -p32 > %s/anal_glb_%s.tar.gz" % (anal_files, pigz, '../TarFiles', today)
        print cmd
        subprocess.call(cmd, shell=True)
        
        if yanal_files:
            # delete yesterday analysis files copy from today directory
            yesterday_anal_files = '  '.join(['./'+af for af in yanal_files])  
            cmd = "rm -rf %s" % yesterday_anal_files
            print cmd
            subprocess.call(cmd, shell=True)
        # end of if yanal_files:        
        
        # do scp the anal tar files to ftp_server and nkn_server
        cmd = 'ssh ncmlogin3 "scp -p %s/anal_glb_%s.tar.gz  %s:/data/ftp/pub/outgoing/NCUM_OSF/0.5/"' % (tarpath, today, ftp_server)
        print cmd
        subprocess.call(cmd, shell=True)
        cmd = 'ssh ncmlogin3 "scp -p %s/anal_glb_%s.tar.gz  %s:NCUM/osf/0.5/"' % (tarpath, today, nkn_server)
        print cmd
        subprocess.call(cmd, shell=True)
        
        # remove past 11th day tar ball from ftp_server 
        cmd = 'ssh ncmlogin3 "ssh %s rm -rf /data/ftp/pub/outgoing/NCUM_OSF/0.5/*%s*tar.gz"' % (ftp_server, y11Day)
        print cmd
        try:
            subprocess.call(cmd, shell=True)
        except Exception as e:
            print "past 11th day tar ball has been removed from ftp_server, already", e
        # remove past 11th day tar ball from nkn_server 
        cmd = 'ssh ncmlogin3 "ssh %s rm -rf /home/incois/NCUM/osf/0.5/*%s*tar.gz"' % (nkn_server, y11Day)
        print cmd
        try:
            subprocess.call(cmd, shell=True)
        except Exception as e:
            print "past 11th day tar ball has been removed from nkn_server, already", e
        
    elif oftype == 'forecast':    
        # create forecast files tar file in parallel  # -m500 need to be include for pbzip2
        cmd = "tar -c ./fcst*%s*.grb | %s  -v  -c -f -p32 > %s/fcst_glb_%s.tar.gz" % (today, pigz, '../TarFiles', today)
        print cmd
        subprocess.call(cmd, shell=True)        
                    
        # delete today's forecasts files, after tar ball has been created!    
        cmd = "rm -rf fcst*%s*.grb" % today
        print cmd
        subprocess.call(cmd, shell=True)
    
        # do scp the fcst tar files to ftp_server and nkn_server
        cmd = 'ssh ncmlogin3 "scp -p %s/fcst_glb_%s.tar.gz  %s:/data/ftp/pub/outgoing/NCUM_OSF/0.5/"' % (tarpath, today, ftp_server)
        print cmd
        subprocess.call(cmd, shell=True)
        cmd = 'ssh ncmlogin3 "scp -p %s/fcst_glb_%s.tar.gz  %s:NCUM/osf/0.5/"' % (tarpath, today, nkn_server)
        print cmd
        subprocess.call(cmd, shell=True)        
    # end of if oftype == 'analysis':    
    
    # remove before 3 days directory, neither today nor yesterday directory!!!
    y4DayPath = os.path.join(path, '../%s' % y4Day)
    if os.path.exists(y4DayPath):    
        cmd = "rm -rf %s" % y4DayPath
        print cmd
        subprocess.call(cmd, shell=True)
    # end of if os.path.exists(y4DayPath):         
    
    os.chdir(cdir)  
# end of def createTarBalls(path, today, ...):

if __name__ == '__main__':

    nkn_server="incois@nkn"
    ftp_server="prod@ftp"
    date = None
    outpath = None
    oftype = None
    utc = None
    helpmsg = 'osf_create_tarball_g2files_put_into_ftp.py --date=20160302 --outpath=path --oftype=analysis --utc=00'
    try:
        opts, args = getopt.getopt(sys.argv[1:], "d:o:t:z:", ["date=","outpath=", "oftype=", "utc="])
    except getopt.GetoptError:
        print helpmsg
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print helpmsg
            sys.exit()
        elif opt in ("-d", "--date"):
            date = arg
        elif opt in ("-o", "--outpath"):
            outpath = arg 
        elif opt in ("-t", "--oftype"):
            oftype = arg
        elif opt in ("-z", "--utc"):
            utc = arg
    # end of for opt, arg in opts:
    
    # create tar balls only if utc is 00, otherwise skip it!    
    if oftype == 'analysis' and utc == '00': 
        # pass the arg to function  
        createTarBalls(outpath, oftype, date, utc, stephr=6)    
    # end of if oftype == 'forecast' and utc == '00': 
