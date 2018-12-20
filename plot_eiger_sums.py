#!/usr/bin/env python3.6

from logbook import Logger, StreamHandler, set_datetime_format
from sys import path, stdout, exit
from scipy import signal
import yaml, pickle
import pandas as pd


class Plotter:
  def __init__(self):
    StreamHandler(stdout).push_application()
    self.logger = Logger(self.__class__.__name__)
    set_datetime_format("local")

    try:
        with open('config.yaml', 'r') as stream:
          self.config = yaml.load(stream)
    except yaml.YAMLError as e:
        logger.critical(e)
        exit()
    except IOError as e:
        logger.critical(e)
        exit()

  def plotYN(self):
    if self.config['out']['plot'] == False:
      self.logger.info('Output not analysed and plotted.')
      exit()

  def read_data(self):
    if self.config['out']['redis']:
      self.fr_redis()
    elif self.config['out']['file']:
      self.fr_file()
    else:
      self.logger.warning('Reading data from neither redis nor file. Aborting')
      exit()

  def fr_redis(self):
    self.logger.info('Reading data from redis key.')
    import redis
    redis = redis.StrictRedis(self.config['sys_settings']['redis_ip'])
    key = self.config['out']['prefix']+':'+self.config['in']['master']
    if redis.exists(key):
      self.data = pickle.loads(redis.get(key), encoding='bytes')
    else:
      self.logger.warning(f'Redis key {key} does not exist; might have expired.')
      self.fr_file()

  def fr_file(self):
    self.logger.info('Reading data from file.')
    fname = self.concat()
    with open(fname+'.pickle','rb') as handle:
      self.data = pickle.load(handle, encoding='bytes')

  def concat(self):
    fname = self.config['in']['master'].split('/')[-1]
    path = self.config['out']['path']
    return path+fname

  def detrend(self):
    self.logger.info('Detrending data')
    df = pd.DataFrame(self.data,columns=['raw'])
    df['detrended'] = signal.detrend(df['raw']) + df['raw'].mean()
    self.df = df

  def normalise(self):
    self.norm = self.df / self.df.mean()

  def make_fig(self):
    import cufflinks as cf #To be removed later; use plotly directly
    title = self.concat()
    self.fig = self.norm.iplot(asFigure=True,title=title,colorscale='polar',
                               xTitle='frame',yTitle='Normalised intensity')

  def plot(self):
    import plotly
    fname = self.concat()+'.html'
    self.logger.info(f'Plot saved as {fname}')
    plotly.offline.plot(self.fig, filename=fname)

  def describe_data(self):
    out = pd.DataFrame()
    for key in self.df.columns:
      tmp = self.df[key].describe()
      tmp['CV%'] = self.df[key].std() / self.df[key].mean() *100
      out = out.append(tmp)

    order =  ['count','mean','std','CV%','min','25%','50%','75%','max']
    out = out[order].T
    fname = self.concat()+'.csv'
    out.to_csv(fname)
    self.logger.info(f'Descriptive stats: \n {out}')
    self.logger.info(f'Data description saved as {fname}')

  def run(self):
    self.plotYN()
    self.read_data()
    self.detrend()
    self.normalise()
    self.describe_data()
    self.make_fig()
    self.plot()

if __name__ == '__main__':
  p = Plotter()
  p.run()


