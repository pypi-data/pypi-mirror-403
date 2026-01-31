import os, logging, uuid, shutil

Base = 'C:/VKHCG'
sCompanies = ['01-Vermeulen','02-Krennwallner','03-Hillman','04-Clark']
sLayers = ['01-Retrieve','02-Assess','03-Process','04-Transform','05-Organise','06-Report']
sLevels = ['debug','info','warning','error']

for sCompany in sCompanies:
    for sLayer in sLayers:
        # Setup logging directory
        sFileDir = os.path.join(Base, sCompany, sLayer, 'Logging')
        if os.path.exists(sFileDir):
            shutil.rmtree(sFileDir)
        os.makedirs(sFileDir)

        # Unique log file
        sLogFile = os.path.join(sFileDir, f'Logging_{uuid.uuid4()}.log')
        print('Set up:', sLogFile)

        # Configure logging
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
            datefmt='%m-%d %H:%M',
            filename=sLogFile,
            filemode='w'
        )

        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        console.setFormatter(logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s'))
        logging.getLogger('').addHandler(console)

        # Log messages
        logging.info('Practical Data Science is fun!')
        log_methods = {'debug': logging.debug, 'info': logging.info, 
                       'warning': logging.warning, 'error': logging.error}

        for sLevel in sLevels:
            logger_name = f'Application-{sCompany}-{sLayer}-{sLevel}'
            logger = logging.getLogger(logger_name)
            log_methods[sLevel](f'Practical Data Science logged a {sLevel} message.')
