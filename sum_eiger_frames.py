#!/usr/bin/env python2.7
from logbook import Logger, StreamHandler, set_datetime_format
from sys import path, stdout
import numpy as np
import pickle, json, yaml, os.path
import multiprocessing as mp
import redis

StreamHandler(stdout).push_application()
logger = Logger(__name__)
set_datetime_format("local")

try:
  with open('config.yaml', 'r') as stream:
    config = yaml.load(stream)
except yaml.YAMLError as e:
  logger.critical(e)
  exit()
except IOError as e:
  logger.critical(e)
  exit()

redis = redis.StrictRedis(config['sys_settings']['redis_ip'])

path.append(config['sys_settings']['albula_path'])
import dectris.albula
series = dectris.albula.DImageSeries()

def sanity_check():
  assert config['in']['start'] >= 0
#  assert config['in']['start'] <= config['in']['end']
  assert config['filter']['low'] <= config['filter']['high']
  assert os.path.isfile(config['in']['master'])
  assert config['sys_settings']['threads'] > 0


def read():
  logger.info('Reading in master file')
  master = config['in']['master']
  series.open(master)


def run():
  nproc = config['sys_settings']['threads']
  logger.info('Running on %i threads' % (nproc))
  pool = mp.Pool(processes=nproc)

  if config['in']['start'] == 0: first = series.first()
  else: first = config['in']['start']

  if config['in']['end'] == 0: last = series.last()
  elif config['in']['end'] > series.last(): last = series.last()
  else: last = config['in']['end']

  logger.info('Processing frames %i to %i' % (first,last))
  results = pool.map(summer,range(first,last+1))
  return results


def summer(n):
  img = series[n]
  data  = img.data()
  data = np.ma.masked_less(data,config['filter']['low'])
  data = np.ma.masked_greater(data,config['filter']['high'])
  if n % 100 == 0: logger.info('...another 100 frames.')
  return data.sum()


def output(sums):
  if config['out']['redis']:
    expire = config['out']['expire'] * 24 * 60 * 60
    key = config['out']['prefix']+':'+config['in']['master']
    redis.set(key,pickle.dumps(sums))
    redis.expire(key,expire)
    logger.info('Output written to rediskey %s' % key)

  if config['out']['file']:
    fname = config['in']['master'].split('/')[-1]
    path = config['out']['path']
    concat = path+fname+'.pickle'
    with open(concat,'wb') as handle:
      pickle.dump(sums,handle)
    logger.info('Output written to file %s' % concat)

  else:
    logger.warning('No output format specified.')
    logger.warning('Dropping into interactive session.')
    from code import interact
    interact(local=locals())


if __name__ == '__main__':
  sanity_check()
  read()
  sums = run()
  output(sums)

