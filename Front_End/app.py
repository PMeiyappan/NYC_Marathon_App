from __future__ import print_function # In python 2.7


import argparse
import csv
import os
import datetime
import re
import sys
import math
import time
import tempfile
from StringIO import StringIO
import json
import logging

import sklearn.preprocessing
from sklearn.externals import joblib
from sklearn.preprocessing import PolynomialFeatures
import numpy as np
from numpy import genfromtxt
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

from flask import Response
from flask import Flask, render_template, request

app = Flask( __name__)

import parser


def generate_series(TFT, Age, Experience, Gender):


    if(Gender == 'Male'):
        Gender=0
    else:
        Gender=1
    
    
    coeff=genfromtxt('./ML_Data/NYC_Marathon_FMNL_model_coefficients.csv', delimiter=',')
    feature_scaling = joblib.load('./ML_Data/scaling_variables.pkl') 

    #X=[int(TFT), int(Age), int(Experience), 75.5, 283.6, 2.3,-0.16]
    X=[int(TFT), int(Age), int(Experience), 71.8, 275.8, 0.94,-1.86]

    X=feature_scaling.transform(X)
    poly = PolynomialFeatures(2)
    X=poly.fit_transform(X)
    X=np.append(X,Gender)
    X=np.asarray(X,dtype=float)

    y_predict=[]
    for i in range(coeff.shape[0]):
        y_predict.append(math.exp(coeff[i,0]+np.sum(np.multiply(X,coeff[i,1:]))))

    
    denominator=sum(y_predict)
    y_predict[:] = [int(TFT)*(x/denominator) for x in y_predict]

    print(y_predict)

    myorder=[0,1,2,3,8,4,5,6,7,9] # Reorder list to suit the spilit order
    y_predict=[y_predict[i] for i in myorder]
    
    y_pace=np.divide(y_predict,np.asarray([5, 5, 5, 5, 1.08241, 3.91759, 5, 5, 5, 2.195]))
    y_predict=np.cumsum(y_predict)

    #turn them into formatted strings
    #y_pace = ['{0:.2f}'.format(v) for v in y_pace]
    #y_predict = ['{0:.1f}'.format(v) for v in y_predict]
    

    
    
    
    #y_predict = [10,30,50,70,90,110,130,150,170,190]
    #y_pace = [v/5 for v in y_predict]
    return (y_pace,y_predict)

def generate_personal_txt_file(y_pace, y_predict):

    
    y_predict_str=[time.strftime('%H:%M:%S',
                                 time.gmtime(float(i)*60)) for i in y_predict]
    proc_seqf = tempfile.TemporaryFile(suffix='.personal.txt')


    proc_seqf.write("2016\tF10\tYou, .\t30\tF\tBomet\t\tUSA")
    proc_seqf.write("\n")
    proc_seqf.write("5k\t10k\t15k\t20k\tHalf\t25k\t30k\t35k\t40k")
    proc_seqf.write("\n")
    proc_seqf.write("%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s" %
                    (y_predict_str[0],y_predict_str[1],y_predict_str[2],
                     y_predict_str[3],y_predict_str[4],y_predict_str[5],
                     y_predict_str[6],y_predict_str[7],y_predict_str[8]))
    proc_seqf.write("\n")
    proc_seqf.write("Finish: Pace\tProj. Time\tOffl. Time\tOverall\tGender\tDivision")
    proc_seqf.write("\n")
    proc_seqf.write("0:00:00\t0:00:00\t%s\t-\t-" % (y_predict_str[9]))
    proc_seqf.flush()
    proc_seqf.seek(0)
    
    return proc_seqf



@app.route('/')
def home():
    return render_template('home.html'
                              , mytable=None
                              , TFT=''
                              , Age=''
                              , Experience=''
                              , Gender='')
@app.route('/', methods=['POST'])
def home_posted():
    TFT0=request.form['Target Finish Time']
    Age=request.form['Age']
    Experience=request.form['Experience']
    Gender=request.form['Gender']
    
    TFTHH,_,TFTMM = TFT0.partition(':')
    TFTHH = int(TFTHH)
    TFTMM = int(TFTMM)
    
    TFT = TFTHH*60 + TFTMM
    

    y_pace, y_predict = generate_series(TFT, Age, Experience, Gender)
    
    y_pace = ['{0:.2f}'.format(v) for v in y_pace]
    y_predict = ['{0:.1f}'.format(v) for v in y_predict]

    marathon_data_url = '/marathon-data.json?Target+Finish+Time=%s&Age=%s&Experience=%s&Gender=%s'
    
    marathon_data_url = marathon_data_url % (TFT0, Age, Experience, Gender)
    
    
    
    return render_template('home.html',
    
                                mytable={
                                  "ProjTime": y_predict
                                , "ProjPace": y_pace
                                , "marathon_data_url": marathon_data_url}
                              , TFT=TFT0
                              , Age=Age
                              , Experience=Experience
                              , Gender=Gender
                                )
@app.route('/bar-plot.png',methods=['GET', 'POST'])
def bar_plot_chart():
    TFT0=request.values.get('Target Finish Time')
    Age=request.values.get('Age')
    Experience=request.values.get('Experience')
    Gender=request.values.get('Gender')


    TFTHH,_,TFTMM = TFT0.partition(':')
    TFTHH = int(TFTHH)
    TFTMM = int(TFTMM)
    
    TFT = TFTHH*60 + TFTMM
    
    y_pace, y_predict = generate_series(TFT, Age, Experience, Gender)


    Pace=np.asarray(y_pace)
    #Pace=np.asarray([4.93,4.38,4.41,4.46,5.08,4.46,4.55,4.85,5.06,3.94])

    xaxis=np.asarray(['0-5k','5-10k','10-15k','15-20k','20k-Half','Half-25k','25-30k','30-35k','35-40k','40k-Finish'])

    assert len(Pace) == len(xaxis)


    sns.set_style("white")
    bar_plot = sns.barplot(x=xaxis,y=Pace,
                            color="dodgerblue")
    bar_plot.set(xlabel='Split', ylabel='Pace (min/km)')
    plt.xticks(rotation=90)
    plt.ylim(round((min(Pace)-0.25/2)*4)/4,round((max(Pace)+0.25/2)*4)/4)


    for p,PaceValue in zip(bar_plot.patches, Pace):
        height = p.get_height()
        #bar_plot.text(p.get_x(), height+0.02, '%1.2f'%(Pace[count]),fontweight="bold")
        bar_plot.text(p.get_x(), height+0.02, '%1.2f'%(PaceValue))
        
    bar_plot.set(axis_bgcolor='whitesmoke')
    bar_plot.set_title('YOUR RECOMMENDED SPLIT PACE (min/km)',fontweight="bold") 

    imgdata = StringIO()
    plt.savefig(imgdata, format='png', bbox_inches="tight", dpi=150)
    imgdata.seek(0)  # rewind the data

    
    return Response(imgdata.buf,  mimetype='image/png')
    return Response(imgdata.buf,  mimetype='image/svg+xml')
    



@app.route('/marathon-data.json', methods=['GET', 'POST'])
def marathon_data():

    TFT0=request.values.get('Target Finish Time')
    Age=request.values.get('Age')
    Experience=request.values.get('Experience')
    Gender=request.values.get('Gender')

    TFTHH,_,TFTMM = TFT0.partition(':')
    TFTHH = int(TFTHH)
    TFTMM = int(TFTMM)
    
    TFT = TFTHH*60 + TFTMM
    
    y_pace, y_predict = generate_series(TFT, Age, Experience, Gender)
    
    
    with open('./Elite_runners.txt') as elite_runners_txt:
        with generate_personal_txt_file(y_pace, y_predict) as personal_txt:
            
            rows = list(parser.read(elite_runners_txt))
            rows += list(parser.read(personal_txt))
            data = parser.parse(rows)
            placed_data, ranks = parser.place_at_splits(data)
            impute_placed_data = parser.impute(placed_data, ranks)
            
            
            marathon_data = json.dumps(impute_placed_data, indent=4)
            
            return Response(marathon_data,  mimetype='text/json')
    

@app.route('/about')
def about():
    return render_template('about.html')



if __name__ == '__main__':



    argparser = argparse.ArgumentParser(description='NYC Marathon Server.')
    argparser.add_argument('port', type=int,
                       help='port to run the server on')


    args = argparser.parse_args()
    
    

    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter("%(levelname)s - %(message)s")
    ch.setFormatter(formatter)
    
    
    fh = logging.FileHandler('app.log')
    fh.setLevel(logging.INFO)


    app.logger.addHandler(ch)
    app.logger.addHandler(fh)

    app.run(host='0.0.0.0',port=args.port)













