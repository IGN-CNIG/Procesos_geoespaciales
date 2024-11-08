from src.modules.inspire import AtomService

def main() -> None:
        
    # 1. Read features from the service service
    # CATASTRO
    # 1. Servicio completo
    #atom = AtomService(source='https://www.catastro.minhap.es/INSPIRE/CadastralParcels/ES.SDGC.CP.atom.xml', name='Catastro')
    # 2. Provincia
    atom = AtomService(source='https://www.catastro.minhap.es/INSPIRE/CadastralParcels/02/ES.SDGC.CP.atom_02.xml', name='Catastro')
    # Solamente ciertos municipios, sabiendo el nombre del fichero
    features = atom.get_feature(typeNames='CadastralParcel', FILES='A.ES.SDGC.CP.02001.zip,A.ES.SDGC.CP.02002.zip')
    
    for index, feature in enumerate(features):
        # Here we do something with the features as they get yielded from the ATOM service.
        pass


if __name__ == '__main__':
    main()