import os, sys
sys.path.insert(0, '.')
os.environ['SCRAPE_TARGET'] = 'domestic'
import updater
updater.main()
