import os, sys
sys.path.insert(0, '.')
os.environ['SCRAPE_TARGET'] = 'portfolios'
import updater
updater.main()
